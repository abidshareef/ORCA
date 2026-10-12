import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { CircleMarker, MapContainer, Popup, TileLayer, useMap } from "react-leaflet";

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");
const FALLBACK_SCENARIOS = [
  { id: "normal_ocean", name: "Normal Ocean State", description: "Illustrative baseline conditions." },
  { id: "marine_heatwave", name: "Marine Heatwave", description: "Illustrative warming stress." },
  { id: "pollution_event", name: "Pollution Event", description: "Illustrative pollution indicators." },
  { id: "combined_crisis", name: "Combined Ecosystem Crisis", description: "Illustrative combined stressors." },
];

function FitScenario({ position }) {
  const map = useMap();
  useEffect(() => {
    map.setView(position, 5, { animate: false });
  }, [map, position]);
  return null;
}

function formatPercent(value) {
  if (value == null || !Number.isFinite(Number(value))) return "—";
  return `${Math.round(Number(value) * 100)}%`;
}

function RiskBadge({ level }) {
  return <span className={`risk-badge risk-${String(level || "unknown").toLowerCase()}`}>{level || "UNKNOWN"}</span>;
}

export default function App() {
  const [scenarios, setScenarios] = useState(FALLBACK_SCENARIOS);
  const [scenarioId, setScenarioId] = useState("normal_ocean");
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [apiStatus, setApiStatus] = useState("checking");
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState("");
  const [queryText, setQueryText] = useState("");
  const [queryLatitude, setQueryLatitude] = useState("");
  const [queryLongitude, setQueryLongitude] = useState("");
  const [queryResult, setQueryResult] = useState(null);
  const [queryLoading, setQueryLoading] = useState(false);
  const [queryError, setQueryError] = useState("");

  const selectedScenario = useMemo(
    () => scenarios.find((item) => item.id === scenarioId) || FALLBACK_SCENARIOS[0],
    [scenarios, scenarioId],
  );

  const checkApi = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/ready`);
      if (!response.ok) throw new Error("API readiness check failed");
      setApiStatus("online");
    } catch {
      setApiStatus("offline");
    }
  }, []);

  useEffect(() => {
    let active = true;
    async function loadScenarios() {
      try {
        const response = await fetch(`${API_BASE}/api/scenarios`);
        if (!response.ok) throw new Error("Scenario endpoint unavailable");
        const payload = await response.json();
        const list = Array.isArray(payload) ? payload : payload.scenarios;
        if (active && Array.isArray(list) && list.length) setScenarios(list);
      } catch {
        // Keep local scenario labels visible while showing API state separately.
      }
    }
    loadScenarios();
    checkApi();
    return () => { active = false; };
  }, [checkApi]);

  const runAnalysis = async (id = scenarioId) => {
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${API_BASE}/api/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scenario_id: id }),
      });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail || "Analysis request failed");
      setAnalysis(payload);
      setLastUpdated(new Date().toLocaleTimeString());
      setApiStatus("online");
    } catch (err) {
      setError(`${err.message}. Confirm the API is deployed and VITE_API_BASE_URL is set correctly.`);
      setApiStatus("offline");
    } finally {
      setLoading(false);
    }
  };

  const runQuery = async (event) => {
    event.preventDefault();
    setQueryLoading(true);
    setQueryError("");
    setQueryResult(null);
    try {
      const payload = {
        query: queryText,
        scenario_id: scenarioId,
      };
      if (queryLatitude.trim() !== "" && queryLongitude.trim() !== "") {
        payload.latitude = Number(queryLatitude);
        payload.longitude = Number(queryLongitude);
      }
      const response = await fetch(`${API_BASE}/api/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "Query failed");
      setQueryResult(result);
      if (result.analysis) {
        setAnalysis(result.analysis);
        setLastUpdated(new Date().toLocaleTimeString());
      } else if (result.plan?.intent === "marine_conditions") {
        // Do not leave an unrelated ecosystem scenario visible under a wave forecast.
        setAnalysis(null);
        setLastUpdated("");
      }
      setApiStatus("online");
    } catch (err) {
      setQueryError(`${err.message}. Check the API URL and backend status.`);
      setApiStatus("offline");
    } finally {
      setQueryLoading(false);
    }
  };

  const mapPosition = useMemo(
    () => [
      Number(analysis?.location?.latitude ?? 15.5),
      Number(analysis?.location?.longitude ?? 70.5),
    ],
    [analysis?.location?.latitude, analysis?.location?.longitude],
  );
  const chartData = (analysis?.agents || []).map((agent) => ({
    agent: agent.agent.replace(" Agent", "").replace(" & Oceanographic", ""),
    risk: Math.round((Number(agent.prediction) || 0) * 100),
    confidence: Math.round((Number(agent.confidence) || 0) * 100),
  }));
  const anomalyCount = (analysis?.anomalies || []).filter((item) => item.severity === "ANOMALY").length;

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="ORCA home">
          <span className="brand-mark">O</span>
          <span><strong>ORCA</strong><small>MARINE INTELLIGENCE</small></span>
        </a>
        <div className="topbar-right">
          <span className={`status-dot status-${apiStatus}`} />
          <span className="status-text">API {apiStatus === "checking" ? "CHECKING" : apiStatus.toUpperCase()}</span>
          <a className="docs-link" href={`${API_BASE}/docs`} target="_blank" rel="noreferrer">API docs ↗</a>
        </div>
      </header>

      <section className="hero">
        <div>
          <p className="eyebrow">OBSERVE · REASON · COORDINATE · ADVISE</p>
          <h1>Understand the ocean<br /><span>as a connected system.</span></h1>
          <p className="hero-copy">ORCA coordinates specialized agents to turn environmental indicators into explainable ecosystem-risk assessments.</p>
        </div>
        <div className="hero-side">
          <span className="hero-orbit orbit-one" /><span className="hero-orbit orbit-two" />
          <span className="hero-core">ORCA</span>
          <span className="hero-coordinate">ARABIAN SEA · DEMO REGION</span>
        </div>
      </section>

      <section className="control-panel panel">
        <div className="control-copy">
          <span className="eyebrow">ANALYSIS WORKSPACE</span>
          <h2>Run an ecosystem scenario</h2>
          <p>Select a controlled scenario and execute the multi-agent analysis pipeline.</p>
        </div>
        <div className="controls">
          <label htmlFor="scenario-select">Scenario</label>
          <select id="scenario-select" value={scenarioId} onChange={(event) => setScenarioId(event.target.value)}>
            {scenarios.map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}
          </select>
          <button className="primary-button" onClick={() => runAnalysis(scenarioId)} disabled={loading}>
            {loading ? <><span className="spinner" /> Analyzing</> : "Run analysis"}
          </button>
        </div>
      </section>

      {error && <div className="error-banner" role="alert"><strong>Analysis unavailable</strong><span>{error}</span><button onClick={() => { checkApi(); runAnalysis(scenarioId); }}>Retry</button></div>}

      <section className="query-panel panel">
        <div className="control-copy">
          <span className="eyebrow">QUERY ROUTER · PROTOTYPE</span>
          <h2>Ask ORCA a marine question</h2>
          <p>Routes your question to relevant capabilities. Live wave forecasts require coordinates; ecosystem answers still use scenario data.</p>
        </div>
        <form className="query-form" onSubmit={runQuery}>
          <label htmlFor="orca-query">Question</label>
          <input id="orca-query" value={queryText} onChange={(event) => setQueryText(event.target.value)} minLength={3} maxLength={1000} placeholder="e.g. Check pollution levels, or what are the waves like?" required />
          <div className="query-coordinate-fields">
            <label>Latitude<input inputMode="decimal" value={queryLatitude} onChange={(event) => setQueryLatitude(event.target.value)} placeholder="e.g. 15.5" /></label>
            <label>Longitude<input inputMode="decimal" value={queryLongitude} onChange={(event) => setQueryLongitude(event.target.value)} placeholder="e.g. 70.5" /></label>
            <button className="primary-button" type="submit" disabled={queryLoading}>{queryLoading ? <><span className="spinner" /> Routing</> : "Ask ORCA"}</button>
          </div>
        </form>
      </section>

      {queryError && <div className="error-banner" role="alert"><strong>Query unavailable</strong><span>{queryError}</span></div>}
      {queryResult && (
        <section className="query-result panel" aria-live="polite">
          <div className="panel-heading"><div><span className="eyebrow">QUERY PLAN</span><h3>{queryResult.plan.intent.replaceAll("_", " ")}</h3></div><span className="map-tag">{queryResult.plan.selected_agents.length ? `${queryResult.plan.selected_agents.length} agents selected` : queryResult.plan.intent === "marine_conditions" ? "Live provider route" : "No matching capability"}</span></div>
          <p className="query-question">“{queryResult.query}”</p>
          <div className="query-chip-row">{queryResult.plan.selected_agents.map((agent) => <span className="query-chip" key={agent}>{agent}</span>)}</div>
          {queryResult.marine_conditions && (
            <>
              <div className="marine-condition-grid">
                <div><span>WAVE HEIGHT</span><strong>{queryResult.marine_conditions.wave_height_m.toFixed(1)} m</strong></div>
                <div><span>WAVE PERIOD</span><strong>{queryResult.marine_conditions.wave_period_s == null ? "—" : `${queryResult.marine_conditions.wave_period_s.toFixed(1)} s`}</strong></div>
                <div><span>DISPLAY BAND</span><strong>{queryResult.marine_conditions.display_band.replaceAll("_", " ")}</strong></div>
                <div><span>FORECAST TIME (UTC)</span><strong>{new Date(queryResult.marine_conditions.forecast_time_utc).toLocaleString()}</strong></div>
              </div>
              <p className="query-notice">Source: <a href={queryResult.marine_conditions.source_url} target="_blank" rel="noreferrer">{queryResult.marine_conditions.source}</a> · Forecast, not a direct observation.</p>
              {(queryResult.marine_conditions.limitations || []).map((limitation) => <p className="query-limitation" key={limitation}>{limitation}</p>)}
            </>
          )}
          {queryResult.notice && <p className="query-notice">{queryResult.notice}</p>}
          {!queryResult.marine_conditions && queryResult.plan.limitations.map((limitation) => <p className="query-limitation" key={limitation}>{limitation}</p>)}
        </section>
      )}

      <section className="section-heading">
        <div><span className="eyebrow">SYSTEM OUTPUT</span><h2>Risk overview</h2></div>
        <span className="timestamp">{lastUpdated ? `Last run · ${lastUpdated}` : "Awaiting first analysis"}</span>
      </section>

      <section className="metrics-grid">
        <article className="metric-card">
          <span className="metric-label">Aggregate risk</span>
          <div className="metric-value">{analysis ? formatPercent(analysis.risk_score) : "—"}</div>
          <div className="metric-foot">Confidence-weighted agent synthesis</div>
          <div className="meter"><span style={{ width: analysis?.risk_score != null ? formatPercent(analysis.risk_score) : "0%" }} /></div>
        </article>
        <article className="metric-card">
          <span className="metric-label">Risk classification</span>
          <div className="metric-risk">{analysis ? <RiskBadge level={analysis.risk_level} /> : <span className="muted">Awaiting result</span>}</div>
          <div className="metric-foot">Based on current prototype thresholds</div>
        </article>
        <article className="metric-card">
          <span className="metric-label">Ecosystem health index</span>
          <div className="metric-value">{analysis ? formatPercent(analysis.ecosystem_health) : "—"}</div>
          <div className="metric-foot">Inverse of aggregated risk score</div>
        </article>
        <article className="metric-card">
          <span className="metric-label">Detected anomalies</span>
          <div className="metric-value">{analysis ? anomalyCount : "—"}</div>
          <div className="metric-foot">Indicators beyond configured z-score thresholds</div>
        </article>
      </section>

      <section className="content-grid">
        <article className="panel map-panel">
          <div className="panel-heading"><div><span className="eyebrow">SPATIAL CONTEXT</span><h3>Analysis location</h3></div><span className="map-tag">DEMO REGION</span></div>
          <div className="map-frame">
            <MapContainer center={mapPosition} zoom={5} scrollWheelZoom={false} className="orca-map">
              <FitScenario position={mapPosition} />
              <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
              <CircleMarker center={mapPosition} radius={10} pathOptions={{ color: "#75e0c1", fillColor: "#75e0c1", fillOpacity: 0.8 }}>
                <Popup>ORCA scenario location<br />{mapPosition[0].toFixed(3)}, {mapPosition[1].toFixed(3)}</Popup>
              </CircleMarker>
            </MapContainer>
          </div>
          <div className="coordinate-row"><span>LATITUDE <strong>{mapPosition[0].toFixed(3)}°</strong></span><span>LONGITUDE <strong>{mapPosition[1].toFixed(3)}°</strong></span><span>DEPTH <strong>{Number(analysis?.location?.depth ?? 10)} m</strong></span></div>
          <p className="disclaimer">Scenario coordinates and measurements are illustrative demo data, not live marine observations.</p>
        </article>

        <article className="panel chart-panel">
          <div className="panel-heading"><div><span className="eyebrow">COLLABORATIVE AGENTS</span><h3>Agent risk contributions</h3></div></div>
          {chartData.length ? (
            <div className="chart-wrap">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} layout="vertical" margin={{ top: 8, right: 22, left: 12, bottom: 4 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#203a46" horizontal={false} />
                  <XAxis type="number" domain={[0, 100]} tick={{ fill: "#8ea5af", fontSize: 11 }} tickFormatter={(value) => `${value}%`} />
                  <YAxis type="category" dataKey="agent" width={108} tick={{ fill: "#c8d7dc", fontSize: 11 }} />
                  <Tooltip contentStyle={{ background: "#102a36", border: "1px solid #2b4a57", borderRadius: 10 }} formatter={(value) => [`${value}%`, "Risk contribution"]} />
                  <Bar dataKey="risk" fill="#75e0c1" radius={[0, 5, 5, 0]} barSize={18} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : <div className="empty-chart"><span className="empty-icon">↗</span><strong>{analysis ? "Insufficient ecological data" : "No analysis yet"}</strong><p>{analysis ? "ORCA cannot calculate agent risk until valid ecosystem measurements are available." : "Run a scenario to view agent outputs."}</p></div>}
          <div className="agent-legend"><span><i className="legend-dot" /> 5 specialized agents</span><span>Confidence-weighted synthesis</span></div>
        </article>
      </section>

      <section className="section-heading findings-heading">
        <div><span className="eyebrow">EVIDENCE & EXPLANATION</span><h2>What the agents found</h2></div>
        {analysis && <RiskBadge level={analysis.risk_level} />}
      </section>

      <section className="findings-grid">
        {(analysis?.agents || []).map((agent) => (
          <article className="finding-card" key={agent.agent}>
            <div className="finding-top"><span className="agent-index">{String((analysis.agents.indexOf(agent) + 1)).padStart(2, "0")}</span><span className="confidence-label">{formatPercent(agent.confidence)} confidence</span></div>
            <h3>{agent.agent}</h3>
            <strong className="finding-title">{agent.finding}</strong>
            <p>{agent.reasoning}</p>
            <div className="finding-meter"><span style={{ width: formatPercent(agent.prediction) }} /></div>
            <div className="finding-foot"><span>Risk signal</span><strong>{formatPercent(agent.prediction)}</strong></div>
            {agent.evidence?.length > 0 && <ul className="evidence-list">{agent.evidence.slice(0, 3).map((item, index) => <li key={index}>{item}</li>)}</ul>}
          </article>
        ))}
        {analysis && !analysis.agents?.length && <div className="empty-state panel"><span className="empty-icon">◎</span><h3>Insufficient ecological data</h3><p>No domain-agent findings were produced because the required ecological measurements are missing. Load valid observations and run the analysis again.</p></div>}
        {!analysis && <div className="empty-state panel"><span className="empty-icon">◎</span><h3>Waiting for a scenario</h3><p>Run an analysis to populate the agent evidence, anomaly signals and recommendations.</p></div>}
      </section>

      {analysis && (
        <section className="content-grid lower-grid">
          <article className="panel">
            <div className="panel-heading"><div><span className="eyebrow">SYSTEM SYNTHESIS</span><h3>Explanation</h3></div></div>
            <p className="result-copy">{analysis.explanation}</p>
            <div className="recommendation"><span className="recommendation-mark">→</span><div><span className="eyebrow">PROTOTYPE RECOMMENDATION</span><p>{analysis.recommendation}</p></div></div>
          </article>
          <article className="panel">
            <div className="panel-heading"><div><span className="eyebrow">TRACEABILITY</span><h3>Analysis metadata</h3></div></div>
            <dl className="metadata-list">
              <div><dt>Data source</dt><dd>{analysis.data_source}</dd></div>
              <div><dt>Scenario</dt><dd>{selectedScenario?.name || scenarioId}</dd></div>
              <div><dt>Analysis timestamp</dt><dd>{analysis.timestamp ? new Date(analysis.timestamp).toLocaleString() : "—"}</dd></div>
              <div><dt>Agent outputs</dt><dd>{analysis.agents?.length || 0} / 5</dd></div>
              <div><dt>Confidence</dt><dd>{formatPercent(analysis.confidence)}</dd></div>
            </dl>
          </article>
        </section>
      )}

      <footer className="footer">
        <div className="brand footer-brand"><span className="brand-mark">O</span><span><strong>ORCA</strong><small>MARINE INTELLIGENCE</small></span></div>
        <p>Research prototype · Decision support only · Verify operational decisions against authoritative sources.</p>
        <span className="footer-version">BUILD 1.0</span>
      </footer>
    </main>
  );
}