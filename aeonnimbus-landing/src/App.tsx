import { useEffect, useRef } from 'react';
import './App.css';
import { PRODUCTS, JOURNEY } from './products';

function useReveal<T extends HTMLElement>() {
    const ref = useRef<T>(null);
    useEffect(() => {
        const el = ref.current;
        if (!el) return;
        const io = new IntersectionObserver(
            ([entry]) => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    io.unobserve(entry.target);
                }
            },
            { threshold: 0.15 },
        );
        io.observe(el);
        return () => io.disconnect();
    }, []);
    return ref;
}

function Reveal({ children, className = '' }: { children: React.ReactNode; className?: string }) {
    const ref = useReveal<HTMLDivElement>();
    return (
        <div ref={ref} className={`fade-in ${className}`}>
            {children}
        </div>
    );
}

export default function App() {
    return (
        <div className="page">
            <div className="glow gold" />
            <div className="glow blue" />
            <div className="glow green" />

            <nav className="nav">
                <div className="nav-inner">
                    <div className="brand">
                        <span className="mark">A</span>
                        AEON NIMBUS
                    </div>
                    <div className="nav-links">
                        <a href="#suite">Intelligence Suite</a>
                        <a href="#journey">How It Works</a>
                        <a href="#track-record">Track Record</a>
                        <a href="#pricing">Pricing</a>
                    </div>
                    <a className="nav-cta" href={`${import.meta.env.BASE_URL}select.html`}>
                        Start Free Trial
                    </a>
                </div>
            </nav>

            <div className="container">
                <section className="hero">
                    <div className="eyebrow">
                        <span className="dot-live" />
                        Built on a live, published track record — not a backtest
                    </div>
                    <h1>
                        Institutional intelligence,
                        <br />
                        <span className="accent">democratized.</span>
                    </h1>
                    <p className="sub">
                        Four connected tools — research, timing, synthesis, and monitoring — built on the same process behind a public 6/6
                        profitable-call record and a +28.4% model portfolio. Not a signal box. The workflow itself.
                    </p>
                    <div className="hero-ctas">
                        <a className="btn-primary" href={`${import.meta.env.BASE_URL}select.html`}>
                            Start Free Trial
                        </a>
                        <a className="btn-ghost" href="#suite">
                            See the 4 tools →
                        </a>
                    </div>

                    <Reveal>
                        <div className="stats">
                            <div className="stat-cell">
                                <div className="stat-num">6/6</div>
                                <div className="stat-label">Profitable Calls</div>
                            </div>
                            <div className="stat-cell">
                                <div className="stat-num">+34.5%</div>
                                <div className="stat-label">Avg. Return / Call</div>
                            </div>
                            <div className="stat-cell">
                                <div className="stat-num gold">+28.4%</div>
                                <div className="stat-label">Model Portfolio, Since Inception</div>
                            </div>
                            <div className="stat-cell">
                                <div className="stat-num gold">1.31</div>
                                <div className="stat-label">Sharpe Ratio</div>
                            </div>
                        </div>
                    </Reveal>
                </section>

                <section className="section" id="watch">
                    <Reveal>
                        <div className="section-head">
                            <div className="kicker">See It In Action</div>
                            <h2>The 35-second overview</h2>
                            <p>The whole suite, the process behind it, and the record it's built on.</p>
                        </div>
                    </Reveal>
                    <Reveal>
                        <div className="watch-video">
                            <video src={`${import.meta.env.BASE_URL}videos/aeon-explainer.mp4`} controls playsInline preload="metadata" />
                        </div>
                    </Reveal>
                </section>

                <section className="section" id="suite">
                    <Reveal>
                        <div className="section-head">
                            <div className="kicker">The Intelligence Suite</div>
                            <h2>Four tools. One process.</h2>
                            <p>Each layer answers one question a trade needs answered — in order.</p>
                        </div>
                    </Reveal>
                    <Reveal>
                        <div className="product-grid">
                            {PRODUCTS.map((p) => (
                                <div className="product-card" key={p.name}>
                                    <div className="icon">{p.icon}</div>
                                    <div className="layer">{p.layer}</div>
                                    <h3>{p.name}</h3>
                                    <span className={`status ${p.status}`}>
                                        {p.status === 'live' ? 'LIVE' : p.status === 'desktop' ? 'LIVE · DESKTOP APP' : 'IN REDESIGN'}
                                    </span>
                                    <p>
                                        <b style={{ color: 'var(--text)' }}>{p.tag}.</b> {p.desc}
                                    </p>
                                    <video
                                        className="card-video"
                                        src={`${import.meta.env.BASE_URL}${p.video.replace(/^\//, '')}`}
                                        controls
                                        playsInline
                                        preload="metadata"
                                    />
                                    {p.href ? (
                                        <a className="cta" href={p.href} target="_blank" rel="noreferrer">
                                            {p.status === 'desktop' ? `Get ${p.name} source` : `Launch ${p.name}`} →
                                        </a>
                                    ) : p.status === 'desktop' ? (
                                        <span className="cta" style={{ color: 'var(--text-dim)' }}>
                                            Runs locally as a native app
                                        </span>
                                    ) : (
                                        <span className="cta" style={{ color: 'var(--text-dim)' }}>
                                            Coming soon
                                        </span>
                                    )}
                                </div>
                            ))}
                        </div>
                    </Reveal>
                    <Reveal>
                        <p className="verify-note" style={{ marginTop: 28 }}>
                            Aeon Platform's own coverage: <b style={{ color: 'var(--text)' }}>319 global companies</b> tracked ·{' '}
                            <b style={{ color: 'var(--text)' }}>35+ live API endpoints</b> powering its research pipeline.
                        </p>
                    </Reveal>
                </section>

                <section className="section" id="journey">
                    <Reveal>
                        <div className="section-head">
                            <div className="kicker">How It Works</div>
                            <h2>The user journey</h2>
                            <p>Every product hands off to the next — from idea to live monitoring.</p>
                        </div>
                    </Reveal>
                    <Reveal>
                        <div className="journey">
                            {JOURNEY.map((s) => (
                                <div className="step" key={s.n}>
                                    <div className="num">
                                        {s.n} — {s.product}
                                    </div>
                                    <h4>{s.title}</h4>
                                    <p>{s.desc}</p>
                                    <div className="out">{s.out}</div>
                                </div>
                            ))}
                        </div>
                    </Reveal>
                </section>

                <section className="section" id="track-record">
                    <Reveal>
                        <div className="section-head">
                            <div className="kicker">Proof, Not Promises</div>
                            <h2>From published thesis to closed trade</h2>
                            <p>Real calls, walked through each layer of the suite — not a backtest.</p>
                        </div>
                    </Reveal>

                    <Reveal>
                        <div className="stats" style={{ marginTop: 0, marginBottom: 48 }}>
                            <div className="stat-cell">
                                <div className="stat-num">6/6</div>
                                <div className="stat-label">Profitable Calls</div>
                            </div>
                            <div className="stat-cell">
                                <div className="stat-num">+34.5%</div>
                                <div className="stat-label">Avg. Return / Call</div>
                            </div>
                            <div className="stat-cell">
                                <div className="stat-num gold">+28.4%</div>
                                <div className="stat-label">Model Portfolio, Since Inception</div>
                            </div>
                            <div className="stat-cell">
                                <div className="stat-num gold">1.31</div>
                                <div className="stat-label">Sharpe Ratio</div>
                            </div>
                        </div>
                    </Reveal>

                    <Reveal>
                        <div className="case-grid">
                            <div className="usecase">
                                <div>
                                    <span className="ticker-badge">ORCL</span>
                                    <h3>"The $98B cloud backlog invisible to the street"</h3>
                                    <p style={{ fontSize: 14, lineHeight: 1.6 }}>
                                        Entry at $143.36 on a thesis that Oracle's cloud infrastructure backlog was mispriced by the market.
                                        Closed at +74.3%.
                                    </p>
                                    <div className="result">+74.3%</div>
                                </div>
                                <ul>
                                    <li>
                                        <b>Aeon Analysis —</b>&nbsp;DCF confirmed backlog-adjusted undervaluation vs. peers
                                    </li>
                                    <li>
                                        <b>Intelligence —</b>&nbsp;Earnings sat at D-12, inside the Accumulation phase
                                    </li>
                                    <li>
                                        <b>Platform —</b>&nbsp;AI insight flagged institutional accumulation pre-print
                                    </li>
                                    <li>
                                        <b>Terminal —</b>&nbsp;Real-time feed surfaced cloud-deal headlines pre-rally
                                    </li>
                                </ul>
                            </div>

                            <div className="usecase">
                                <div>
                                    <span className="ticker-badge">RDDT</span>
                                    <h3>"AI's training feedstock, not its victim"</h3>
                                    <p style={{ fontSize: 14, lineHeight: 1.6 }}>
                                        Early entry on the thesis that Reddit's user-generated data was an AI-training asset the market was
                                        mispricing as a risk. Closed at +32.5%.
                                    </p>
                                    <div className="result">+32.5%</div>
                                </div>
                                <ul>
                                    <li>
                                        <b>Aeon Analysis —</b>&nbsp;Comparative analysis vs. other social/data platforms
                                    </li>
                                    <li>
                                        <b>Intelligence —</b>&nbsp;Tracked IPO lockup-expiration timing risk
                                    </li>
                                    <li>
                                        <b>Platform —</b>&nbsp;Sentiment tracking flagged institutional flow shift
                                    </li>
                                    <li>
                                        <b>Terminal —</b>&nbsp;Live user-growth and API-deal headline monitoring
                                    </li>
                                </ul>
                            </div>
                        </div>
                    </Reveal>

                    <Reveal>
                        <p className="verify-note">
                            These are two calls from a published, 6-for-6 record.{' '}
                            <a href="https://aeonnimbus.com" target="_blank" rel="noreferrer">
                                Verify the full track record on aeonnimbus.com →
                            </a>
                        </p>
                    </Reveal>
                </section>

                <section className="section" id="pricing">
                    <Reveal>
                        <div className="section-head">
                            <div className="kicker">Pricing</div>
                            <h2>Free tools. Paid edge.</h2>
                            <p>Research stays free. The suite is the professional upgrade.</p>
                        </div>
                    </Reveal>
                    <Reveal>
                        <div className="pricing-grid">
                            <div className="price-card">
                                <h4>Free</h4>
                                <div className="amount">
                                    $0<span>/mo</span>
                                </div>
                                <ul>
                                    <li>3 Aeon Analysis runs / day</li>
                                    <li>Intelligence: 7-day horizon</li>
                                    <li>Platform: view-only signals</li>
                                    <li>Terminal: 1hr-delayed news</li>
                                </ul>
                                <button>Get Started</button>
                            </div>
                            <div className="price-card highlight">
                                <h4>Professional</h4>
                                <div className="amount">
                                    $39<span>/mo · early access</span>
                                </div>
                                <ul>
                                    <li>Unlimited Aeon Analysis + PDF export</li>
                                    <li>Intelligence: 90-day horizon + AI predictions</li>
                                    <li>Platform: unlimited signals & alerts</li>
                                    <li>Terminal: real-time, all sources</li>
                                </ul>
                                <button
                                    onClick={() => {
                                        window.location.href = `${import.meta.env.BASE_URL}select.html`;
                                    }}
                                >
                                    Start Free Trial
                                </button>
                            </div>
                            <div className="price-card">
                                <h4>Systematic</h4>
                                <div className="amount">
                                    $249<span>/mo · early access</span>
                                </div>
                                <ul>
                                    <li>Everything in Professional</li>
                                    <li>12 systematic strategy signals</li>
                                    <li>Real-time model portfolio</li>
                                    <li>Monthly strategy call + API access</li>
                                </ul>
                                <button>Talk to Us</button>
                            </div>
                            <div className="price-card">
                                <h4>Institutional</h4>
                                <div className="amount">Custom</div>
                                <ul>
                                    <li>White-label intelligence suite</li>
                                    <li>Custom strategy development</li>
                                    <li>On-premise deployment</li>
                                    <li>Dedicated support & team seats</li>
                                </ul>
                                <button>Contact Sales</button>
                            </div>
                        </div>
                    </Reveal>
                </section>

                <section className="footer-cta">
                    <Reveal>
                        <h2>
                            The same tools behind a +34.5% average return.
                            <br />
                            Now available to you.
                        </h2>
                        <p>14-day free trial on Professional. No card required.</p>
                        <div className="hero-ctas" style={{ marginTop: 28 }}>
                            <a className="btn-primary" href={`${import.meta.env.BASE_URL}select.html`}>
                                Start Free Trial
                            </a>
                            <a className="btn-ghost" href="#suite">
                                Explore the Suite
                            </a>
                        </div>
                    </Reveal>
                </section>
            </div>

            <footer>© {new Date().getFullYear()} Aeon Nimbus. Independent research + intelligence tools.</footer>
        </div>
    );
}
