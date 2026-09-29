import React, { useState, useEffect } from 'react';
import './Landing.css';

interface LandingProps {
    onEnter: () => void;
}

export const Landing: React.FC<LandingProps> = ({ onEnter }) => {
    const [activeDemo, setActiveDemo] = useState<'signals' | 'portfolio' | 'insights'>('signals');
    const [terminalText, setTerminalText] = useState('');

    const terminalLines = [
        '$ aeon-nimbus-intelligence --init',
        '> Initializing market intelligence system...',
        '> Loading event tracking framework...',
        '> Connecting real-time data feeds...',
        '> AI analysis engine ready.',
        '> System operational.',
        '',
        '> 847 events tracked | 1,243 news items analyzed | 23 signals generated',
        '',
    ];

    useEffect(() => {
        let index = 0;
        const interval = setInterval(() => {
            if (index < terminalLines.join('\n').length) {
                setTerminalText(terminalLines.join('\n').substring(0, index));
                index += 2;
            }
        }, 20);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="landing-page">
            {/* Hero Section */}
            <section className="hero-section">
                <div className="hero-content">
                    <div className="hero-badge">AEON NIMBUS</div>
                    <h1 className="hero-title">Intelligence</h1>
                    <p className="hero-subtitle">Event-driven market intelligence that detects opportunities before they're priced in</p>

                    <div className="terminal-demo">
                        <div className="terminal-header">
                            <span className="terminal-dot"></span>
                            <span className="terminal-dot"></span>
                            <span className="terminal-dot"></span>
                            <span className="terminal-title">intelligence-core</span>
                        </div>
                        <div className="terminal-body">
                            <pre>{terminalText}</pre>
                            <span className="terminal-cursor">_</span>
                        </div>
                    </div>

                    <div className="hero-cta">
                        <button className="cta-primary" onClick={onEnter}>
                            Launch Platform
                        </button>
                        <button
                            className="cta-secondary"
                            onClick={() => document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })}
                        >
                            View Features
                        </button>
                    </div>

                    <div className="hero-stats">
                        <div className="stat-item">
                            <div className="stat-value">D-X Phase System</div>
                            <div className="stat-label">Proprietary Event Timing</div>
                        </div>
                        <div className="stat-item">
                            <div className="stat-value">68% Win Rate</div>
                            <div className="stat-label">Accumulation Phase Signals</div>
                        </div>
                        <div className="stat-item">
                            <div className="stat-value">Real-time</div>
                            <div className="stat-label">10s Update Frequency</div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Ecosystem Section */}
            <section className="ecosystem-section">
                <div className="section-container">
                    <h2 className="section-title">The Aeon Nimbus Ecosystem</h2>
                    <p className="section-description">Three integrated products that transform intelligence into alpha</p>

                    <div className="ecosystem-flow">
                        <div className="ecosystem-card intelligence-card">
                            <div className="card-icon">⚡</div>
                            <h3>Intelligence</h3>
                            <p>Detect opportunities using event-driven analysis and AI-powered insights</p>
                            <div className="card-features">
                                <span>• D-X Phase System</span>
                                <span>• Signal Generation</span>
                                <span>• Portfolio Analysis</span>
                            </div>
                        </div>

                        <div className="flow-arrow">→</div>

                        <div className="ecosystem-card terminal-card">
                            <div className="card-icon">💻</div>
                            <h3>Terminal</h3>
                            <p>Execute trades with one-click signal integration and portfolio management</p>
                            <div className="card-features">
                                <span>• Signal Import</span>
                                <span>• Order Execution</span>
                                <span>• Position Tracking</span>
                            </div>
                        </div>

                        <div className="flow-arrow">→</div>

                        <div className="ecosystem-card platform-card">
                            <div className="card-icon">📊</div>
                            <h3>Platform</h3>
                            <p>Validate strategies with historical backtesting and optimization</p>
                            <div className="card-features">
                                <span>• Strategy Builder</span>
                                <span>• Backtesting</span>
                                <span>• Performance Analytics</span>
                            </div>
                        </div>
                    </div>

                    <div className="ecosystem-loop">
                        <div className="loop-text">
                            Intelligence feeds Terminal → Terminal validates on Platform → Platform refines Intelligence
                        </div>
                    </div>
                </div>
            </section>

            {/* Features Section */}
            <section id="features" className="features-section">
                <div className="section-container">
                    <h2 className="section-title">Core Capabilities</h2>

                    <div className="demo-selector">
                        <button className={activeDemo === 'signals' ? 'active' : ''} onClick={() => setActiveDemo('signals')}>
                            Trading Signals
                        </button>
                        <button className={activeDemo === 'portfolio' ? 'active' : ''} onClick={() => setActiveDemo('portfolio')}>
                            Portfolio Intelligence
                        </button>
                        <button className={activeDemo === 'insights' ? 'active' : ''} onClick={() => setActiveDemo('insights')}>
                            AI Insights
                        </button>
                    </div>

                    {activeDemo === 'signals' && (
                        <div className="demo-content">
                            <div className="demo-visual">
                                <div className="mock-signal-card">
                                    <div className="signal-header-mock">
                                        <span className="signal-ticker-mock">AAPL</span>
                                        <span className="signal-action-mock">BUY</span>
                                    </div>
                                    <div className="signal-metrics-mock">
                                        <div>
                                            <span>Entry</span>
                                            <strong>$178.50</strong>
                                        </div>
                                        <div>
                                            <span>Target</span>
                                            <strong className="green">$185.20</strong>
                                        </div>
                                        <div>
                                            <span>Stop</span>
                                            <strong className="red">$175.80</strong>
                                        </div>
                                    </div>
                                    <div className="signal-stats-mock">
                                        <div>
                                            R:R <strong>2.48:1</strong>
                                        </div>
                                        <div>
                                            Confidence <strong>82%</strong>
                                        </div>
                                        <div>
                                            D-14 <strong>Accumulation</strong>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div className="demo-description">
                                <h3>Auto-Generated Trading Signals</h3>
                                <p className="desc-main">
                                    AI analyzes events in the accumulation phase (D-10 to D-20) and automatically calculates entry points,
                                    profit targets, and stop losses based on historical pattern matching.
                                </p>
                                <ul className="desc-features">
                                    <li>
                                        <strong>Probability-Weighted:</strong> Each signal shows confidence score based on historical win
                                        rates
                                    </li>
                                    <li>
                                        <strong>Risk-Managed:</strong> Automatic R:R calculation ensures favorable risk/reward ratios
                                    </li>
                                    <li>
                                        <strong>Event-Driven:</strong> Tied to specific catalysts with clear timeframes
                                    </li>
                                    <li>
                                        <strong>One-Click Export:</strong> Send directly to Aeon Nimbus Terminal for execution
                                    </li>
                                </ul>
                            </div>
                        </div>
                    )}

                    {activeDemo === 'portfolio' && (
                        <div className="demo-content">
                            <div className="demo-visual">
                                <div className="mock-portfolio-card">
                                    <div className="portfolio-header-mock">
                                        <span className="portfolio-ticker-mock">NVDA</span>
                                        <span className="risk-badge-mock high">HIGH RISK</span>
                                    </div>
                                    <div className="portfolio-metrics-mock">
                                        <div>
                                            <span>Upcoming Events</span>
                                            <strong>7</strong>
                                        </div>
                                        <div>
                                            <span>Aggregate Impact</span>
                                            <strong>8.4/10</strong>
                                        </div>
                                    </div>
                                    <div className="portfolio-rec-mock">
                                        <div className="rec-label-mock">Recommendation:</div>
                                        <div className="rec-text-mock">
                                            Consider reducing exposure before high-impact earnings. 3 events in next 7 days.
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div className="demo-description">
                                <h3>Portfolio Impact Analysis</h3>
                                <p className="desc-main">
                                    Real-time risk assessment for every position in your watchlist. Know exactly how upcoming events will
                                    impact your holdings before they happen.
                                </p>
                                <ul className="desc-features">
                                    <li>
                                        <strong>Event Clustering:</strong> Identifies when multiple catalysts converge on single positions
                                    </li>
                                    <li>
                                        <strong>Impact Scoring:</strong> Quantifies aggregate risk from all upcoming events
                                    </li>
                                    <li>
                                        <strong>Smart Recommendations:</strong> Position sizing guidance based on event calendar
                                    </li>
                                    <li>
                                        <strong>Correlation Warnings:</strong> Alerts when multiple holdings face similar risks
                                    </li>
                                </ul>
                            </div>
                        </div>
                    )}

                    {activeDemo === 'insights' && (
                        <div className="demo-content">
                            <div className="demo-visual">
                                <div className="mock-insight-card">
                                    <div className="insight-header-mock">
                                        <span className="insight-type-mock">OPPORTUNITY</span>
                                        <span className="insight-confidence-mock">82%</span>
                                    </div>
                                    <h4 className="insight-title-mock">Multiple Accumulation Phase Setups</h4>
                                    <p className="insight-desc-mock">
                                        6 high-probability setups in optimal entry window (D-10 to D-20). Historical win rate: 68%.
                                    </p>
                                    <div className="insight-tickers-mock">
                                        <span>AAPL</span>
                                        <span>MSFT</span>
                                        <span>GOOGL</span>
                                        <span>NVDA</span>
                                    </div>
                                </div>
                            </div>
                            <div className="demo-description">
                                <h3>AI-Generated Market Insights</h3>
                                <p className="desc-main">
                                    Pattern recognition engine analyzes cross-market data to surface opportunities and risks that aren't
                                    visible from individual events alone.
                                </p>
                                <ul className="desc-features">
                                    <li>
                                        <strong>Event Clustering:</strong> Detects sector-wide catalyst convergence
                                    </li>
                                    <li>
                                        <strong>Sentiment Divergence:</strong> Identifies when news sentiment contradicts price action
                                    </li>
                                    <li>
                                        <strong>Volatility Alerts:</strong> Warns of elevated near-term risk from event clusters
                                    </li>
                                    <li>
                                        <strong>Pattern Matching:</strong> Compares current setup to historical precedents
                                    </li>
                                </ul>
                            </div>
                        </div>
                    )}
                </div>
            </section>

            {/* How It Works */}
            <section className="workflow-section">
                <div className="section-container">
                    <h2 className="section-title">How It Works</h2>
                    <p className="section-description">The D-X Phase System explained</p>

                    <div className="workflow-steps">
                        <div className="workflow-step">
                            <div className="step-number">01</div>
                            <div className="step-icon danger">⚠️</div>
                            <h3>Danger Phase (D-0 to D-2)</h3>
                            <p>
                                Event imminent. Maximum volatility. Exit positions or execute final adjustments. News already priced in,
                                risk of "sell the news" event.
                            </p>
                            <div className="step-action">Action: Close or hedge positions</div>
                        </div>

                        <div className="workflow-step">
                            <div className="step-number">02</div>
                            <div className="step-icon euforia">🔥</div>
                            <h3>Euforia Phase (D-3 to D-9)</h3>
                            <p>
                                Hype building. FOMO kicking in. Prices running up on speculation. Late entries high risk. Consider
                                profit-taking on existing positions.
                            </p>
                            <div className="step-action">Action: Take profits, avoid new entries</div>
                        </div>

                        <div className="workflow-step">
                            <div className="step-number">03</div>
                            <div className="step-icon accumulation">📈</div>
                            <h3>Accumulation Phase (D-10 to D-20)</h3>
                            <p>
                                <strong>Sweet spot for entries.</strong> Event known but not yet hyped. Smart money accumulating. Best
                                risk/reward ratio. Historical 68% win rate in this window.
                            </p>
                            <div className="step-action success">Action: Primary entry zone - size positions</div>
                        </div>

                        <div className="workflow-step">
                            <div className="step-number">04</div>
                            <div className="step-icon pre-rumor">📡</div>
                            <h3>Pre-Rumor Phase (D-20+)</h3>
                            <p>
                                Event announced but far out. Price impact minimal. Watch for confirmation signals. Build watchlist, set
                                alerts, research historical patterns.
                            </p>
                            <div className="step-action">Action: Research & watchlist building</div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Keyboard Shortcuts */}
            <section className="shortcuts-section">
                <div className="section-container">
                    <h2 className="section-title">Keyboard-First Workflow</h2>
                    <p className="section-description">Professional traders work at terminal speed</p>

                    <div className="shortcuts-grid">
                        <div className="shortcut-item">
                            <div className="shortcut-key">⌘K</div>
                            <div className="shortcut-desc">Command Palette - Fast navigation</div>
                        </div>
                        <div className="shortcut-item">
                            <div className="shortcut-key">1-5</div>
                            <div className="shortcut-desc">Switch tabs instantly</div>
                        </div>
                        <div className="shortcut-item">
                            <div className="shortcut-key">⌘E</div>
                            <div className="shortcut-desc">Export to Terminal</div>
                        </div>
                        <div className="shortcut-item">
                            <div className="shortcut-key">⌘S</div>
                            <div className="shortcut-desc">Send to Platform</div>
                        </div>
                        <div className="shortcut-item">
                            <div className="shortcut-key">W</div>
                            <div className="shortcut-desc">Add to watchlist</div>
                        </div>
                        <div className="shortcut-item">
                            <div className="shortcut-key">ESC</div>
                            <div className="shortcut-desc">Close panels</div>
                        </div>
                    </div>
                </div>
            </section>

            {/* Pricing Tiers */}
            <section className="pricing-section">
                <div className="section-container">
                    <h2 className="section-title">Choose Your Tier</h2>

                    <div className="pricing-grid">
                        <div className="pricing-card">
                            <div className="price-header">
                                <h3>Pro</h3>
                                <div className="price">
                                    $49<span>/month</span>
                                </div>
                            </div>
                            <ul className="price-features">
                                <li>Real-time news feed</li>
                                <li>Full D-X phase tracking</li>
                                <li>Unlimited watchlist</li>
                                <li>Basic signal generation</li>
                                <li>100 API calls/day</li>
                            </ul>
                            <button className="price-cta">Start Free Trial</button>
                        </div>

                        <div className="pricing-card featured">
                            <div className="featured-badge">MOST POPULAR</div>
                            <div className="price-header">
                                <h3>Alpha</h3>
                                <div className="price">
                                    $199<span>/month</span>
                                </div>
                            </div>
                            <ul className="price-features">
                                <li>
                                    <strong>Everything in Pro, plus:</strong>
                                </li>
                                <li>Advanced probability scoring</li>
                                <li>Portfolio impact analysis</li>
                                <li>AI-generated insights</li>
                                <li>Terminal integration</li>
                                <li>Priority alerts (SMS)</li>
                                <li>1,000 API calls/day</li>
                            </ul>
                            <button className="price-cta primary">Start Free Trial</button>
                        </div>

                        <div className="pricing-card">
                            <div className="price-header">
                                <h3>Institutional</h3>
                                <div className="price">
                                    $999<span>/month</span>
                                </div>
                            </div>
                            <ul className="price-features">
                                <li>
                                    <strong>Everything in Alpha, plus:</strong>
                                </li>
                                <li>Custom event rules</li>
                                <li>White-label options</li>
                                <li>Dedicated support</li>
                                <li>Platform integration</li>
                                <li>Team accounts (5 seats)</li>
                                <li>Unlimited API access</li>
                            </ul>
                            <button className="price-cta">Contact Sales</button>
                        </div>
                    </div>
                </div>
            </section>

            {/* Final CTA */}
            <section className="final-cta-section">
                <div className="section-container">
                    <h2 className="final-cta-title">Start Generating Alpha Today</h2>
                    <p className="final-cta-desc">
                        Join professional traders using Aeon Nimbus to detect opportunities before they're priced in
                    </p>
                    <button className="final-cta-button" onClick={onEnter}>
                        Launch Intelligence Platform
                    </button>
                    <div className="final-cta-note">14-day free trial • No credit card required • Cancel anytime</div>
                </div>
            </section>
        </div>
    );
};
