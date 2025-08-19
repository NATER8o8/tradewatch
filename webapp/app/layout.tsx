
export const metadata = { title: "Official Trades Pro", description: "Public-official trades tracker" };
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en"><link rel="manifest" href="/manifest.json"/>
      <body style={{ background:"#0b0f14", color:"#e6eef7", fontFamily:"ui-sans-serif, system-ui" }}>
        <div style={{ maxWidth: 1000, margin: "0 auto", padding: 20 }}>
          <header style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom: 16 }}>
            <h1 style={{ margin:0 }}>Official Trades Pro</h1>
            <nav style={{ display:"flex", gap:12 }}>
              <a href="/" style={{ color:"#9fb0c0" }}>Dashboard</a>
              <a href="/jobs" style={{ color:"#9fb0c0" }}>Jobs</a>
            </nav>
          </header>
          {children}
        </div>
      
        <script dangerouslySetInnerHTML={{__html:`
          if ('serviceWorker' in navigator) {
            window.addEventListener('load', ()=> navigator.serviceWorker.register('/sw.js').catch(()=>{}));
          }
        `}} />
      </body>
    </html>
  )
}
