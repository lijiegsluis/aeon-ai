import React, { useState, useEffect, useMemo } from 'react';
import './ProfessionalProduct.css';
import './NewsTab.css';

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
    timestamp: string;
    affected_tickers: string;
    sentiment: string;
}

interface NewsAnalysis {
    impact: 'high' | 'medium' | 'low';
    probability: number;
    timeframe: string;
    direction: 'bullish' | 'bearish' | 'neutral';
    explanation: string;
    affectedSectors: string[];
}

export const ProfessionalProduct: React.FC = () => {
    const [events, setEvents] = useState<Event[]>([]);
    const [news, setNews] = useState<NewsItem[]>([]);
    const [activeTab, setActiveTab] = useState<'dashboard' | 'news' | 'calendar' | 'earnings' | 'analysis'>('dashboard');
    const [newsFilters, setNewsFilters] = useState({
        sources: new Set<string>(),
        sentiments: new Set<string>(['positive', 'negative', 'neutral']),
        timeRange: '24h' as '1h' | '24h' | '7d' | 'all',
    });
    const [selectedEvent, setSelectedEvent] = useState<Event | null>(null);
    const [selectedNews, setSelectedNews] = useState<NewsItem | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
    const [watchlist, setWatchlist] = useState<Set<string>>(new Set(['AAPL', 'MSFT', 'GOOGL', 'NVDA']));
    const [favorites, setFavorites] = useState<Set<number>>(new Set());
    const [alerts, setAlerts] = useState<any[]>([]);
    const [showAlerts, setShowAlerts] = useState(false);
    const [showFilters, setShowFilters] = useState(false);
    const [filters, setFilters] = useState<any>({
        phases: new Set(['DANGER', 'EUFORIA', 'ACCUMULATION', 'PRE-RUMOR']),
        impactRange: [0, 10],
        daysRange: [0, 100],
        eventTypes: new Set(),
        tickers: [],
    });
    const [fearGreed, setFearGreed] = useState({ value: 52, label: 'Neutral', color: '#9e9e9e' });
    const [loadingStates, setLoadingStates] = useState({ events: true, news: true });

    useEffect(() => {
        fetchData();
        const interval = setInterval(fetchData, 10000);
        return () => clearInterval(interval);
    }, []);

    const fetchData = async () => {
        try {
            const [eventsRes, newsRes] = await Promise.all([
                fetch('http://localhost:8001/api/events/live?timeframe=90days'),
                fetch('http://localhost:8001/api/news/feed?limit=100'),
            ]);

            const eventsJson = await eventsRes.json();
            const newsJson = await newsRes.json();

            // Backend returns { events: [...] } with affected_tickers as an array
            // and lowercase phase names ("danger"/"euforia"/.../"live") and
            // days_until (not days_away) — normalize to what this UI expects.
            const mappedEvents: Event[] = (eventsJson.events || []).map((e: any) => ({
                ...e,
                affected_tickers: Array.isArray(e.affected_tickers) ? e.affected_tickers.join(',') : e.affected_tickers,
                days_away: e.days_until,
                phase: e.phase === 'live' ? 'DANGER' : String(e.phase).toUpperCase(),
            }));
            const newsList: NewsItem[] = newsJson.feed || [];

            setEvents(mappedEvents);
            setNews(newsList);
            setLoadingStates({ events: false, news: false });

            calculateFearGreed(mappedEvents, newsList);
        } catch (error) {
            console.error('Error fetching data:', error);
            setLoadingStates({ events: false, news: false });
        }
    };

    const analyzeNews = (newsItem: NewsItem): NewsAnalysis => {
        const tickerCount = newsItem.affected_tickers?.split(',').length || 0;
        const isMajorIndex = newsItem.affected_tickers?.includes('SPY') || newsItem.affected_tickers?.includes('QQQ');

        let impact: 'high' | 'medium' | 'low' = 'low';
        let probability = 0;
        let timeframe = '';
        let explanation = '';
        let affectedSectors: string[] = [];

        if (newsItem.sentiment === 'positive') {
            if (isMajorIndex) {
                impact = 'high';
                probability = 75;
                timeframe = '1-3 days';
                explanation =
                    'Major index catalysts typically drive broad market momentum. Expected continuation in near-term trading sessions with increased volume.';
                affectedSectors = ['Technology', 'Financial Services', 'Consumer Discretionary'];
            } else if (tickerCount > 2) {
                impact = 'medium';
                probability = 65;
                timeframe = '2-5 days';
                explanation = 'Multi-stock positive catalyst suggests sector-wide strength. Watch for follow-through in related names.';
                affectedSectors = ['Related Sector Stocks'];
            } else {
                impact = 'low';
                probability = 55;
                timeframe = '1-2 days';
                explanation = 'Single-stock news may drive short-term volatility. Impact likely contained unless guidance changes.';
                affectedSectors = ['Individual Stock'];
            }
        } else if (newsItem.sentiment === 'negative') {
            if (isMajorIndex) {
                impact = 'high';
                probability = 80;
                timeframe = 'Immediate';
                explanation =
                    'Major index weakness typically cascades across correlated assets. Defensive positioning recommended in short term.';
                affectedSectors = ['Broad Market', 'High Beta Stocks', 'Growth Names'];
            } else if (tickerCount > 2) {
                impact = 'medium';
                probability = 70;
                timeframe = '1-3 days';
                explanation = 'Multi-stock bearish signal indicates sector headwinds. Risk-off sentiment may persist through sector.';
                affectedSectors = ['Sector Peers', 'Supply Chain'];
            } else {
                impact = 'low';
                probability = 60;
                timeframe = '1 day';
                explanation = 'Isolated negative news. Limited contagion expected unless systemic issues emerge.';
                affectedSectors = ['Individual Stock'];
            }
        } else {
            impact = 'low';
            probability = 50;
            timeframe = '1-2 days';
            explanation =
                'Neutral sentiment suggests information already priced in. Monitor for directional clarity in subsequent reports.';
            affectedSectors = ['Mixed'];
        }

        return {
            impact,
            probability,
            timeframe,
            direction: newsItem.sentiment === 'positive' ? 'bullish' : newsItem.sentiment === 'negative' ? 'bearish' : 'neutral',
            explanation,
            affectedSectors,
        };
    };

    const calculateFearGreed = (events: Event[], news: NewsItem[]) => {
        const bullishNews = news.filter((n) => n.sentiment === 'positive').length;
        const bearishNews = news.filter((n) => n.sentiment === 'negative').length;
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
        if (diffMins < 60) return `${diffMins}m ago`;
        const diffHours = Math.floor(diffMins / 60);
        if (diffHours < 24) return `${diffHours}h ago`;
        return `${Math.floor(diffHours / 24)}d ago`;
    };

    const toggleFavorite = (eventId: number) => {
        setFavorites((prev) => {
            const next = new Set(prev);
            if (next.has(eventId)) next.delete(eventId);
            else next.add(eventId);
            return next;
        });
    };

    const toggleWatchlist = (ticker: string) => {
        setWatchlist((prev) => {
            const next = new Set(prev);
            if (next.has(ticker)) next.delete(ticker);
            else next.add(ticker);
            return next;
        });
    };

    const allTickers = useMemo(() => {
        const tickerSet = new Set<string>();
        events.forEach((e) => {
            if (e.affected_tickers) {
                e.affected_tickers.split(',').forEach((t) => tickerSet.add(t.trim()));
            }
        });
        news.forEach((n) => {
            if (n.affected_tickers) {
                n.affected_tickers.split(',').forEach((t) => tickerSet.add(t.trim()));
            }
        });
        return Array.from(tickerSet).sort();
    }, [events, news]);

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
            if (selectedTicker) {
                const eventTickers = e.affected_tickers?.split(',').map((t) => t.trim()) || [];
                if (!eventTickers.includes(selectedTicker)) return false;
            }
            return true;
        });
    }, [events, searchQuery, filters, selectedTicker]);

    const filteredNews = useMemo(() => {
        let filtered = news;

        // Search filter
        if (searchQuery) {
            filtered = filtered.filter(
                (n) =>
                    n.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                    n.content?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                    n.affected_tickers?.toLowerCase().includes(searchQuery.toLowerCase()),
            );
        }

        // Ticker filter
        if (selectedTicker) {
            filtered = filtered.filter((n) => {
                const newsTickers = n.affected_tickers?.split(',').map((t) => t.trim()) || [];
                return newsTickers.includes(selectedTicker);
            });
        }

        // Source filter (for News tab)
        if (newsFilters.sources.size > 0) {
            filtered = filtered.filter((n) => newsFilters.sources.has(n.source));
        }

        // Sentiment filter (for News tab)
        if (newsFilters.sentiments.size > 0) {
            filtered = filtered.filter((n) => newsFilters.sentiments.has(n.sentiment));
        }

        // Time range filter (for News tab)
        if (newsFilters.timeRange !== 'all') {
            const now = new Date();
            const cutoff = new Date();
            if (newsFilters.timeRange === '1h') cutoff.setHours(now.getHours() - 1);
            else if (newsFilters.timeRange === '24h') cutoff.setHours(now.getHours() - 24);
            else if (newsFilters.timeRange === '7d') cutoff.setDate(now.getDate() - 7);

            filtered = filtered.filter((n) => new Date(n.timestamp) >= cutoff);
        }

        return filtered;
    }, [news, searchQuery, selectedTicker, newsFilters]);

    const allNewsSources = useMemo(() => {
        return Array.from(new Set(news.map((n) => n.source))).sort();
    }, [news]);

    const dangerEvents = filteredEvents.filter((e) => e.phase.includes('DANGER'));
    const euforiaEvents = filteredEvents.filter((e) => e.phase.includes('EUFORIA'));
    const accumulationEvents = filteredEvents.filter((e) => e.phase.includes('ACCUMULATION'));
    const preRumorEvents = filteredEvents.filter((e) => e.phase.includes('PRE-RUMOR'));
    const earningsEvents = filteredEvents.filter((e) => e.event_type === 'earnings').slice(0, 12);
    const opportunities = filteredEvents.filter((e) => e.impact_score >= 7 && e.days_away >= 10 && e.days_away <= 20).slice(0, 6);

    return (
        <div className="professional-product">
            <header className="product-header">
                <div className="header-brand">
                    <h1 className="brand-logo">AEON NIMBUS</h1>
                    <span className="brand-tagline">Professional Market Intelligence</span>
                </div>

                <nav className="main-nav">
                    <button className={activeTab === 'dashboard' ? 'active' : ''} onClick={() => setActiveTab('dashboard')}>
                        <span className="nav-icon">📊</span>
                        Dashboard
                    </button>
                    <button className={activeTab === 'news' ? 'active' : ''} onClick={() => setActiveTab('news')}>
                        <span className="nav-icon">📰</span>
                        News
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
                    <button className="action-btn" onClick={() => setShowFilters(!showFilters)}>
                        <span>⚙️</span>
                    </button>
                    <div className="header-search">
                        <input
                            type="text"
                            placeholder="Search events, news, tickers..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                    </div>
                </div>
            </header>

            {activeTab === 'dashboard' && (
                <div className="dashboard-layout">
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

                    <div className="dashboard-grid">
                        <div className="grid-column left">
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

                            <div className="dashboard-card">
                                <div className="card-header">
                                    <h3>Trading Opportunities</h3>
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
                                                    💡 {event.recommendation || 'Monitor for entry signal in accumulation phase'}
                                                </div>
                                            </div>
                                        ))
                                    )}
                                </div>
                            </div>
                        </div>

                        <div className="grid-column center">
                            <div className="dashboard-card full-height">
                                <div className="card-header">
                                    <h3>Event Timeline</h3>
                                    <span className="card-badge">{filteredEvents.length}</span>
                                </div>
                                <div className="timeline-container">
                                    {filteredEvents.slice(0, 20).map((event) => (
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
                                                    {new Date(event.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                                                </span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>

                        <div className="grid-column right">
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
                                        </div>
                                        {selectedEvent.recommendation && (
                                            <div className="detail-recommendation">
                                                <div className="recommendation-icon">💡</div>
                                                <div className="recommendation-text">{selectedEvent.recommendation}</div>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ) : selectedNews ? (
                                <div className="dashboard-card">
                                    <div className="card-header">
                                        <h3>News Analysis</h3>
                                        <button className="close-btn" onClick={() => setSelectedNews(null)}>
                                            ×
                                        </button>
                                    </div>
                                    <div className="news-analysis-panel">
                                        <div className="analysis-title">{selectedNews.title}</div>
                                        {(() => {
                                            const analysis = analyzeNews(selectedNews);
                                            return (
                                                <>
                                                    <div className="analysis-metrics">
                                                        <div className="analysis-metric">
                                                            <div className="metric-label-small">Impact Level</div>
                                                            <div className={`metric-badge ${analysis.impact}`}>
                                                                {analysis.impact.toUpperCase()}
                                                            </div>
                                                        </div>
                                                        <div className="analysis-metric">
                                                            <div className="metric-label-small">Probability</div>
                                                            <div className="metric-value-large">{analysis.probability}%</div>
                                                        </div>
                                                        <div className="analysis-metric">
                                                            <div className="metric-label-small">Timeframe</div>
                                                            <div className="metric-value-large">{analysis.timeframe}</div>
                                                        </div>
                                                    </div>

                                                    <div className="analysis-direction">
                                                        <div
                                                            className="direction-badge"
                                                            style={{
                                                                background:
                                                                    analysis.direction === 'bullish'
                                                                        ? 'rgba(0, 200, 83, 0.1)'
                                                                        : analysis.direction === 'bearish'
                                                                          ? 'rgba(255, 59, 48, 0.1)'
                                                                          : 'rgba(158, 158, 158, 0.1)',
                                                                border:
                                                                    analysis.direction === 'bullish'
                                                                        ? '1px solid #00c853'
                                                                        : analysis.direction === 'bearish'
                                                                          ? '1px solid #ff3b30'
                                                                          : '1px solid #9e9e9e',
                                                                color:
                                                                    analysis.direction === 'bullish'
                                                                        ? '#00c853'
                                                                        : analysis.direction === 'bearish'
                                                                          ? '#ff3b30'
                                                                          : '#9e9e9e',
                                                            }}
                                                        >
                                                            {analysis.direction === 'bullish'
                                                                ? '📈 BULLISH'
                                                                : analysis.direction === 'bearish'
                                                                  ? '📉 BEARISH'
                                                                  : '➡️ NEUTRAL'}
                                                        </div>
                                                    </div>

                                                    <div className="analysis-explanation">
                                                        <div className="explanation-label">Market Intelligence</div>
                                                        <p>{analysis.explanation}</p>
                                                    </div>

                                                    <div className="analysis-sectors">
                                                        <div className="sectors-label">Affected Sectors</div>
                                                        <div className="sectors-list">
                                                            {analysis.affectedSectors.map((sector) => (
                                                                <span key={sector} className="sector-tag">
                                                                    {sector}
                                                                </span>
                                                            ))}
                                                        </div>
                                                    </div>

                                                    {selectedNews.affected_tickers && (
                                                        <div className="analysis-tickers">
                                                            <div className="tickers-label">Related Tickers</div>
                                                            <div className="tickers-grid">
                                                                {selectedNews.affected_tickers
                                                                    .split(',')
                                                                    .map((t) => t.trim())
                                                                    .map((ticker) => (
                                                                        <button
                                                                            key={ticker}
                                                                            className={`ticker-button ${watchlist.has(ticker) ? 'in-watchlist' : ''}`}
                                                                            onClick={() => {
                                                                                setSelectedTicker(ticker);
                                                                                setSelectedNews(null);
                                                                            }}
                                                                        >
                                                                            {ticker}
                                                                        </button>
                                                                    ))}
                                                            </div>
                                                        </div>
                                                    )}

                                                    <div className="analysis-source">
                                                        <span className="source-label">Source:</span>
                                                        <span className="source-name">{selectedNews.source}</span>
                                                        <span className="source-time">{formatTimeAgo(selectedNews.timestamp)}</span>
                                                    </div>
                                                </>
                                            );
                                        })()}
                                    </div>
                                </div>
                            ) : (
                                <div className="dashboard-card">
                                    <div className="card-header">
                                        <h3>Live Intelligence Feed</h3>
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
                                        ) : filteredNews.length === 0 ? (
                                            <div className="empty-state-small">No news items found</div>
                                        ) : (
                                            filteredNews.slice(0, 15).map((item) => {
                                                const analysis = analyzeNews(item);
                                                return (
                                                    <div key={item.id} className="news-stream-item" onClick={() => setSelectedNews(item)}>
                                                        <div className="news-stream-header">
                                                            <span className="news-source">{item.source}</span>
                                                            <span className="news-time">{formatTimeAgo(item.timestamp)}</span>
                                                        </div>
                                                        <div className="news-stream-title">{item.title}</div>
                                                        <div className="news-stream-meta">
                                                            <span
                                                                className="sentiment-indicator"
                                                                style={{
                                                                    background:
                                                                        item.sentiment === 'positive'
                                                                            ? '#00c853'
                                                                            : item.sentiment === 'negative'
                                                                              ? '#ff1744'
                                                                              : '#9e9e9e',
                                                                }}
                                                            >
                                                                {item.sentiment}
                                                            </span>
                                                            <span className="impact-badge-mini">{analysis.impact}</span>
                                                            <span className="probability-text">{analysis.probability}%</span>
                                                        </div>
                                                        {item.affected_tickers && (
                                                            <div className="news-tickers">
                                                                {item.affected_tickers
                                                                    .split(',')
                                                                    .map((t) => t.trim())
                                                                    .slice(0, 4)
                                                                    .map((t) => (
                                                                        <span
                                                                            key={t}
                                                                            className="ticker-chip-micro"
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
                                                    </div>
                                                );
                                            })
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* News Tab */}
            {activeTab === 'news' && (
                <div className="news-view">
                    <div className="news-view-header">
                        <div className="news-header-top">
                            <h2>📰 Intelligence News Feed</h2>
                            <div className="news-stats">
                                <span className="news-total">{filteredNews.length} articles</span>
                                <span className="news-sources-count">{allNewsSources.length} sources</span>
                            </div>
                        </div>

                        <div className="news-filters-bar">
                            <div className="filter-group">
                                <label className="filter-label">Time Range</label>
                                <div className="time-range-buttons">
                                    {(['1h', '24h', '7d', 'all'] as const).map((range) => (
                                        <button
                                            key={range}
                                            className={`time-btn ${newsFilters.timeRange === range ? 'active' : ''}`}
                                            onClick={() => setNewsFilters({ ...newsFilters, timeRange: range })}
                                        >
                                            {range === '1h'
                                                ? '1 Hour'
                                                : range === '24h'
                                                  ? '24 Hours'
                                                  : range === '7d'
                                                    ? '7 Days'
                                                    : 'All Time'}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            <div className="filter-group">
                                <label className="filter-label">Sentiment</label>
                                <div className="sentiment-filters">
                                    {['positive', 'negative', 'neutral'].map((sentiment) => (
                                        <label key={sentiment} className="sentiment-checkbox">
                                            <input
                                                type="checkbox"
                                                checked={newsFilters.sentiments.has(sentiment)}
                                                onChange={(e) => {
                                                    const next = new Set(newsFilters.sentiments);
                                                    if (e.target.checked) next.add(sentiment);
                                                    else next.delete(sentiment);
                                                    setNewsFilters({ ...newsFilters, sentiments: next });
                                                }}
                                            />
                                            <span className={`sentiment-label ${sentiment}`}>{sentiment}</span>
                                        </label>
                                    ))}
                                </div>
                            </div>

                            <div className="filter-group">
                                <label className="filter-label">Sources ({allNewsSources.length})</label>
                                <div className="sources-filters">
                                    {allNewsSources.map((source) => (
                                        <label key={source} className="source-checkbox">
                                            <input
                                                type="checkbox"
                                                checked={newsFilters.sources.has(source)}
                                                onChange={(e) => {
                                                    const next = new Set(newsFilters.sources);
                                                    if (e.target.checked) next.add(source);
                                                    else next.delete(source);
                                                    setNewsFilters({ ...newsFilters, sources: next });
                                                }}
                                            />
                                            <span className="source-name">{source}</span>
                                        </label>
                                    ))}
                                </div>
                            </div>

                            {(newsFilters.sources.size > 0 || newsFilters.sentiments.size < 3 || newsFilters.timeRange !== 'all') && (
                                <button
                                    className="clear-filters-btn"
                                    onClick={() =>
                                        setNewsFilters({
                                            sources: new Set(),
                                            sentiments: new Set(['positive', 'negative', 'neutral']),
                                            timeRange: 'all',
                                        })
                                    }
                                >
                                    Clear Filters
                                </button>
                            )}
                        </div>
                    </div>

                    <div className="news-grid-view">
                        {loadingStates.news ? (
                            <div className="loading-skeleton">
                                {[...Array(12)].map((_, i) => (
                                    <div key={i} className="skeleton-item"></div>
                                ))}
                            </div>
                        ) : filteredNews.length === 0 ? (
                            <div className="empty-state-large">
                                <div className="empty-icon">📰</div>
                                <div className="empty-title">No news items found</div>
                                <div className="empty-subtitle">Try adjusting your filters or check back later</div>
                            </div>
                        ) : (
                            filteredNews.map((item) => {
                                const analysis = analyzeNews(item);
                                return (
                                    <div key={item.id} className="news-card" onClick={() => setSelectedNews(item)}>
                                        <div className="news-card-header">
                                            <span className="news-card-source">{item.source}</span>
                                            <span className="news-card-time">{formatTimeAgo(item.timestamp)}</span>
                                        </div>

                                        <h3 className="news-card-title">{item.title}</h3>

                                        {item.content && <p className="news-card-content">{item.content.substring(0, 150)}...</p>}

                                        <div className="news-card-analysis">
                                            <div className="analysis-row">
                                                <div className="analysis-item">
                                                    <span className="analysis-item-label">Impact</span>
                                                    <span className={`analysis-value impact-${analysis.impact}`}>
                                                        {analysis.impact.toUpperCase()}
                                                    </span>
                                                </div>
                                                <div className="analysis-item">
                                                    <span className="analysis-item-label">Probability</span>
                                                    <span className="analysis-value probability">{analysis.probability}%</span>
                                                </div>
                                                <div className="analysis-item">
                                                    <span className="analysis-item-label">Timeframe</span>
                                                    <span className="analysis-value timeframe">{analysis.timeframe}</span>
                                                </div>
                                            </div>
                                        </div>

                                        <div className="news-card-footer">
                                            <span
                                                className="sentiment-badge"
                                                style={{
                                                    background:
                                                        item.sentiment === 'positive'
                                                            ? 'rgba(0, 200, 83, 0.15)'
                                                            : item.sentiment === 'negative'
                                                              ? 'rgba(255, 59, 48, 0.15)'
                                                              : 'rgba(158, 158, 158, 0.15)',
                                                    color:
                                                        item.sentiment === 'positive'
                                                            ? '#00c853'
                                                            : item.sentiment === 'negative'
                                                              ? '#ff3b30'
                                                              : '#9e9e9e',
                                                    border:
                                                        item.sentiment === 'positive'
                                                            ? '1px solid #00c853'
                                                            : item.sentiment === 'negative'
                                                              ? '1px solid #ff3b30'
                                                              : '1px solid #9e9e9e',
                                                }}
                                            >
                                                {item.sentiment === 'positive' ? '📈' : item.sentiment === 'negative' ? '📉' : '➡️'}{' '}
                                                {item.sentiment.toUpperCase()}
                                            </span>

                                            {item.affected_tickers && (
                                                <div className="news-card-tickers">
                                                    {item.affected_tickers
                                                        .split(',')
                                                        .map((t) => t.trim())
                                                        .slice(0, 4)
                                                        .map((ticker) => (
                                                            <span
                                                                key={ticker}
                                                                className="news-ticker-tag"
                                                                onClick={(e) => {
                                                                    e.stopPropagation();
                                                                    setSelectedTicker(ticker);
                                                                    setActiveTab('dashboard');
                                                                }}
                                                            >
                                                                {ticker}
                                                            </span>
                                                        ))}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                );
                            })
                        )}
                    </div>
                </div>
            )}

            <footer className="product-footer">
                <div className="footer-status">
                    <span className="status-dot connected"></span>
                    <span>
                        Connected • {filteredEvents.length} events • {filteredNews.length} news items • Real-time intelligence
                    </span>
                </div>
                <div className="footer-info">Aeon Nimbus Intelligence v3.0 Professional • Market data updated every 10s</div>
            </footer>
        </div>
    );
};
