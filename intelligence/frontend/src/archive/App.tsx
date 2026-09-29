import React, { useState, useEffect } from 'react';
import './App.css';

interface Event {
    id: number;
    title: string;
    date: string;
    event_type: string;
    description: string;
    impact_score: number;
    affected_tickers: string;
    phase: string;
    days_away: number;
    recommendation?: string;
}

function App() {
    const [events, setEvents] = useState<Event[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<'events' | 'signals' | 'portfolio'>('events');
    // Opened from Aeon Analysis with ?ticker=XYZ — filters this (still synthetic
    // demo) event feed down to that ticker instead of showing everything.
    const [tickerFilter, setTickerFilter] = useState(() => new URLSearchParams(window.location.search).get('ticker') || '');

    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await fetch('http://localhost:8001/api/events/live');
                if (!response.ok) throw new Error('Failed to fetch');
                const data = await response.json();
                setEvents(data);
                setLoading(false);
            } catch (err) {
                setError('Failed to connect to API');
                setLoading(false);
            }
        };

        fetchData();
        const interval = setInterval(fetchData, 10000);
        return () => clearInterval(interval);
    }, []);

    if (loading) {
        return (
            <div className="app">
                <div className="loading">
                    <div className="spinner"></div>
                    <p>LOADING SYSTEM...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="app">
                <div className="error">
                    <h2>CONNECTION ERROR</h2>
                    <p>{error}</p>
                    <button onClick={() => window.location.reload()}>RETRY</button>
                </div>
            </div>
        );
    }

    return (
        <div className="app">
            <header className="header">
                <div className="brand">
                    <div className="brand-name">AEON NIMBUS</div>
                    <div className="brand-sub">INTELLIGENCE</div>
                </div>
                <nav className="nav">
                    <button className={activeTab === 'events' ? 'active' : ''} onClick={() => setActiveTab('events')}>
                        EVENTS
                    </button>
                    <button className={activeTab === 'signals' ? 'active' : ''} onClick={() => setActiveTab('signals')}>
                        SIGNALS
                    </button>
                    <button className={activeTab === 'portfolio' ? 'active' : ''} onClick={() => setActiveTab('portfolio')}>
                        PORTFOLIO
                    </button>
                </nav>
                <div className="status">
                    <span className="dot"></span>
                    LIVE
                </div>
            </header>

            <main className="main">
                <div className="stats">
                    <div className="stat-card">
                        <div className="stat-label">EVENTS TRACKED</div>
                        <div className="stat-value">{events.length}</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-label">DANGER PHASE</div>
                        <div className="stat-value danger">{events.filter((e) => e.phase === 'DANGER').length}</div>
                    </div>
                    <div className="stat-card">
                        <div className="stat-label">ACCUMULATION</div>
                        <div className="stat-value success">{events.filter((e) => e.phase === 'ACCUMULATION').length}</div>
                    </div>
                </div>

                <div className="events-list">
                    <h2>TRACKED EVENTS</h2>
                    {tickerFilter && (
                        <div className="event-meta" style={{ marginBottom: 12 }}>
                            Filtered to <strong>{tickerFilter.toUpperCase()}</strong> ·{' '}
                            <button
                                onClick={() => {
                                    setTickerFilter('');
                                    window.history.replaceState(null, '', window.location.pathname);
                                }}
                                style={{
                                    background: 'none',
                                    border: 'none',
                                    color: 'inherit',
                                    textDecoration: 'underline',
                                    cursor: 'pointer',
                                    padding: 0,
                                }}
                            >
                                view all events
                            </button>
                        </div>
                    )}
                    {(tickerFilter ? events.filter((e) => e.affected_tickers.toUpperCase().includes(tickerFilter.toUpperCase())) : events)
                        .slice(0, 20)
                        .map((event) => (
                            <div key={event.id} className="event-card">
                                <div className="event-header">
                                    <div className="event-ticker">{event.affected_tickers}</div>
                                    <div className={`event-phase ${event.phase.toLowerCase()}`}>{event.phase}</div>
                                </div>
                                <div className="event-title">{event.title}</div>
                                <div className="event-meta">
                                    D-{event.days_away} • {event.event_type} • Impact: {event.impact_score.toFixed(1)}
                                </div>
                                {event.recommendation && <div className="event-rec">{event.recommendation}</div>}
                            </div>
                        ))}
                </div>
            </main>
        </div>
    );
}

export default App;
