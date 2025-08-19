
"use client";
import { useEffect, useState } from "react";
const API = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8001";
export default function Dashboard() {
  const [trades, setTrades] = useState<any[]>([]);
  const [alpha, setAlpha] = useState<number | null>(null);
  const [brief, setBrief] = useState<string>("");
  const [busy, setBusy] = useState(false);
  useEffect(()=>{
    fetch(`${API}/api/trades?limit=10`, { credentials: "include" }).then(r=>r.json()).then(d=> setTrades(d.items || []));
    fetch(`${API}/api/backtest`, { credentials: "include" }).then(r=>r.json()).then(d=> setAlpha(d.summary?.alpha ?? null));
  }, []);
  async function genBrief() {
    setBusy(true);
    try{
      const r = await fetch(`${API}/api/brief/latest`, { method: "POST", credentials: "include" });
      const d = await r.json();
      if (d.ok) setBrief(d.content_md || "");
      else setBrief("No brief available.");
    } finally { setBusy(false); }
  }
  return (
    <main>
      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:16 }}>
        <div style={{ background:"#0f1620", border:"1px solid #152131", borderRadius:16, padding:14 }}>
          <h3 style={{ marginTop:0 }}>Signal (demo)</h3>
          <p>Alpha (30d vs SPY): <b>{alpha !== null ? (alpha*100).toFixed(1) + "%" : "—"}</b></p>
        </div>
        <div style={{ background:"#0f1620", border:"1px solid #152131", borderRadius:16, padding:14 }}>
          <h3 style={{ marginTop:0 }}>Latest Brief</h3>
          <button onClick={genBrief} disabled={busy} style={{ padding:"8px 12px", borderRadius:12, background:"#60a5fa", color:"#0b0f14", border:"none" }}>
            {busy ? "Generating..." : "Generate"}
          </button>
          {brief && <pre style={{ whiteSpace:"pre-wrap", marginTop:12 }}>{brief}</pre>}
        </div>
      </div>
      <div style={{ background:"#0f1620", border:"1px solid #152131", borderRadius:16, padding:14, marginTop:16 }}>
        <h3 style={{ marginTop:0 }}>Latest Trades</h3>
        {trades.length === 0 && <p style={{ color:"#9fb0c0" }}>No trades yet.</p>}
        <ul>
          {trades.map(t => (
            <li key={t.id}><b>#{t.id}</b> — {t.trade_date || "—"} — {t.transaction_type?.toUpperCase()} {t.ticker || t.issuer || "(unknown)"} by {t.official_name || "Unknown"}</li>
          ))}
        </ul>
      </div>
    
      <div style={{ marginTop:16 }}>
        <button onClick={()=>{
          Notification.requestPermission().then(p=>{
            if (p==='granted') navigator.serviceWorker?.controller?.postMessage({ type:'notify', text:'Alerts are configured. You will receive digests when they run.' });
          });
        }} style={{ padding:"8px 12px", borderRadius:12, background:"#a78bfa", color:"#0b0f14", border:"none" }}>Test Notification</button>
      </div>
    </main>
  );
}
