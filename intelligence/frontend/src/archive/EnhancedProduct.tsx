import React, { useState, useEffect, useMemo, useCallback } from 'react';
import './EnhancedProduct.css';

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

interface FilterState {
    phases: Set<string>;
    impactRange: [number, number];
    daysRange: [number, number];
    eventTypes: Set<string>;
    tickers: string[];
}

interface Alert {
    id: string;
    type: 'critical' | 'warning' | 'info';
    title: string;
    message: string;
    eventId?: number;
    timestamp: Date;
    dismissed: boolean;
}

export const EnhancedProduct: React.FC = () => {
    const [events, setEvents] = useState<Event[]>([]);
    const [news, setNews] = useState<NewsItem[]>([]);
    const [activeTab, setActiveTab] = useState<'dashboard' | 'calendar' | 'earnings' | 'analysis'>('dashboard');
    const [selectedEvent, setSelectedEvent] = useState<Event | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
    const [watchlist, setWatchlist] = useState<Set<string>>(new Set(['AAPL', 'MSFT', 'GOOGL']));
    const [favorites, setFavorites] = useState<Set<number>>(new Set());
    const [alerts, setAlerts] = useState<Alert[]>([]);
    const [showAlerts, setShowAlerts] = useState(false);
    const [showFilters, setShowFilters] = useState(false);
    const [filters, setFilters] = useState<FilterState>({
        phases: new Set(['DANGER', 'EUFORIA', 'ACCUMULATION', 'PRE-RUMOR']),
        impactRange: [0, 10],
        daysRange: [0, 100],
        eventTypes: new Set(),
        tickers: [],
    });
    const [fearGreed, setFearGreed] = useState({ value: 52, label: 'Neutral', color: '#9e9e9e' });
    const [loadingStates, setLoadingStates] = useState({
        events: true,
        news: true,
    });

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 10000);
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
    }, []);

    useEffect(() => {
        checkForAlerts(events);
    }, [events]);

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
            setLoadingStates({ events: false, news: false });

            calculateFearGreed(eventsData, newsData.news || []);
        } catch (error) {
            console.error('Error fetching data:', error);
            setLoadingStates({ events: false, news: false });
        }
    };

    const checkForAlerts = (events: Event[]) => {
        const criticalEvents = events.filter((e) => e.days_away <= 2 && e.impact_score >= 7);
        const watchlistEvents = events.filter((e) => {
            const tickers = e.affected_tickers?.split(',').map((t) => t.trim()) || [];
            return tickers.some((t) => watchlist.has(t)) && e.days_away <= 5;
        });

        const newAlerts: Alert[] = [];

        criticalEvents.forEach((event) => {
            if (!alerts.some((a) => a.eventId === event.id && a.type === 'critical')) {
                const alert: Alert = {
                    id: `critical-${event.id}-${Date.now()}`,
                    type: 'critical',
                    title: `Critical Event Alert`,
                    message: `${event.title} - D-${event.days_away}`,
                    eventId: event.id,
                    timestamp: new Date(),
                    dismissed: false,
                };
                newAlerts.push(alert);

                if (Notification.permission === 'granted') {
                    new Notification(alert.title, { body: alert.message });
                }
            }
        });

        watchlistEvents.forEach((event) => {
            if (!alerts.some((a) => a.eventId === event.id && a.type === 'warning')) {
                newAlerts.push({
                    id: `watchlist-${event.id}-${Date.now()}`,
                    type: 'warning',
                    title: `Watchlist Alert`,
                    message: `${event.title} affecting ${event.affected_tickers}`,
                    eventId: event.id,
                    timestamp: new Date(),
                    dismissed: false,
                });
            }
        });

        if (newAlerts.length > 0) {
            setAlerts((prev) => [...newAlerts, ...prev].slice(0, 50));
        }
    };

    const calculateFearGreed = (events: Event[], news: NewsItem[]) => {
        const bullishNews = news.filter((n) => n.sentiment === 'bullish').length;
        const bearishNews = news.filter((n) => n.sentiment === 'bearish').length;
        const highImpactEvents = events.filter((e) => e.impact_score >= 8 && e.days_away <= 7).length;

        let score = 50;
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

    const allTickers = useMemo(() => {
        const tickerSet = new Set<string>();
        events.forEach((e) => {
            if (e.affected_tickers) {
                e.affected_tickers.split(',').forEach((t) => tickerSet.add(t.trim()));
            }
        });
        return Array.from(tickerSet).sort();
    }, [events]);

    const allEventTypes = useMemo(() => {
        return Array.from(new Set(events.map((e) => e.event_type))).sort();
    }, [events]);

    const filteredEvents = useMemo(() => {
        return events.filter((e) => {
            if (
                searchQuery &&
                !e.title.toLowerCase().includes(searchQuery.toLowerCase()) &&
                !e.affected_tickers?.toLowerCase().includes(searchQuery.toLowerCase())
            ) {
                return false;
            }

            if (!filters.phases.has(e.phase.split(' ')[0])) return false;
            if (e.impact_score < filters.impactRange[0] || e.impact_score > filters.impactRange[1]) return false;
            if (e.days_away < filters.daysRange[0] || e.days_away > filters.daysRange[1]) return false;

            if (filters.eventTypes.size > 0 && !filters.eventTypes.has(e.event_type)) return false;

            if (filters.tickers.length > 0) {
                const eventTickers = e.affected_tickers?.split(',').map((t) => t.trim()) || [];
                if (!eventTickers.some((t) => filters.tickers.includes(t))) return false;
            }

            if (selectedTicker) {
                const eventTickers = e.affected_tickers?.split(',').map((t) => t.trim()) || [];
                if (!eventTickers.includes(selectedTicker)) return false;
            }

            return true;
        });
    }, [events, searchQuery, filters, selectedTicker]);

    const toggleFavorite = (eventId: number) => {
        setFavorites((prev) => {
            const next = new Set(prev);
            if (next.has(eventId)) {
                next.delete(eventId);
            } else {
                next.add(eventId);
            }
            return next;
        });
    };

    const toggleWatchlist = (ticker: string) => {
        setWatchlist((prev) => {
            const next = new Set(prev);
            if (next.has(ticker)) {
                next.delete(ticker);
            } else {
                next.add(ticker);
            }
            return next;
        });
    };

    const dismissAlert = (alertId: string) => {
        setAlerts((prev) => prev.map((a) => (a.id === alertId ? { ...a, dismissed: true } : a)));
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

    const dangerEvents = filteredEvents.filter((e) => e.phase.includes('DANGER'));
    const euforiaEvents = filteredEvents.filter((e) => e.phase.includes('EUFORIA'));
    const accumulationEvents = filteredEvents.filter((e) => e.phase.includes('ACCUMULATION'));
    const preRumorEvents = filteredEvents.filter((e) => e.phase.includes('PRE-RUMOR'));

    const earningsEvents = filteredEvents.filter((e) => e.event_type === 'earnings').slice(0, 12);

    const opportunities = filteredEvents.filter((e) => e.impact_score >= 7 && e.days_away >= 10 && e.days_away <= 20).slice(0, 6);

    const activeAlerts = alerts.filter((a) => !a.dismissed);

    return (
        <div className="enhanced-product">
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

                <div className="header-actions">
                    <button className="action-btn" onClick={() => setShowFilters(!showFilters)} title="Filters">
                        <span className="filter-icon">⚙️</span>
                        {(filters.eventTypes.size > 0 ||
                            filters.tickers.length > 0 ||
                            filters.phases.size < 4 ||
                            filters.impactRange[0] > 0 ||
                            filters.impactRange[1] < 10) && <span className="active-badge"></span>}
                    </button>
                    <button className="action-btn alert-btn" onClick={() => setShowAlerts(!showAlerts)} title="Alerts">
                        <span className="alert-icon">🔔</span>
                        {activeAlerts.length > 0 && <span className="alert-count">{activeAlerts.length}</span>}
                    </button>
                    <div className="header-search">
                        <input
                            type="text"
                            placeholder="Search events or tickers..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                    </div>
                </div>
            </header>

            {/* Alerts Panel */}
            {showAlerts && (
                <div className="alerts-panel">
                    <div className="alerts-header">
                        <h3>Alerts</h3>
                        <button onClick={() => setShowAlerts(false)}>×</button>
                    </div>
                    <div className="alerts-list">
                        {activeAlerts.length === 0 ? (
                            <div className="empty-state-small">No active alerts</div>
                        ) : (
                            activeAlerts.map((alert) => (
                                <div key={alert.id} className={`alert-item alert-${alert.type}`}>
                                    <div className="alert-content">
                                        <div className="alert-title">{alert.title}</div>
                                        <div className="alert-message">{alert.message}</div>
                                        <div className="alert-time">{formatTimeAgo(alert.timestamp.toISOString())}</div>
                                    </div>
                                    <button className="alert-dismiss" onClick={() => dismissAlert(alert.id)}>
                                        ×
                                    </button>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            )}

            {/* Filters Panel */}
            {showFilters && (
                <div className="filters-panel">
                    <div className="filters-header">
                        <h3>Filters</h3>
                        <button onClick={() => setShowFilters(false)}>×</button>
                    </div>
                    <div className="filters-content">
                        <div className="filter-section">
                            <label>Phases</label>
                            <div className="filter-checkboxes">
                                {['DANGER', 'EUFORIA', 'ACCUMULATION', 'PRE-RUMOR'].map((phase) => (
                                    <label key={phase} className="filter-checkbox">
                                        <input
                                            type="checkbox"
                                            checked={filters.phases.has(phase)}
                                            onChange={(e) => {
                                                const next = new Set(filters.phases);
                                                if (e.target.checked) next.add(phase);
                                                else next.delete(phase);
                                                setFilters({ ...filters, phases: next });
                                            }}
                                        />
                                        <span>{phase}</span>
                                    </label>
                                ))}
                            </div>
                        </div>

                        <div className="filter-section">
                            <label>
                                Impact Score: {filters.impactRange[0].toFixed(1)} - {filters.impactRange[1].toFixed(1)}
                            </label>
                            <div className="filter-range-inputs">
                                <input
                                    type="range"
                                    min="0"
                                    max="10"
                                    step="0.5"
                                    value={filters.impactRange[0]}
                                    onChange={(e) =>
                                        setFilters({ ...filters, impactRange: [parseFloat(e.target.value), filters.impactRange[1]] })
                                    }
                                />
                                <input
                                    type="range"
                                    min="0"
                                    max="10"
                                    step="0.5"
                                    value={filters.impactRange[1]}
                                    onChange={(e) =>
                                        setFilters({ ...filters, impactRange: [filters.impactRange[0], parseFloat(e.target.value)] })
                                    }
                                />
                            </div>
                        </div>

                        <div className="filter-section">
                            <label>
                                Days Away: {filters.daysRange[0]} - {filters.daysRange[1]}
                            </label>
                            <div className="filter-range-inputs">
                                <input
                                    type="range"
                                    min="0"
                                    max="100"
                                    step="1"
                                    value={filters.daysRange[0]}
                                    onChange={(e) =>
                                        setFilters({ ...filters, daysRange: [parseInt(e.target.value), filters.daysRange[1]] })
                                    }
                                />
                                <input
                                    type="range"
                                    min="0"
                                    max="100"
                                    step="1"
                                    value={filters.daysRange[1]}
                                    onChange={(e) =>
                                        setFilters({ ...filters, daysRange: [filters.daysRange[0], parseInt(e.target.value)] })
                                    }
                                />
                            </div>
                        </div>

                        <div className="filter-section">
                            <label>Event Types</label>
                            <div className="filter-checkboxes">
                                {allEventTypes.map((type) => (
                                    <label key={type} className="filter-checkbox">
                                        <input
                                            type="checkbox"
                                            checked={filters.eventTypes.has(type)}
                                            onChange={(e) => {
                                                const next = new Set(filters.eventTypes);
                                                if (e.target.checked) next.add(type);
                                                else next.delete(type);
                                                setFilters({ ...filters, eventTypes: next });
                                            }}
                                        />
                                        <span>{type}</span>
                                    </label>
                                ))}
                            </div>
                        </div>

                        <button
                            className="filter-reset"
                            onClick={() =>
                                setFilters({
                                    phases: new Set(['DANGER', 'EUFORIA', 'ACCUMULATION', 'PRE-RUMOR']),
                                    impactRange: [0, 10],
                                    daysRange: [0, 100],
                                    eventTypes: new Set(),
                                    tickers: [],
                                })
                            }
                        >
                            Reset All Filters
                        </button>
                    </div>
                </div>
            )}

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

                    {/* Watchlist Bar */}
                    <div className="watchlist-bar">
                        <div className="watchlist-label">Watchlist</div>
                        <div className="watchlist-tickers">
                            {Array.from(watchlist).map((ticker) => {
                                const tickerEvents = filteredEvents.filter((e) =>
                                    e.affected_tickers
                                        ?.split(',')
                                        .map((t) => t.trim())
                                        .includes(ticker),
                                );
                                return (
                                    <button
                                        key={ticker}
                                        className={`watchlist-ticker ${selectedTicker === ticker ? 'active' : ''}`}
                                        onClick={() => setSelectedTicker(selectedTicker === ticker ? null : ticker)}
                                    >
                                        <span className="ticker-symbol">{ticker}</span>
                                        <span className="ticker-count">{tickerEvents.length}</span>
                                        <button
                                            className="ticker-remove"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                toggleWatchlist(ticker);
                                            }}
                                        >
                                            ×
                                        </button>
                                    </button>
                                );
                            })}
                            <select
                                className="watchlist-add"
                                onChange={(e) => {
                                    if (e.target.value) {
                                        toggleWatchlist(e.target.value);
                                        e.target.value = '';
                                    }
                                }}
                                value=""
                            >
                                <option value="">+ Add Ticker</option>
                                {allTickers
                                    .filter((t) => !watchlist.has(t))
                                    .map((t) => (
                                        <option key={t} value={t}>
                                            {t}
                                        </option>
                                    ))}
                            </select>
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
                                    <h3>Trading Opportunities</h3>
                                    <span className="card-badge">{opportunities.length}</span>
                                </div>
                                <div className="opportunities-list">
                                    {loadingStates.events ? (
                                        <div className="loading-skeleton">
                                            {[...Array(3)].map((_, i) => (
                                                <div key={i} className="skeleton-item"></div>
                                            ))}
                                        </div>
                                    ) : opportunities.length === 0 ? (
                                        <div className="empty-state-small">No opportunities identified</div>
                                    ) : (
                                        opportunities.map((event) => (
                                            <div key={event.id} className="opportunity-item" onClick={() => setSelectedEvent(event)}>
                                                <div className="opportunity-header">
                                                    <span className="opportunity-phase" style={{ color: getPhaseColor(event.phase) }}>
                                                        D-{event.days_away}
                                                    </span>
                                                    <div className="opportunity-actions">
                                                        <span className="opportunity-impact">{event.impact_score.toFixed(1)}</span>
                                                        <button
                                                            className={`favorite-btn ${favorites.has(event.id) ? 'active' : ''}`}
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                toggleFavorite(event.id);
                                                            }}
                                                        >
                                                            ★
                                                        </button>
                                                    </div>
                                                </div>
                                                <div className="opportunity-title">{event.title}</div>
                                                {event.affected_tickers && (
                                                    <div className="opportunity-tickers">
                                                        {event.affected_tickers
                                                            .split(',')
                                                            .map((t) => t.trim())
                                                            .slice(0, 3)
                                                            .map((t) => (
                                                                <span
                                                                    key={t}
                                                                    className="ticker-chip"
                                                                    onClick={(e) => {
                                                                        e.stopPropagation();
                                                                        setSelectedTicker(t);
                                                                    }}
                                                                >
                                                                    {t}
                                                                </span>
                                                            ))}
                                                    </div>
                                                )}
                                                <div className="opportunity-recommendation">
                                                    💡 {event.recommendation || 'Monitor closely for entry signal'}
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
                                    <h3>Event Timeline</h3>
                                    <span className="card-badge">{filteredEvents.length}</span>
                                </div>
                                <div className="timeline-container">
                                    {loadingStates.events ? (
                                        <div className="loading-skeleton">
                                            {[...Array(8)].map((_, i) => (
                                                <div key={i} className="skeleton-item"></div>
                                            ))}
                                        </div>
                                    ) : (
                                        filteredEvents.slice(0, 20).map((event) => (
                                            <div
                                                key={event.id}
                                                className="timeline-event"
                                                onClick={() => setSelectedEvent(event)}
                                                style={{ borderLeftColor: getPhaseColor(event.phase) }}
                                            >
                                                <div className="timeline-event-header">
                                                    <div className="timeline-countdown">D-{event.days_away}</div>
                                                    <div className="timeline-actions">
                                                        <div className="timeline-impact">
                                                            <div className="impact-dots">
                                                                {[...Array(10)].map((_, i) => (
                                                                    <span
                                                                        key={i}
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
                                                        <button
                                                            className={`favorite-btn ${favorites.has(event.id) ? 'active' : ''}`}
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                toggleFavorite(event.id);
                                                            }}
                                                        >
                                                            ★
                                                        </button>
                                                    </div>
                                                </div>
                                                <div className="timeline-event-title">{event.title}</div>
                                                {event.affected_tickers && (
                                                    <div className="timeline-tickers">
                                                        {event.affected_tickers
                                                            .split(',')
                                                            .map((t) => t.trim())
                                                            .slice(0, 5)
                                                            .map((t) => (
                                                                <span
                                                                    key={t}
                                                                    className="ticker-chip-mini"
                                                                    onClick={(e) => {
                                                                        e.stopPropagation();
                                                                        setSelectedTicker(t);
                                                                    }}
                                                                >
                                                                    {t}
                                                                </span>
                                                            ))}
                                                    </div>
                                                )}
                                                <div className="timeline-event-meta">
                                                    <span className="timeline-category">{event.event_type}</span>
                                                    <span className="timeline-date">
                                                        {new Date(event.date).toLocaleDateString('en-US', {
                                                            month: 'short',
                                                            day: 'numeric',
                                                        })}
                                                    </span>
                                                </div>
                                            </div>
                                        ))
                                    )}
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
                                        <div className="card-header-actions">
                                            <button
                                                className={`favorite-btn ${favorites.has(selectedEvent.id) ? 'active' : ''}`}
                                                onClick={() => toggleFavorite(selectedEvent.id)}
                                            >
                                                ★
                                            </button>
                                            <button className="close-btn" onClick={() => setSelectedEvent(null)}>
                                                ×
                                            </button>
                                        </div>
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
                                                    <div className="detail-tickers">
                                                        {selectedEvent.affected_tickers
                                                            .split(',')
                                                            .map((t) => t.trim())
                                                            .map((t) => (
                                                                <span
                                                                    key={t}
                                                                    className={`ticker-chip ${watchlist.has(t) ? 'in-watchlist' : ''}`}
                                                                    onClick={() => toggleWatchlist(t)}
                                                                >
                                                                    {t}
                                                                    {!watchlist.has(t) && <span className="add-icon">+</span>}
                                                                </span>
                                                            ))}
                                                    </div>
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
                                        <h3>Live News</h3>
                                        <span className="live-indicator">
                                            <span className="pulse-dot"></span>
                                            LIVE
                                        </span>
                                    </div>
                                    <div className="news-stream">
                                        {loadingStates.news ? (
                                            <div className="loading-skeleton">
                                                {[...Array(5)].map((_, i) => (
                                                    <div key={i} className="skeleton-item"></div>
                                                ))}
                                            </div>
                                        ) : (
                                            news.slice(0, 12).map((item) => (
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
                                            ))
                                        )}
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
                            const dayEvents = filteredEvents.filter((e) => {
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
                        <h2>Earnings Calendar</h2>
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
                    <h2>Market Analysis</h2>
                    <div className="analysis-grid">
                        <div className="analysis-card">
                            <h3>Phase Distribution</h3>
                            <div className="phase-chart">
                                <div
                                    className="phase-bar danger"
                                    style={{ width: `${(dangerEvents.length / filteredEvents.length) * 100 || 0}%` }}
                                >
                                    DANGER: {dangerEvents.length}
                                </div>
                                <div
                                    className="phase-bar euforia"
                                    style={{ width: `${(euforiaEvents.length / filteredEvents.length) * 100 || 0}%` }}
                                >
                                    EUFORIA: {euforiaEvents.length}
                                </div>
                                <div
                                    className="phase-bar accumulation"
                                    style={{ width: `${(accumulationEvents.length / filteredEvents.length) * 100 || 0}%` }}
                                >
                                    ACCUMULATION: {accumulationEvents.length}
                                </div>
                                <div
                                    className="phase-bar neutral"
                                    style={{ width: `${(preRumorEvents.length / filteredEvents.length) * 100 || 0}%` }}
                                >
                                    PRE-RUMOR: {preRumorEvents.length}
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
                    <span>
                        Connected • {filteredEvents.length} events • {news.length} news items
                    </span>
                </div>
                <div className="footer-info">Aeon Nimbus Intelligence v2.1 • Enhanced Edition</div>
            </footer>
        </div>
    );
};
