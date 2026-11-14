import { useEffect, useId, useRef, useState } from "react";
import { LoaderCircle } from "lucide-react";
import { checkLocationCoverage, searchLocations } from "../api/routingApi";

export default function LocationInput({
  icon: Icon,
  label,
  value,
  onChange,
  onSelect,
  coverage,
  onCoverageChange,
}) {
  const listId = useId();
  const [suggestions, setSuggestions] = useState([]);
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [failed, setFailed] = useState(false);
  const [active, setActive] = useState(-1);
  const selectedValue = useRef(value);
  const coverageRequest = useRef(null);

  useEffect(() => () => coverageRequest.current?.abort(), []);

  useEffect(() => {
    if (value.trim().length < 2 || value === selectedValue.current) {
      setSuggestions([]);
      setOpen(false);
      return;
    }
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      setLoading(true);
      setFailed(false);
      try {
        const results = await searchLocations(value.trim(), controller.signal);
        setSuggestions(results);
        setOpen(true);
        setActive(-1);
      } catch (error) {
        if (error.name !== "AbortError") {
          setSuggestions([]);
          setFailed(true);
          setOpen(true);
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }, 250);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [value]);

  async function select(location) {
    selectedValue.current = location.label;
    if (onSelect) onSelect(location);
    else onChange(location.label);
    setOpen(false);
    coverageRequest.current?.abort();
    const controller = new AbortController();
    coverageRequest.current = controller;
    onCoverageChange?.(null);
    try {
      const covered = await checkLocationCoverage(
        location.latitude,
        location.longitude,
        controller.signal,
      );
      if (!controller.signal.aborted) onCoverageChange?.(covered);
    } catch (error) {
      if (error.name !== "AbortError") onCoverageChange?.("error");
    }
  }

  function handleKeyDown(event) {
    if (!open || !suggestions.length) return;
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      const direction = event.key === "ArrowDown" ? 1 : -1;
      setActive(
        (current) =>
          (current + direction + suggestions.length) % suggestions.length,
      );
    } else if (event.key === "Enter" && active >= 0) {
      event.preventDefault();
      select(suggestions[active]);
    } else if (event.key === "Escape") {
      setOpen(false);
    }
  }

  function handleBlur() {
    setTimeout(() => {
      setOpen(false);
      if (selectedValue.current) return;
      const exact = suggestions.find(
        (location) =>
          location.label.split(",")[0].localeCompare(value.trim(), undefined, {
            sensitivity: "base",
          }) === 0,
      );
      if (exact) select(exact);
      else onCoverageChange?.("unselected");
    }, 120);
  }

  return (
    <label className="location-field">
      <span>
        <Icon size={15} /> {label}
      </span>
      <div className="location-input">
        <input
          required
          maxLength={200}
          autoComplete="off"
          value={value}
          onChange={(event) => {
            selectedValue.current = "";
            coverageRequest.current?.abort();
            onCoverageChange?.(null);
            onChange(event.target.value);
          }}
          onKeyDown={handleKeyDown}
          onFocus={() => suggestions.length && setOpen(true)}
          onBlur={handleBlur}
          role="combobox"
          aria-autocomplete="list"
          aria-expanded={open}
          aria-controls={listId}
          aria-activedescendant={
            active >= 0 ? `${listId}-${active}` : undefined
          }
        />
        {loading && <LoaderCircle className="location-spinner" size={16} />}
        {open && failed && (
          <div className="location-options location-status" role="status">
            Search unavailable. Try again.
          </div>
        )}
        {open && !failed && suggestions.length > 0 && (
          <div className="location-options" id={listId} role="listbox">
            {suggestions.map((location, index) => (
              <button
                type="button"
                role="option"
                aria-selected={active === index}
                id={`${listId}-${index}`}
                key={`${location.label}-${location.latitude}-${location.longitude}`}
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => select(location)}
              >
                {location.label}
              </button>
            ))}
          </div>
        )}
      </div>
      {coverage === false && (
        <span className="location-error" role="alert">
          This location is not covered by the routing API.
        </span>
      )}
      {coverage === "error" && (
        <span className="location-error" role="alert">
          Routing coverage could not be verified. Try again.
        </span>
      )}
      {coverage === "unselected" && (
        <span className="location-error" role="alert">
          Select a city or country from the suggestions.
        </span>
      )}
    </label>
  );
}
