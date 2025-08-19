
"use client";
import { useEffect, useState } from "react";
const API = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8001";

export default function Prov() {
  const [trades, setTrades] = useState<any[]>([]);
  const [sources, setSources] = useState<Record<number, any[]>>({});
  useEffect(()=>{
    fetch(`${API}/api/trades?limit=20`).then(r=>r.json()).then(d=> setTrades(d.items || []));
  }, []);
  async function openSources(id: number) {
    const r = await fetch(`${API}/api/trades/${id}/sources`);
    const d = await r.json();
    setSources(prev => ({...prev, [id]: d.items || []}));
  }
  return (
    <main>
      <h2>Provenance</h2>
      <ul>
        {trades.map((t:any)=>(
          <li key={t.id} style={{ marginBottom:12 }}>
            <b>#{t.id}</b> {t.trade_date} — {t.transaction_type?.toUpperCase()} {t.ticker || t.issuer} <button onClick={()=>openSources(t.id)}>Sources</button>
            {sources[t.id] && (
              <div style={{ background:"#0f1620", border:"1px solid #152131", borderRadius:12, padding:8, marginTop:6 }}>
                {(sources[t.id] || []).map((s:any)=>(
                  <div key={s.id} style={{ marginBottom:6 }}>
                    <div><b>{s.source}</b> — <a href={s.source_url} style={{ color:"#60a5fa" }}>{s.source_url}</a></div>
                    <pre style={{ whiteSpace:"pre-wrap" }}>{s.raw_json}</pre>
                  </div>
                ))}
              </div>
            )}
          </li>
        ))}
      </ul>
    </main>
  );
}
