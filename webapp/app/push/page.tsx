
"use client";
import { useEffect, useState } from "react";
const API = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8001";

export default function PushPage() {
  const [pub, setPub] = useState<string>("");
  const [status, setStatus] = useState<string>("");
  useEffect(()=>{
    fetch(`${API}/api/push/public_key`).then(r=>r.json()).then(d=> setPub(d.public_key || ""));
  }, []);

  async function subscribe() {
    if (!("serviceWorker" in navigator)) { setStatus("Service worker not supported."); return; }
    const reg = await navigator.serviceWorker.ready;
    if (!pub) { setStatus("No VAPID public key set on server."); return; }
    const sub = await reg.pushManager.subscribe({
      userVisibleOnly: true,
      applicationServerKey: urlBase64ToUint8Array(pub)
    });
    const r = await fetch(`${API}/api/push/register`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(sub)
    });
    const d = await r.json();
    setStatus(d.ok ? "Subscribed." : "Failed to subscribe.");
  }

  async function testPush() {
    const r = await fetch(`${API}/api/push/test`, { method: "POST" });
    const d = await r.json();
    setStatus(`Sent test to ${d.sent} subscribers.`);
  }

  return (
    <main>
      <h2>Push Notifications</h2>
      <p>VAPID public key: <code style={{wordBreak:"break-all"}}>{pub || "(unset)"}</code></p>
      <div style={{ display:"flex", gap:8 }}>
        <button onClick={subscribe} style={{ padding:"8px 12px", borderRadius:12, background:"#60a5fa", color:"#0b0f14", border:"none" }}>Subscribe</button>
        <button onClick={testPush} style={{ padding:"8px 12px", borderRadius:12, background:"#34d399", color:"#0b0f14", border:"none" }}>Send Test</button>
      </div>
      <p style={{ marginTop:8 }}>{status}</p>
      <script dangerouslySetInnerHTML={{__html:`
        function urlBase64ToUint8Array(base64String) {
          const padding = '='.repeat((4 - base64String.length % 4) % 4);
          const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
          const rawData = atob(base64);
          const outputArray = new Uint8Array(rawData.length);
          for (let i = 0; i < rawData.length; ++i) { outputArray[i] = rawData.charCodeAt(i); }
          return outputArray;
        }
      `}}/>
    </main>
  );
}
