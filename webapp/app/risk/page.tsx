
"use client";
import { useEffect, useState } from "react";
const API = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8001";
export default function Risk() {
  const [items, setItems] = useState<any[]>([]);
  useEffect(()=>{
    fetch(`${API}/api/risk/officials`).then(r=>r.json()).then(d=> setItems(d.items||[]));
  }, []);
  return (
    <main>
      <h2>Insider‑Risk (heuristic)</h2>
      <p style={{opacity:0.8}}>0..100 score; heuristic features: frequency, committee‑sector overlap, buy/sell bias, recency.</p>
      <table style={{ width:"100%", borderCollapse:"collapse" }}>
        <thead><tr><th align="left">Official</th><th align="right">Score</th><th align="right">Freq</th><th align="right">Overlap</th><th align="right">Recency</th><th align="left">Sector</th></tr></thead>
        <tbody>
          {items.map((it:any)=>(
            <tr key={it.official_id} style={{ borderTop:"1px solid #152131" }}>
              <td>{it.official_name || it.official_id}</td>
              <td align="right">{it.score}</td>
              <td align="right">{it.freq}</td>
              <td align="right">{it.overlap}</td>
              <td align="right">{it.recency}</td>
              <td>{it.sector || "-"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </main>
  );
}
