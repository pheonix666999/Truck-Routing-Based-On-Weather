import { useState } from "react";
import { ArrowRight, MapPin, Navigation, Truck } from "lucide-react";
import LocationInput from "./LocationInput";
export default function TripForm({ onSubmit, loading }) {
  const [trip, setTrip] = useState(() => ({
    origin: "Chicago, Illinois, USA",
    origin_lat: 41.8781,
    origin_lon: -87.6298,
    destination: "Detroit, Michigan, USA",
    destination_lat: 42.3314,
    destination_lon: -83.0458,
    departure_time: new Date(Date.now() + 3600000).toISOString().slice(0, 16),
    load_weight: 42000,
    checkpoint_interval: 25,
  }));
  const [coverage, setCoverage] = useState({ origin: true, destination: true });
  const field = (key) => ({
    value: trip[key],
    onChange: (e) => setTrip({ ...trip, [key]: e.target.value }),
  });
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit(trip);
      }}
    >
      <div className="section-label">PLAN YOUR JOURNEY</div>
      <LocationInput
        icon={MapPin}
        label="Origin"
        value={trip.origin}
        onChange={(origin) =>
          setTrip({ ...trip, origin, origin_lat: null, origin_lon: null })
        }
        onSelect={(location) =>
          setTrip({
            ...trip,
            origin: location.label,
            origin_lat: location.latitude,
            origin_lon: location.longitude,
          })
        }
        coverage={coverage.origin}
        onCoverageChange={(origin) =>
          setCoverage((current) => ({ ...current, origin }))
        }
      />
      <LocationInput
        icon={Navigation}
        label="Destination"
        value={trip.destination}
        onChange={(destination) =>
          setTrip({
            ...trip,
            destination,
            destination_lat: null,
            destination_lon: null,
          })
        }
        onSelect={(location) =>
          setTrip({
            ...trip,
            destination: location.label,
            destination_lat: location.latitude,
            destination_lon: location.longitude,
          })
        }
        coverage={coverage.destination}
        onCoverageChange={(destination) =>
          setCoverage((current) => ({ ...current, destination }))
        }
      />
      <label>
        Departure / UTC
        <input type="datetime-local" required {...field("departure_time")} />
      </label>
      <div className="form-row">
        <label>
          <Truck size={15} /> Load (lb)
          <input
            type="number"
            min="0.01"
            max="99999999"
            step="0.01"
            required
            {...field("load_weight")}
          />
        </label>
        <label>
          Checkpoints
          <select {...field("checkpoint_interval")}>
            {[10, 25, 50].map((n) => (
              <option key={n} value={n}>
                Every {n} miles
              </option>
            ))}
          </select>
        </label>
      </div>
      <button
        className="primary"
        disabled={
          loading ||
          coverage.origin !== true ||
          coverage.destination !== true
        }
      >
        {loading ? "Analyzing route & weather..." : "Find safest route"}
        <ArrowRight size={17} />
      </button>
    </form>
  );
}
