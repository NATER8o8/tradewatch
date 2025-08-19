
"use client";
import { useEffect, useState } from "react";
const API = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8001";
export default function JobsPage() {
  const [items, setItems] = useState<any[]>([]);
  const [selected, setSelected] = useState<any | null>(null);
  const [jobId, setJobId] = useState("");
  async function load() {
    const r = await fetch(`${API}/api/jobs?limit=50`, { credentials: "include" });
    const d = await r.json();
    if (d.ok) setItems(d.items || []);
  }
  async function open(job_id: string) {
    const r = await fetch(`${API}/api/jobs/${job_id}`, { credentials: "include" });
    const d = await r.json();
    if (d.ok) setSelected(d.item);
  }
  useEffect(()=>{ load(); }, []);
  useEffect(()=>{
    if (!selected?.id) return;
    const t = setInterval(()=> open(selected.id), 1500);
    return ()=> clearInterval(t);
  }, [selected?.id]);
  return (
    <main>
      <h2>Jobs</h2>
      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:16 }}>
        <div style={{ background:"#0f1620", border:"1px solid #152131", borderRadius:16, padding:14 }}>
          <div style={{ display:"flex", gap:8, alignItems:"center"}}>
            <button onClick={load} style={{ padding:"8px 12px", borderRadius:12, background:"#60a5fa", color:"#0b0f14", border:"none" }}>Refresh</button>
            <input value={jobId} onChange={e=>setJobId(e.target.value)} placeholder="Job ID..." style={{ padding:8, borderRadius:8, border:"1px solid #152131", background:"#0d141c", color:"#e6eef7", flex:1 }}/>
            <button onClick={()=>jobId && open(jobId)} style={{ padding:"8px 12px", borderRadius:12, background:"#34d399", color:"#0b0f14", border:"none" }}>Open</button>
          </div>
          <ul style={{ marginTop:12 }}>
            {items.map((x,i)=> (
              <li key={i}><a onClick={()=>open(x.id)} style={{ cursor:"pointer", color:"#9fb0c0" }}>{x.id.slice(0,8)}…</a> — {x.status}</li>
            ))}
          </ul>
        </div>
        <div style={{ background:"#0f1620", border:"1px solid #152131", borderRadius:16, padding:14 }}>
          <h3 style={{ marginTop:0 }}>Detail</h3>
          {!selected && <p style={{ color:"#9fb0c0" }}>Select a job to view details.</p>}
          {selected && (
            <div>
              <div style={{ display:"flex", gap:8, alignItems:"center" }}>
                <div style={{ flex:1, background:"#152131", borderRadius:10, overflow:"hidden", height:14 }}>
                  <div style={{ width:`${selected.meta?.progress ?? 0}%`, height:"100%", background:"#60a5fa" }} />
                </div>
                <span style={{ color:"#9fb0c0" }}>{selected.meta?.progress ?? 0}%</span>
              </div>
              {selected.meta?.note && <p style={{ color:"#9fb0c0", marginTop:8 }}>{selected.meta.note}</p>}
              <pre style={{ whiteSpace:"pre-wrap", marginTop:12 }}>{JSON.stringify(selected, null, 2)}</pre>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
