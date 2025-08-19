
"use client";
import { useState } from "react";
const API = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8001";
export default function AdminPage() {
  const [src, setSrc] = useState("us-senate");
  const [out, setOut] = useState<any>(null);
  const [token, setToken] = useState("");
  const [persist, setPersist] = useState(true);
  const [limit, setLimit] = useState<number>(50);
  async function runIngest() {
    const r = await fetch(`${API}/api/admin/ingest/run?source=${src}&persist=${persist?1:0}`);
    setOut(await r.json());
  }
  async function runAll() {
    const r = await fetch(`${API}/api/admin/ingest/run_all?persist=${persist?1:0}&limit=${limit}`);
    setOut(await r.json());
  }
  async function requeueFailed() {
    await fetch(`${API}/api/admin/jobs/requeue_failed`, { method: "POST", headers: token ? { Authorization: `Bearer ${token}` } : {} });
    alert("Requeued failed jobs");
  }
  return (
    <main>
      <h2>Admin</h2>
      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:16 }}>
        <div style={{ background:"#0f1620", border:"1px solid #152131", borderRadius:16, padding:14 }}>
          <h3>Connectors</h3>
          <div style={{ display:"flex", gap:8, alignItems:"center" }}>
            <select value={src} onChange={e=>setSrc(e.target.value)}>
              <option value="us-senate">US Senate</option>
              <option value="us-house">US House</option>
              <option value="uk">UK Register</option>
            </select>
            <label><input type="checkbox" checked={persist} onChange={e=>setPersist(e.target.checked)} /> persist</label>
            <input type="number" value={limit} onChange={e=>setLimit(parseInt(e.target.value||"0"))} style={{ width:100 }} />
          </div>
          <div style={{ marginTop:8, display:"flex", gap:8 }}>
            <button onClick={runIngest} style={{ padding:"8px 12px", borderRadius:12, background:"#60a5fa", color:"#0b0f14", border:"none" }}>Run Source</button>
            <button onClick={runAll} style={{ padding:"8px 12px", borderRadius:12, background:"#34d399", color:"#0b0f14", border:"none" }}>Run All</button>
          </div>
          <pre style={{ whiteSpace:"pre-wrap", marginTop:12 }}>{out ? JSON.stringify(out,null,2) : "No run yet."}</pre>
        </div>
        <div style={{ background:"#0f1620", border:"1px solid #152131", borderRadius:16, padding:14 }}>
          <h3>Jobs</h3>
          <input placeholder="API token" value={token} onChange={e=>setToken(e.target.value)} style={{ padding:8, borderRadius:8, border:"1px solid #152131", background:"#0d141c", color:"#e6eef7", width:"100%" }}/>
          <button onClick={requeueFailed} style={{ marginTop:8, padding:"8px 12px", borderRadius:12, background:"#34d399", color:"#0b0f14", border:"none" }}>Requeue Failed</button>
        </div>
      </div>
    </main>
  );
}
