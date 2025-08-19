
"use client";
import { useEffect, useState } from "react";
const API = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8001";

export default function Checklist() {
  const [status, setStatus] = useState<string>("");
  async function initToken() {
    const r = await fetch(`${API}/api/admin/init`, { method: "POST", headers: { "Content-Type":"application/json" }, body: JSON.stringify({}) });
    const d = await r.json();
    setStatus(`API token: ${d.api_token}`);
  }
  async function quickIngest() {
    const r = await fetch(`${API}/api/admin/ingest/run_all?limit=25&persist=1`, { method: "POST" });
    const d = await r.json();
    setStatus(`Ingested: ${d.added} (unique: ${d.unique})`);
  }
  async function runBacktest() {
    const r = await fetch(`${API}/api/backtest`);
    const d = await r.json();
    setStatus(`Backtest alpha: ${((d.summary?.alpha||0)*100).toFixed(1)}%`);
  }
  async function openPush() {
    window.location.href = "/push";
  }
  return (
    <main>
      <h2>First‑run Checklist</h2>
      <ol>
        <li><button onClick={initToken}>Generate API token</button></li>
        <li><button onClick={quickIngest}>Run quick ingest</button></li>
        <li><button onClick={runBacktest}>Run backtest</button></li>
        <li><button onClick={openPush}>Enable push notifications</button></li>
        <li><a href="/provenance">Review provenance</a></li>
        <li><a href="/quality">Check data quality</a></li>
      </ol>
      <p>{status}</p>
    </main>
  );
}
