import React from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

function App() {
  return (
    <main className="shell">
      <section className="card">
        <p className="eyebrow">FUNDOPS AGENT STUDIO</p>
        <h1>Private-market operations, powered by governed AI agents.</h1>
        <p>
          Describe a fund-operation task, connect the required data, and run an
          evidence-backed workflow.
        </p>
        <div className="status">Phase 0 foundation ready</div>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
