
"use client";
import { useState } from "react";
const API = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8001";
export default function Setup() {
  const [token, setToken] = useState("");
  const [result, setResult] = useState<any>(null);
  async function init() {
    const r = await fetch(`${API}/api/admin/init`, { method: "POST", headers: { "Content-Type":"application/json" }, body: JSON.stringify({ api_token: token || null }) });
    const d = await r.json(); setResult(d);
  }
  return (
    <main>
      <h2>First‑run setup</h2>
      <ol>
        <li>Optionally set an API token for admin routes (or leave blank to auto‑generate a strong one).</li>
        <li>Click <b>Initialize</b>. Copy the token and use it as <code>Authorization: Bearer &lt;token&gt;</code>.</li>
        <li>Go to <a href="/admin">Admin</a> to run a quick ingest.</li>
      </ol>
      <div style={{ display:"flex", gap:8, alignItems:"center" }}>
        <input value={token} onChange={e=>setToken(e.target.value)} placeholder="Custom API token (optional)" style={{ padding:8, borderRadius:8, border:"1px solid #152131", background:"#0d141c", color:"#e6eef7", flex:1 }}/>
        <button onClick={init} style={{ padding:"8px 12px", borderRadius:12, background:"#60a5fa", color:"#0b0f14", border:"none" }}>Initialize</button>
      </div>
      {result && (
        <div style={{ marginTop:12, background:"#0f1620", border:"1px solid #152131", borderRadius:16, padding:12 }}>
          <p><b>API token:</b> <code>{result.api_token}</code></p>
          <p>Store safely. You can rotate it by re‑running this setup.</p>
        </div>
      )}
    </main>
  );
}
