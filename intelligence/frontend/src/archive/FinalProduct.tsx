import React, { useState, useEffect } from 'react';
import './FinalProduct.css';

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

interface NewsItem {
    id: number;
    title: string;
    content: string;
    source: string;
    published_at: string;
    sentiment: string;
    sentiment_score: number;
}

interface FearGreedData {
    value: number;
    label: string;
    color: string;
}

export const FinalProduct: React.FC = () => {
    const [events, setEvents] = useState<Event[]>([]);
    const [news, setNews] = useState<NewsItem[]>([]);
    const [activeTab, setActiveTab] = useState<'dashboard' | 'calendar' | 'earnings' | 'analysis'>('dashboard');
    const [selectedEvent, setSelectedEvent] = useState<Event | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [fearGreed, setFearGreed] = useState<FearGreedData>({ value: 52, label: 'Neutral', color: '#9e9e9e' });

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 10000);
        return () => clearInterval(interval);
    }, []);

    const fetchData = async () => {
        try {
            const [eventsRes, newsRes] = await Promise.all([
                fetch('http://localhost:8001/api/events/live'),
                fetch('http://localhost:8001/api/news/live'),
            ]);

            const eventsData = await eventsRes.json();
            const newsData = await newsRes.json();

            setEvents(eventsData || []);
            setNews(newsData.news || []);

            // Calculate Fear & Greed based on market data
            calculateFearGreed(eventsData, newsData.news || []);
        } catch (error) {
            console.error('Error fetching data:', error);
        }
    };

    const calculateFearGreed = (events: Event[], news: NewsItem[]) => {
        // Simple calculation based on sentiment and upcoming events
        const bullishNews = news.filter((n) => n.sentiment === 'bullish').length;
        const bearishNews = news.filter((n) => n.sentiment === 'bearish').length;
        const highImpactEvents = events.filter((e) => e.impact_score >= 8 && e.days_away <= 7).length;

        let score = 50; // Neutral baseline
        score += (bullishNews - bearishNews) * 5;
        score -= highImpactEvents * 3;
        score = Math.max(0, Math.min(100, score));

        let label = 'Neutral';
        let color = '#9e9e9e';

        if (score >= 75) {
            label = 'Extreme Greed';
            color = '#00c853';
        } else if (score >= 60) {
            label = 'Greed';
            color = '#64dd17';
        } else if (score >= 40) {
            label = 'Neutral';
            color = '#9e9e9e';
        } else if (score >= 25) {
            label = 'Fear';
            color = '#ff9500';
        } else {
            label = 'Extreme Fear';
            color = '#ff3b30';
        }

        setFearGreed({ value: score, label, color });
    };

    const getPhaseColor = (phase: string) => {
        if (phase.includes('DANGER')) return '#ff3b30';
        if (phase.includes('EUFORIA')) return '#ff9500';
        if (phase.includes('ACCUMULATION')) return '#34c759';
        return '#007aff';
    };

    const formatTimeAgo = (dateString: string) => {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m`;
        const diffHours = Math.floor(diffMins / 60);
        if (diffHours < 24) return `${diffHours}h`;
        return `${Math.floor(diffHours / 24)}d`;
    };

    // Group events by phase
    const dangerEvents = events.filter((e) => e.phase.includes('DANGER'));
    const euforiaEvents = events.filter((e) => e.phase.includes('EUFORIA'));
    const accumulationEvents = events.filter((e) => e.phase.includes('ACCUMULATION'));
    const preRumorEvents = events.filter((e) => e.phase.includes('PRE-RUMOR'));

    // Get earnings events
    const earningsEvents = events.filter((e) => e.event_type === 'earnings').slice(0, 10);

    // Get high impact opportunities
    const opportunities = events.filter((e) => e.impact_score >= 7 && e.days_away >= 10 && e.days_away <= 20).slice(0, 5);

    // Filter events
    const filteredEvents = events.filter((e) => !searchQuery || e.title.toLowerCase().includes(searchQuery.toLowerCase()));

    return (
        <div className="final-product">
            {/* Header */}
            <header className="product-header">
                <div className="header-brand">
                    <h1 className="brand-logo">AEON NIMBUS</h1>
                    <span className="brand-tagline">Market Intelligence Platform</span>
                </div>

                <nav className="main-nav">
                    <button className={activeTab === 'dashboard' ? 'active' : ''} onClick={() => setActiveTab('dashboard')}>
                        <span className="nav-icon">📊</span>
                        Dashboard
                    </button>
                    <button className={activeTab === 'calendar' ? 'active' : ''} onClick={() => setActiveTab('calendar')}>
                        <span className="nav-icon">📅</span>
                        Calendar
                    </button>
                    <button className={activeTab === 'earnings' ? 'active' : ''} onClick={() => setActiveTab('earnings')}>
                        <span className="nav-icon">💰</span>
                        Earnings
                    </button>
                    <button className={activeTab === 'analysis' ? 'active' : ''} onClick={() => setActiveTab('analysis')}>
                        <span className="nav-icon">🔍</span>
                        Analysis
                    </button>
                </nav>

                <div className="header-search">
                    <input
                        type="text"
                        placeholder="Search events..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                </div>
            </header>

            {/* Dashboard View */}
            {activeTab === 'dashboard' && (
                <div className="dashboard-layout">
                    {/* Top Metrics */}
                    <div className="metrics-row">
                        <div className="metric-card danger">
                            <div className="metric-icon">⚠️</div>
                            <div className="metric-content">
                                <div className="metric-value">{dangerEvents.length}</div>
                                <div className="metric-label">Danger Zone</div>
                                <div className="metric-sublabel">D-0 to D-2</div>
                            </div>
                        </div>

                        <div className="metric-card euforia">
                            <div className="metric-icon">🔥</div>
                            <div className="metric-content">
                                <div className="metric-value">{euforiaEvents.length}</div>
                                <div className="metric-label">Euforia Phase</div>
                                <div className="metric-sublabel">D-3 to D-9</div>
                            </div>
                        </div>

                        <div className="metric-card accumulation">
                            <div className="metric-icon">📈</div>
                            <div className="metric-content">
                                <div className="metric-value">{accumulationEvents.length}</div>
                                <div className="metric-label">Accumulation</div>
                                <div className="metric-sublabel">D-10 to D-20</div>
                            </div>
                        </div>

                        <div className="metric-card neutral">
                            <div className="metric-icon">📡</div>
                            <div className="metric-content">
                                <div className="metric-value">{preRumorEvents.length}</div>
                                <div className="metric-label">Pre-Rumor</div>
                                <div className="metric-sublabel">D-20+</div>
                            </div>
                        </div>

                        <div className="metric-card special">
                            <div className="metric-icon">🎯</div>
                            <div className="metric-content">
                                <div className="metric-value">{opportunities.length}</div>
                                <div className="metric-label">Opportunities</div>
                                <div className="metric-sublabel">High Impact</div>
                            </div>
                        </div>
                    </div>

                    {/* Main Content Grid */}
                    <div className="dashboard-grid">
                        {/* Left Column */}
                        <div className="grid-column left">
                            {/* Fear & Greed Index */}
                            <div className="dashboard-card">
                                <div className="card-header">
                                    <h3>Fear & Greed Index</h3>
                                </div>
                                <div className="fear-greed-display">
                                    <div className="fear-greed-gauge">
                                        <svg viewBox="0 0 200 120" className="gauge-svg">
                                            <defs>
                                                <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                                                    <stop offset="0%" style={{ stopColor: '#ff3b30' }} />
                                                    <stop offset="25%" style={{ stopColor: '#ff9500' }} />
                                                    <stop offset="50%" style={{ stopColor: '#9e9e9e' }} />
                                                    <stop offset="75%" style={{ stopColor: '#64dd17' }} />
                                                    <stop offset="100%" style={{ stopColor: '#00c853' }} />
                                                </linearGradient>
                                            </defs>
                                            <path
                                                d="M 20 100 A 80 80 0 0 1 180 100"
                                                fill="none"
                                                stroke="url(#gaugeGradient)"
                                                strokeWidth="20"
                                                strokeLinecap="round"
                                            />
                                            <circle cx="100" cy="100" r="5" fill={fearGreed.color} />
                                            <line
                                                x1="100"
                                                y1="100"
                                                x2={100 + 70 * Math.cos((((fearGreed.value / 100) * 180 - 180) * Math.PI) / 180)}
                                                y2={100 + 70 * Math.sin((((fearGreed.value / 100) * 180 - 180) * Math.PI) / 180)}
                                                stroke={fearGreed.color}
                                                strokeWidth="3"
                                                strokeLinecap="round"
                                            />
                                        </svg>
                                    </div>
                                    <div className="fear-greed-info">
                                        <div className="fear-greed-value" style={{ color: fearGreed.color }}>
                                            {fearGreed.value}
                                        </div>
                                        <div className="fear-greed-label" style={{ color: fearGreed.color }}>
                                            {fearGreed.label}
                                        </div>
                                        <div className="fear-greed-description">
                                            {fearGreed.value >= 60
                                                ? 'Market showing signs of optimism'
                                                : fearGreed.value >= 40
                                                  ? 'Market in balanced state'
                                                  : 'Market showing caution'}
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Opportunities */}
                            <div className="dashboard-card">
                                <div className="card-header">
                                    <h3>🎯 Trading Opportunities</h3>
                                    <span className="card-badge">{opportunities.length}</span>
                                </div>
                                <div className="opportunities-list">
                                    {opportunities.length === 0 ? (
                                        <div className="empty-state-small">No opportunities identified</div>
                                    ) : (
                                        opportunities.map((event) => (
                                            <div key={event.id} className="opportunity-item" onClick={() => setSelectedEvent(event)}>
                                                <div className="opportunity-header">
                                                    <span className="opportunity-phase" style={{ color: getPhaseColor(event.phase) }}>
                                                        D-{event.days_away}
                                                    </span>
                                                    <span className="opportunity-impact">{event.impact_score.toFixed(1)}</span>
                                                </div>
                                                <div className="opportunity-title">{event.title}</div>
                                                <div className="opportunity-recommendation">
                                                    💡 {event.recommendation || 'Monitor closely'}
                                                </div>
                                            </div>
                                        ))
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Center Column */}
                        <div className="grid-column center">
                            {/* Upcoming Events Timeline */}
                            <div className="dashboard-card full-height">
                                <div className="card-header">
                                    <h3>📊 Event Timeline</h3>
                                    <span className="card-badge">{filteredEvents.length}</span>
                                </div>
                                <div className="timeline-container">
                                    {filteredEvents.slice(0, 15).map((event) => (
                                        <div
                                            key={event.id}
                                            className="timeline-event"
                                            onClick={() => setSelectedEvent(event)}
                                            style={{ borderLeftColor: getPhaseColor(event.phase) }}
                                        >
                                            <div className="timeline-event-header">
                                                <div className="timeline-countdown">D-{event.days_away}</div>
                                                <div className="timeline-impact">
                                                    <div className="impact-dots">
                                                        {[...Array(10)].map((_, i) => (
                                                            <span
                                                                key={i}
                                                                className={i < event.impact_score ? 'active' : ''}
                                                                style={{
                                                                    background:
                                                                        i < event.impact_score
                                                                            ? event.impact_score >= 8
                                                                                ? '#ff3b30'
                                                                                : event.impact_score >= 6
                                                                                  ? '#ff9500'
                                                                                  : '#00d9ff'
                                                                            : 'rgba(255,255,255,0.1)',
                                                                }}
                                                            />
                                                        ))}
                                                    </div>
                                                </div>
                                            </div>
                                            <div className="timeline-event-title">{event.title}</div>
                                            <div className="timeline-event-meta">
                                                <span className="timeline-category">{event.event_type}</span>
                                                <span className="timeline-date">
                                                    {new Date(event.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                                                </span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* Right Column */}
                        <div className="grid-column right">
                            {/* Event Details or News */}
                            {selectedEvent ? (
                                <div className="dashboard-card">
                                    <div className="card-header">
                                        <h3>Event Details</h3>
                                        <button className="close-btn" onClick={() => setSelectedEvent(null)}>
                                            ×
                                        </button>
                                    </div>
                                    <div className="event-details-panel">
                                        <div className="detail-title">{selectedEvent.title}</div>
                                        <div className="detail-grid">
                                            <div className="detail-row">
                                                <span className="detail-label">Countdown</span>
                                                <span className="detail-value highlight">D-{selectedEvent.days_away}</span>
                                            </div>
                                            <div className="detail-row">
                                                <span className="detail-label">Impact</span>
                                                <span className="detail-value">{selectedEvent.impact_score.toFixed(1)}/10</span>
                                            </div>
                                            <div className="detail-row">
                                                <span className="detail-label">Phase</span>
                                                <span className="detail-value" style={{ color: getPhaseColor(selectedEvent.phase) }}>
                                                    {selectedEvent.phase}
                                                </span>
                                            </div>
                                            <div className="detail-row">
                                                <span className="detail-label">Category</span>
                                                <span className="detail-value">{selectedEvent.event_type}</span>
                                            </div>
                                            <div className="detail-row">
                                                <span className="detail-label">Date</span>
                                                <span className="detail-value">
                                                    {new Date(selectedEvent.date).toLocaleDateString('en-US', {
                                                        month: 'long',
                                                        day: 'numeric',
                                                        year: 'numeric',
                                                    })}
                                                </span>
                                            </div>
                                            {selectedEvent.affected_tickers && (
                                                <div className="detail-row full">
                                                    <span className="detail-label">Affected Tickers</span>
                                                    <span className="detail-value">{selectedEvent.affected_tickers}</span>
                                                </div>
                                            )}
                                        </div>
                                        {selectedEvent.recommendation && (
                                            <div className="detail-recommendation">
                                                <div className="recommendation-icon">💡</div>
                                                <div className="recommendation-text">{selectedEvent.recommendation}</div>
                                            </div>
                                        )}
                                        {selectedEvent.description && (
                                            <div className="detail-description">
                                                <div className="detail-label">Description</div>
                                                <p>{selectedEvent.description}</p>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ) : (
                                <div className="dashboard-card">
                                    <div className="card-header">
                                        <h3>📰 Live News</h3>
                                        <span className="live-indicator">
                                            <span className="pulse-dot"></span>
                                            LIVE
                                        </span>
                                    </div>
                                    <div className="news-stream">
                                        {news.slice(0, 10).map((item) => (
                                            <div key={item.id} className="news-stream-item">
                                                <div className="news-stream-header">
                                                    <span className="news-source">{item.source}</span>
                                                    <span className="news-time">{formatTimeAgo(item.published_at)}</span>
                                                </div>
                                                <div className="news-stream-title">{item.title}</div>
                                                <div className="news-stream-sentiment">
                                                    <span
                                                        className="sentiment-indicator"
                                                        style={{
                                                            background:
                                                                item.sentiment === 'bullish'
                                                                    ? '#00c853'
                                                                    : item.sentiment === 'bearish'
                                                                      ? '#ff1744'
                                                                      : '#9e9e9e',
                                                        }}
                                                    >
                                                        {item.sentiment}
                                                    </span>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Calendar View */}
            {activeTab === 'calendar' && (
                <div className="calendar-view">
                    <div className="calendar-header">
                        <h2>Monthly Event Calendar</h2>
                    </div>
                    <div className="calendar-month">
                        {[...Array(30)].map((_, i) => {
                            const day = new Date();
                            day.setDate(day.getDate() + i);
                            const dayEvents = events.filter((e) => {
                                const eventDate = new Date(e.date).toDateString();
                                return eventDate === day.toDateString();
                            });

                            return (
                                <div key={i} className={`calendar-day-card ${i === 0 ? 'today' : ''}`}>
                                    <div className="calendar-day-header">
                                        <div className="day-number">{day.getDate()}</div>
                                        <div className="day-name">{day.toLocaleDateString('en-US', { weekday: 'short' })}</div>
                                    </div>
                                    <div className="calendar-day-events">
                                        {dayEvents.map((event) => (
                                            <div
                                                key={event.id}
                                                className="calendar-event-mini"
                                                onClick={() => setSelectedEvent(event)}
                                                style={{ borderLeftColor: getPhaseColor(event.phase) }}
                                            >
                                                <div className="event-mini-title">{event.title}</div>
                                                <div className="event-mini-impact">{event.impact_score.toFixed(1)}</div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* Earnings View */}
            {activeTab === 'earnings' && (
                <div className="earnings-view">
                    <div className="earnings-header">
                        <h2>💰 Earnings Calendar</h2>
                        <span className="earnings-count">{earningsEvents.length} upcoming</span>
                    </div>
                    <div className="earnings-grid">
                        {earningsEvents.map((event) => (
                            <div key={event.id} className="earnings-card" onClick={() => setSelectedEvent(event)}>
                                <div className="earnings-card-header">
                                    <div className="earnings-ticker">{event.affected_tickers?.split(',')[0]}</div>
                                    <div className="earnings-countdown">D-{event.days_away}</div>
                                </div>
                                <div className="earnings-card-title">{event.title}</div>
                                <div className="earnings-card-meta">
                                    <span className="earnings-date">
                                        {new Date(event.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                                    </span>
                                    <span className="earnings-impact">Impact: {event.impact_score.toFixed(1)}</span>
                                </div>
                                {event.recommendation && <div className="earnings-recommendation">💡 {event.recommendation}</div>}
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Analysis View */}
            {activeTab === 'analysis' && (
                <div className="analysis-view">
                    <h2>🔍 Market Analysis</h2>
                    <div className="analysis-grid">
                        <div className="analysis-card">
                            <h3>Phase Distribution</h3>
                            <div className="phase-chart">
                                <div className="phase-bar danger" style={{ width: `${(dangerEvents.length / events.length) * 100}%` }}>
                                    <span>{dangerEvents.length}</span>
                                </div>
                                <div className="phase-bar euforia" style={{ width: `${(euforiaEvents.length / events.length) * 100}%` }}>
                                    <span>{euforiaEvents.length}</span>
                                </div>
                                <div
                                    className="phase-bar accumulation"
                                    style={{ width: `${(accumulationEvents.length / events.length) * 100}%` }}
                                >
                                    <span>{accumulationEvents.length}</span>
                                </div>
                                <div className="phase-bar neutral" style={{ width: `${(preRumorEvents.length / events.length) * 100}%` }}>
                                    <span>{preRumorEvents.length}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Footer */}
            <footer className="product-footer">
                <div className="footer-status">
                    <span className="status-dot connected"></span>
                    <span>Connected</span>
                </div>
                <div className="footer-info">Aeon Nimbus Intelligence v2.0</div>
            </footer>
        </div>
    );
};
