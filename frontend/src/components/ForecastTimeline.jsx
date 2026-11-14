import { useEffect, useState } from "react";
import { Play, Pause, ChevronLeft, ChevronRight } from "lucide-react";
import { stamp } from "../utils/geo";
export default function ForecastTimeline({ times, hour, setHour }) {
  const [playing, setPlaying] = useState(false);
  useEffect(() => {
    if (!playing) return;
    const id = setInterval(() => setHour((h) => (h + 1) % 49), 1000);
    return () => clearInterval(id);
  }, [playing, setHour]);
  return (
    <section className="timeline">
      <div className="timeline-top">
        <div>
          <div className="section-label">CORRIDOR FORECAST</div>
          <strong>{stamp(times?.[hour])}</strong>
        </div>
        <span className="badge">+{hour} hours</span>
      </div>
      <div className="timeline-controls">
        <button
          aria-label="Previous hour"
          onClick={() => setHour(Math.max(0, hour - 1))}
          disabled={hour === 0}
        >
          <ChevronLeft size={17} />
        </button>
        <button
          aria-label={playing ? "Pause forecast" : "Play forecast"}
          onClick={() => setPlaying(!playing)}
        >
          {playing ? <Pause size={17} /> : <Play size={17} />}
        </button>
        <input
          aria-label="Forecast hour"
          type="range"
          min="0"
          max="48"
          value={hour}
          onChange={(e) => setHour(+e.target.value)}
        />
        <button
          aria-label="Next hour"
          onClick={() => setHour(Math.min(48, hour + 1))}
          disabled={hour === 48}
        >
          <ChevronRight size={17} />
        </button>
      </div>
      <div className="timeline-ticks">
        <span>Departure hour</span>
        <span>+12h</span>
        <span>+24h</span>
        <span>+36h</span>
        <span>+48h</span>
      </div>
      <p className="hint">
        Hour 0 is departure rounded up to the next UTC hour. Gray means
        unavailable. This view does not change ETA-based rankings.
      </p>
    </section>
  );
}
