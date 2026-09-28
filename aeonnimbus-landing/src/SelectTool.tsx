import './App.css'
import { PRODUCTS } from './products'

export default function SelectTool() {
  return (
    <div className="page">
      <div className="glow gold" />
      <div className="glow blue" />
      <div className="glow green" />

      <nav className="nav">
        <div className="nav-inner">
          <a className="brand" href={import.meta.env.BASE_URL} style={{ textDecoration: 'none', color: 'inherit' }}>
            <span className="mark">A</span>
            AEON NIMBUS
          </a>
          <a className="nav-cta" href={import.meta.env.BASE_URL}>← Back to Home</a>
        </div>
      </nav>

      <div className="container">
        <section className="hero" style={{ paddingBottom: 30 }}>
          <div className="eyebrow">
            <span className="dot-live" />
            Step 1 of 1 — Choose Your Tool
          </div>
          <h1>
            Which layer do you<br />
            <span className="accent">want to launch?</span>
          </h1>
          <p className="sub">
            Pick the tool for what you need right now. Each one opens in a new tab —
            come back here any time to launch another.
          </p>
        </section>

        <section className="section" style={{ paddingTop: 10, paddingBottom: 100 }}>
          <div className="product-grid">
            {PRODUCTS.map((p) => (
              <div className="product-card" key={p.name}>
                <div className="icon">{p.icon}</div>
                <div className="layer">{p.layer}</div>
                <h3>{p.name}</h3>
                <span className={`status ${p.status}`}>
                  {p.status === 'live' ? 'LIVE' : p.status === 'desktop' ? 'LIVE · DESKTOP APP' : 'IN REDESIGN'}
                </span>
                <p><b style={{ color: 'var(--text)' }}>{p.tag}.</b> {p.desc}</p>
                {p.href ? (
                  <a className="cta" href={p.href} target="_blank" rel="noreferrer">
                    {p.status === 'desktop' ? `Get ${p.name} source` : `Launch ${p.name}`} →
                  </a>
                ) : p.status === 'desktop' ? (
                  <span className="cta" style={{ color: 'var(--text-dim)' }}>Runs locally as a native app</span>
                ) : (
                  <span className="cta" style={{ color: 'var(--text-dim)' }}>Coming soon</span>
                )}
              </div>
            ))}
          </div>
        </section>
      </div>

      <footer>
        © {new Date().getFullYear()} Aeon Nimbus. Independent research + intelligence tools.
      </footer>
    </div>
  )
}
