import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

type Agent = { id: string; name: string; kind: string; description: string; deterministic: boolean; version: string; capabilities: string[] };
type Run = { id: string; status: string; output?: Record<string, unknown>; errors?: string[] };

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API}${path}`, { headers: { "Content-Type": "application/json", ...(options?.headers || {}) }, ...options });
  if (!response.ok) throw new Error(`${response.status}: ${await response.text()}`);
  return response.json();
}

function App() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selected, setSelected] = useState("fund-reconciliation");
  const [request, setRequest] = useState("Reconcile administrator and fund manager valuations");
  const [run, setRun] = useState<Run | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => { api<Agent[]>("/fund-ops/agents").then(setAgents).catch((e) => setError(e.message)); }, []);

  const active = useMemo(() => agents.find((a) => a.id === selected), [agents, selected]);

  async function execute() {
    setBusy(true); setError(""); setRun(null);
    try {
      const result = await api<Run>(`/fund-ops/agents/${selected}/run`, {
        method: "POST",
        body: JSON.stringify({ records: [], parameters: { question: request } }),
      });
      setRun(result);
    } catch (e) { setError(e instanceof Error ? e.message : String(e)); }
    finally { setBusy(false); }
  }

  return (
    <div className="app">
      <header className="topbar">
        <div><span className="logo">F</span><strong>FundOps Agent Studio</strong></div>
        <span className="pill">CONTROLLED AI · PHASE 9</span>
      </header>

      <main className="workspace">
        <section className="hero">
          <div><p className="eyebrow">PRIVATE MARKETS OPERATIONS</p><h1>Turn fund operations into governed AI workflows.</h1><p className="sub">Upload data, describe the job, execute deterministic controls, and review every material result with evidence.</p></div>
          <div className="hero-stat"><strong>{agents.length || "—"}</strong><span>registered agents</span></div>
        </section>

        <div className="grid">
          <aside className="panel agents">
            <div className="panel-title"><span>Agent library</span><span>{agents.length}</span></div>
            {agents.map((agent) => <button key={agent.id} className={`agent ${selected === agent.id ? "selected" : ""}`} onClick={() => setSelected(agent.id)}><span className="agent-icon">{agent.kind === "reconciliation" ? "↔" : "✦"}</span><span><b>{agent.name}</b><small>{agent.description}</small></span></button>)}
          </aside>

          <section className="panel builder">
            <div className="panel-title"><span>Run agent</span><span className="safe">● Deterministic controls</span></div>
            <label>What do you want the agent to do?</label>
            <textarea value={request} onChange={(e) => setRequest(e.target.value)} rows={4} />
            <div className="selected-agent"><span className="agent-icon">✦</span><div><b>{active?.name || selected}</b><small>{active?.description || "Loading agent capabilities…"}</small></div><span className="version">v{active?.version || "1.0.0"}</span></div>
            <div className="dropzone"><strong>Drop fund files here</strong><span>Excel or JSON · provenance will be captured</span><button type="button">Choose files</button></div>
            <button className="run" onClick={execute} disabled={busy || !selected}>{busy ? "Running workflow…" : "Run agent →"}</button>
            {error && <div className="error">{error}</div>}
          </section>

          <section className="panel result">
            <div className="panel-title"><span>Run result</span>{run && <span className={`status ${run.status}`}>{run.status}</span>}</div>
            {!run && <div className="empty"><div className="empty-icon">⌁</div><b>No run yet</b><span>Execute an agent to see exceptions, evidence and audit information here.</span></div>}
            {run && <div className="run-result"><div className="run-id">RUN <code>{run.id}</code></div><div className="result-card"><b>Execution {run.status}</b><pre>{JSON.stringify(run.output || run.errors || {}, null, 2)}</pre></div><div className="evidence"><b>Evidence & audit</b><span>Open the run to inspect source lineage, execution events and approval decisions.</span></div></div>}
          </section>
        </div>
      </main>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(<React.StrictMode><App /></React.StrictMode>);
