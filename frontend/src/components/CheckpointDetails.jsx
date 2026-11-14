import { conditionsAt, number, stamp, riskColors } from "../utils/geo";
export default function CheckpointDetails({ checkpoint, mode, hour, onClose }) {
  const current = conditionsAt(checkpoint, mode, hour),
    weather = current?.weather,
    risk = current?.risk;
  return (
    <section className="checkpoint-detail">
      <div className="card-top">
        <h3>Mile {number(checkpoint.mile)}</h3>
        <button onClick={onClose} aria-label="Close checkpoint">
          Close
        </button>
      </div>
      <p className="hint">
        {checkpoint.lat.toFixed(4)}, {checkpoint.lon.toFixed(4)}
      </p>
      <p>Truck ETA: {stamp(checkpoint.eta)}</p>
      <p>Forecast: {stamp(weather?.forecast_time)}</p>
      {!current ? (
        <p role="status">Forecast unavailable for this hour.</p>
      ) : (
        <>
          <strong style={{ color: riskColors[risk?.overall_risk] }}>
            {risk?.overall_risk}
          </strong>
          <dl>
            {[
              ["Wind", "wind_mph", "mph", "wind_risk"],
              ["Rain", "rain_in_per_hr", "in/hr", "rain_risk"],
              ["Snow", "snow_in_per_hr", "in/hr", "snow_risk"],
            ].map(([name, key, unit, r]) => (
              <div key={key}>
                <dt>{name}</dt>
                <dd>
                  {number(weather?.[key])} {unit} / {risk?.[r]}
                </dd>
              </div>
            ))}
          </dl>
        </>
      )}
    </section>
  );
}
