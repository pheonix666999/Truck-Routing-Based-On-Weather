import { useServerStatus } from "../hooks/useServerStatus";

const labels = {
  checking: "Checking server",
  waking: "Waking server",
  ready: "Ready",
  unavailable: "Unavailable",
};

export default function ServerStatus() {
  const { status, retry } = useServerStatus();
  return (
    <div className={`server-status ${status}`} role="status" aria-live="polite">
      <span className="server-dot" aria-hidden="true" />
      <span>
        <strong>{labels[status]}</strong>
        {status === "waking" && <small>Free server startup can take over a minute.</small>}
        {status === "unavailable" && <small>The server did not respond. Try again.</small>}
      </span>
      {status === "unavailable" && <button type="button" onClick={retry}>Retry</button>}
    </div>
  );
}
