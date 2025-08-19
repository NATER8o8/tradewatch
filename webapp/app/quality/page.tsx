
"use client";
import { useEffect, useState } from "react";
const API = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8001";

export default function Quality() {
  const [rep, setRep] = useState<any>(null);
  async function run() {
    const r = await fetch(`${API}/api/admin/quality/report`);
    setRep(await r.json());
  }
  useEffect(()=>{ run(); }, []);
  if (!rep) return <main><p>Loading…</p></main>;
  return (
    <main>
      <h2>Data Quality</h2>
      <pre style={{ whiteSpace:"pre-wrap" }}>{JSON.stringify(rep, null, 2)}</pre>
    </main>
  );
}
