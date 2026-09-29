import React, { useState, useEffect } from 'react';
import './CompleteApp.css';

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

interface Stats {
    total_events: number;
    total_news: number;
    active_alerts: number;
}

export const CompleteApp: React.FC = () => {
    const [events, setEvents] = useState<Event[]>([]);
    const [news, setNews] = useState<NewsItem[]>([]);
    const [stats, setStats] = useState<Stats>({ total_events: 0, total_news: 0, active_alerts: 0 });
    const [chatInput, setChatInput] = useState('');
    const [chatMessages, setChatMessages] = useState<Array<{ role: string; content: string }>>([]);
    const [selectedPhase, setSelectedPhase] = useState<string>('all');
    const [selectedCategory, setSelectedCategory] = useState<string>('all');
    const [selectedEvent, setSelectedEvent] = useState<Event | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
    const [viewMode, setViewMode] = useState<'table' | 'calendar'>('table');
    const [calendarView, setCalendarView] = useState<'week' | 'month'>('month');

    useEffect(() => {
        fetchEvents();
        fetchNews();
        fetchStats();

        const interval = setInterval(() => {
            fetchEvents();
            fetchNews();
            fetchStats();
            setLastUpdate(new Date());
        }, 10000);

        return () => clearInterval(interval);
    }, []);

    const fetchEvents = async () => {
        try {
            const response = await fetch('http://localhost:8001/api/events/live');
            const data = await response.json();
            setEvents(data || []);
        } catch (error) {
            console.error('Error fetching events:', error);
        }
    };

    const fetchNews = async () => {
        try {
            const response = await fetch('http://localhost:8001/api/news/live');
            const data = await response.json();
            setNews(data.news || []);
        } catch (error) {
            console.error('Error fetching news:', error);
        }
    };

    const fetchStats = async () => {
        try {
            const response = await fetch('http://localhost:8001/api/stats');
            const data = await response.json();
            setStats(data);
        } catch (error) {
            console.error('Error fetching stats:', error);
        }
    };

    const handleChatSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!chatInput.trim()) return;

        const userMessage = { role: 'user', content: chatInput };
        setChatMessages([...chatMessages, userMessage]);
        setChatInput('');

        try {
            const response = await fetch('http://localhost:8001/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: chatInput }),
            });
            const data = await response.json();
            setChatMessages((prev) => [...prev, { role: 'assistant', content: data.response }]);
        } catch (error) {
            setChatMessages((prev) => [...prev, { role: 'assistant', content: 'Error: Could not connect to AI agent.' }]);
        }
    };

    const getPhaseColor = (phase: string) => {
        if (phase.includes('DANGER')) return '#ff3b30';
        if (phase.includes('EUFORIA')) return '#ff9500';
        if (phase.includes('ACCUMULATION')) return '#34c759';
        return '#007aff';
    };

    const getSentimentColor = (sentiment: string) => {
        if (sentiment === 'bullish') return '#00c853';
        if (sentiment === 'bearish') return '#ff1744';
        return '#9e9e9e';
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
        const diffDays = Math.floor(diffHours / 24);
        return `${diffDays}d ago`;
    };

    const filteredEvents = events.filter((event) => {
        if (selectedPhase !== 'all' && !event.phase.includes(selectedPhase)) return false;
        if (selectedCategory !== 'all' && event.event_type !== selectedCategory) return false;
        if (searchQuery && !event.title.toLowerCase().includes(searchQuery.toLowerCase())) return false;
        return true;
    });

    const phaseGroups = {
        DANGER: events.filter((e) => e.phase.includes('DANGER')),
        EUFORIA: events.filter((e) => e.phase.includes('EUFORIA')),
        ACCUMULATION: events.filter((e) => e.phase.includes('ACCUMULATION')),
        'PRE-RUMOR': events.filter((e) => e.phase.includes('PRE-RUMOR')),
    };

    const upcomingToday = events.filter((e) => e.days_away === 0);
    const upcomingThisWeek = events.filter((e) => e.days_away <= 7);
    const highImpact = events.filter((e) => e.impact_score >= 7);

    // Calendar functions
    const getCalendarDays = () => {
        const today = new Date();
        const days: Date[] = [];

        if (calendarView === 'week') {
            // Next 7 days
            for (let i = 0; i < 7; i++) {
                const day = new Date(today);
                day.setDate(today.getDate() + i);
                days.push(day);
            }
        } else {
            // Next 30 days
            for (let i = 0; i < 30; i++) {
                const day = new Date(today);
                day.setDate(today.getDate() + i);
                days.push(day);
            }
        }

        return days;
    };

    const getEventsForDay = (day: Date) => {
        const dayStr = day.toISOString().split('T')[0];
        return filteredEvents.filter((event) => {
            const eventDate = new Date(event.date).toISOString().split('T')[0];
            return eventDate === dayStr;
        });
    };

    const calendarDays = getCalendarDays();

    return (
        <div className="complete-app">
            {/* Top Bar */}
            <div className="top-bar">
                <div className="top-bar-left">
                    <div className="logo-container">
                        <div className="logo">AEON NIMBUS</div>
                        <div className="logo-subtitle">INTELLIGENCE</div>
                    </div>
                    <div className="search-box">
                        <span className="search-icon">🔍</span>
                        <input
                            type="text"
                            placeholder="Search events..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="search-input"
                        />
                    </div>
                </div>
                <div className="top-bar-right">
                    <div className="quick-stats">
                        <div className="quick-stat">
                            <span className="quick-stat-value">{stats.total_events}</span>
                            <span className="quick-stat-label">Events</span>
                        </div>
                        <div className="quick-stat">
                            <span className="quick-stat-value">{stats.total_news}</span>
                            <span className="quick-stat-label">News</span>
                        </div>
                        <div className="quick-stat">
                            <span className="quick-stat-value">{stats.active_alerts}</span>
                            <span className="quick-stat-label">Alerts</span>
                        </div>
                    </div>
                    <div className="update-indicator">
                        <span className="live-dot"></span>
                        <span className="update-text">Updated {formatTimeAgo(lastUpdate.toISOString())}</span>
                    </div>
                </div>
            </div>

            {/* Main Layout */}
            <div className="main-layout">
                {/* Sidebar */}
                <div className="sidebar">
                    <div className="sidebar-section">
                        <div className="sidebar-title">QUICK VIEW</div>
                        <div className="sidebar-card" onClick={() => setSelectedPhase('DANGER')}>
                            <div className="sidebar-card-label">Today</div>
                            <div className="sidebar-card-value">{upcomingToday.length}</div>
                        </div>
                        <div className="sidebar-card" onClick={() => setSelectedPhase('all')}>
                            <div className="sidebar-card-label">This Week</div>
                            <div className="sidebar-card-value">{upcomingThisWeek.length}</div>
                        </div>
                        <div className="sidebar-card" onClick={() => setSelectedPhase('all')}>
                            <div className="sidebar-card-label">High Impact</div>
                            <div className="sidebar-card-value">{highImpact.length}</div>
                        </div>
                    </div>

                    <div className="sidebar-section">
                        <div className="sidebar-title">PHASE DISTRIBUTION</div>
                        <div
                            className="phase-sidebar-item danger"
                            onClick={() => setSelectedPhase(selectedPhase === 'DANGER' ? 'all' : 'DANGER')}
                        >
                            <div className="phase-sidebar-info">
                                <div className="phase-sidebar-name">Danger Zone</div>
                                <div className="phase-sidebar-range">D-0 to D-2</div>
                            </div>
                            <div className="phase-sidebar-count">{phaseGroups.DANGER.length}</div>
                        </div>
                        <div
                            className="phase-sidebar-item euforia"
                            onClick={() => setSelectedPhase(selectedPhase === 'EUFORIA' ? 'all' : 'EUFORIA')}
                        >
                            <div className="phase-sidebar-info">
                                <div className="phase-sidebar-name">Euforia</div>
                                <div className="phase-sidebar-range">D-3 to D-9</div>
                            </div>
                            <div className="phase-sidebar-count">{phaseGroups.EUFORIA.length}</div>
                        </div>
                        <div
                            className="phase-sidebar-item accumulation"
                            onClick={() => setSelectedPhase(selectedPhase === 'ACCUMULATION' ? 'all' : 'ACCUMULATION')}
                        >
                            <div className="phase-sidebar-info">
                                <div className="phase-sidebar-name">Accumulation</div>
                                <div className="phase-sidebar-range">D-10 to D-20</div>
                            </div>
                            <div className="phase-sidebar-count">{phaseGroups.ACCUMULATION.length}</div>
                        </div>
                        <div
                            className="phase-sidebar-item pre-rumor"
                            onClick={() => setSelectedPhase(selectedPhase === 'PRE-RUMOR' ? 'all' : 'PRE-RUMOR')}
                        >
                            <div className="phase-sidebar-info">
                                <div className="phase-sidebar-name">Pre-Rumor</div>
                                <div className="phase-sidebar-range">D-20+</div>
                            </div>
                            <div className="phase-sidebar-count">{phaseGroups['PRE-RUMOR'].length}</div>
                        </div>
                    </div>

                    <div className="sidebar-section">
                        <div className="sidebar-title">FILTERS</div>
                        <select className="sidebar-select" value={selectedCategory} onChange={(e) => setSelectedCategory(e.target.value)}>
                            <option value="all">All Categories</option>
                            <option value="macro">Macro</option>
                            <option value="earnings">Earnings</option>
                            <option value="commodity">Commodity</option>
                            <option value="geopolitical">Geopolitical</option>
                            <option value="political">Political</option>
                        </select>
                    </div>

                    <div className="sidebar-section">
                        <div className="sidebar-title">VIEW MODE</div>
                        <div className="view-toggle">
                            <button className={viewMode === 'table' ? 'active' : ''} onClick={() => setViewMode('table')}>
                                📊 Table
                            </button>
                            <button className={viewMode === 'calendar' ? 'active' : ''} onClick={() => setViewMode('calendar')}>
                                📅 Calendar
                            </button>
                        </div>
                        {viewMode === 'calendar' && (
                            <div className="calendar-toggle">
                                <button className={calendarView === 'week' ? 'active' : ''} onClick={() => setCalendarView('week')}>
                                    Week
                                </button>
                                <button className={calendarView === 'month' ? 'active' : ''} onClick={() => setCalendarView('month')}>
                                    Month
                                </button>
                            </div>
                        )}
                    </div>
                </div>

                {/* Center Content */}
                <div className="center-content">
                    <div className="content-header">
                        <h1 className="content-title">
                            {viewMode === 'table'
                                ? 'Event Timeline'
                                : `Calendar View - ${calendarView === 'week' ? 'Next 7 Days' : 'Next 30 Days'}`}
                        </h1>
                        <div className="content-meta">
                            {selectedPhase !== 'all' && (
                                <span className="filter-badge">
                                    {selectedPhase} ({filteredEvents.length})<button onClick={() => setSelectedPhase('all')}>×</button>
                                </span>
                            )}
                            {selectedCategory !== 'all' && (
                                <span className="filter-badge">
                                    {selectedCategory}
                                    <button onClick={() => setSelectedCategory('all')}>×</button>
                                </span>
                            )}
                        </div>
                    </div>

                    <div className="events-container">
                        {viewMode === 'table' ? (
                            // Table View
                            filteredEvents.length === 0 ? (
                                <div className="empty-state">
                                    <div className="empty-icon">📊</div>
                                    <div className="empty-text">No events match your filters</div>
                                </div>
                            ) : (
                                <table className="events-table-complete">
                                    <thead>
                                        <tr>
                                            <th>COUNTDOWN</th>
                                            <th>EVENT</th>
                                            <th>CATEGORY</th>
                                            <th>IMPACT</th>
                                            <th>PHASE</th>
                                            <th>DATE</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {filteredEvents.map((event) => (
                                            <tr
                                                key={event.id}
                                                onClick={() => setSelectedEvent(event)}
                                                className={selectedEvent?.id === event.id ? 'selected' : ''}
                                            >
                                                <td className="countdown-cell">
                                                    <div className="countdown-badge">D-{event.days_away}</div>
                                                </td>
                                                <td className="event-title-cell">
                                                    <div className="event-title">{event.title}</div>
                                                    {event.affected_tickers && (
                                                        <div className="event-tickers">
                                                            {event.affected_tickers.split(',').slice(0, 3).join(', ')}
                                                        </div>
                                                    )}
                                                </td>
                                                <td className="category-cell-complete">
                                                    <span className="category-tag">{event.event_type}</span>
                                                </td>
                                                <td className="impact-cell-complete">
                                                    <div className="impact-visual">
                                                        <div className="impact-bar-outer">
                                                            <div
                                                                className="impact-bar-inner"
                                                                style={{
                                                                    width: `${event.impact_score * 10}%`,
                                                                    background:
                                                                        event.impact_score >= 8
                                                                            ? '#ff3b30'
                                                                            : event.impact_score >= 6
                                                                              ? '#ff9500'
                                                                              : '#00d9ff',
                                                                }}
                                                            />
                                                        </div>
                                                        <span className="impact-number">{event.impact_score.toFixed(1)}</span>
                                                    </div>
                                                </td>
                                                <td className="phase-cell">
                                                    <span
                                                        className="phase-tag"
                                                        style={{
                                                            color: getPhaseColor(event.phase),
                                                            borderColor: getPhaseColor(event.phase),
                                                        }}
                                                    >
                                                        {event.phase.split(' ')[0].toUpperCase()}
                                                    </span>
                                                </td>
                                                <td className="date-cell-complete">
                                                    {new Date(event.date).toLocaleDateString('en-US', {
                                                        month: 'short',
                                                        day: 'numeric',
                                                        year: 'numeric',
                                                    })}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            )
                        ) : (
                            // Calendar View
                            <div className={`calendar-grid ${calendarView}`}>
                                {calendarDays.map((day, index) => {
                                    const dayEvents = getEventsForDay(day);
                                    const isToday = day.toDateString() === new Date().toDateString();

                                    return (
                                        <div key={index} className={`calendar-day ${isToday ? 'today' : ''}`}>
                                            <div className="calendar-day-header">
                                                <div className="calendar-day-name">
                                                    {day.toLocaleDateString('en-US', { weekday: 'short' })}
                                                </div>
                                                <div className="calendar-day-number">{day.getDate()}</div>
                                                <div className="calendar-day-month">
                                                    {day.toLocaleDateString('en-US', { month: 'short' })}
                                                </div>
                                            </div>
                                            <div className="calendar-day-events">
                                                {dayEvents.length === 0 ? (
                                                    <div className="calendar-no-events">No events</div>
                                                ) : (
                                                    dayEvents.map((event) => (
                                                        <div
                                                            key={event.id}
                                                            className="calendar-event"
                                                            onClick={() => setSelectedEvent(event)}
                                                            style={{ borderLeftColor: getPhaseColor(event.phase) }}
                                                        >
                                                            <div className="calendar-event-title">{event.title}</div>
                                                            <div className="calendar-event-meta">
                                                                <span className="calendar-event-time">
                                                                    {new Date(event.date).toLocaleTimeString('en-US', {
                                                                        hour: 'numeric',
                                                                        minute: '2-digit',
                                                                    })}
                                                                </span>
                                                                <span
                                                                    className="calendar-event-impact"
                                                                    style={{
                                                                        background:
                                                                            event.impact_score >= 8
                                                                                ? '#ff3b30'
                                                                                : event.impact_score >= 6
                                                                                  ? '#ff9500'
                                                                                  : '#00d9ff',
                                                                    }}
                                                                >
                                                                    {event.impact_score.toFixed(1)}
                                                                </span>
                                                            </div>
                                                        </div>
                                                    ))
                                                )}
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                    </div>
                </div>

                {/* Right Panel */}
                <div className="right-panel">
                    {/* Event Detail */}
                    {selectedEvent ? (
                        <div className="panel-section event-detail">
                            <div className="panel-header">
                                <h3 className="panel-title">Event Details</h3>
                                <button className="close-btn" onClick={() => setSelectedEvent(null)}>
                                    ×
                                </button>
                            </div>
                            <div className="event-detail-content">
                                <div className="event-detail-title">{selectedEvent.title}</div>
                                <div className="event-detail-meta">
                                    <div className="event-detail-row">
                                        <span className="event-detail-label">Countdown:</span>
                                        <span className="event-detail-value countdown">D-{selectedEvent.days_away}</span>
                                    </div>
                                    <div className="event-detail-row">
                                        <span className="event-detail-label">Date:</span>
                                        <span className="event-detail-value">
                                            {new Date(selectedEvent.date).toLocaleDateString('en-US', {
                                                weekday: 'long',
                                                year: 'numeric',
                                                month: 'long',
                                                day: 'numeric',
                                                hour: 'numeric',
                                                minute: '2-digit',
                                            })}
                                        </span>
                                    </div>
                                    <div className="event-detail-row">
                                        <span className="event-detail-label">Category:</span>
                                        <span className="event-detail-value">{selectedEvent.event_type}</span>
                                    </div>
                                    <div className="event-detail-row">
                                        <span className="event-detail-label">Impact:</span>
                                        <span className="event-detail-value">{selectedEvent.impact_score.toFixed(1)}/10</span>
                                    </div>
                                    <div className="event-detail-row">
                                        <span className="event-detail-label">Phase:</span>
                                        <span className="event-detail-value" style={{ color: getPhaseColor(selectedEvent.phase) }}>
                                            {selectedEvent.phase}
                                        </span>
                                    </div>
                                    {selectedEvent.affected_tickers && (
                                        <div className="event-detail-row">
                                            <span className="event-detail-label">Tickers:</span>
                                            <span className="event-detail-value">{selectedEvent.affected_tickers}</span>
                                        </div>
                                    )}
                                </div>
                                {selectedEvent.description && (
                                    <div className="event-description">
                                        <div className="event-detail-label">Description:</div>
                                        <p>{selectedEvent.description}</p>
                                    </div>
                                )}
                            </div>
                        </div>
                    ) : (
                        <div className="panel-section empty-detail">
                            <div className="empty-detail-icon">📊</div>
                            <div className="empty-detail-text">Select an event to view details</div>
                        </div>
                    )}

                    {/* News Feed */}
                    <div className="panel-section news-panel">
                        <div className="panel-header">
                            <h3 className="panel-title">Live News</h3>
                            <span className="live-badge">
                                <span className="live-pulse"></span>
                                LIVE
                            </span>
                        </div>
                        <div className="news-feed-container">
                            {news.length === 0 ? (
                                <div className="empty-news">
                                    <div className="empty-news-icon">📰</div>
                                    <div className="empty-news-text">No news available</div>
                                </div>
                            ) : (
                                news.map((item) => (
                                    <div key={item.id} className="news-card">
                                        <div className="news-card-header">
                                            <span className="news-source-tag">{item.source}</span>
                                            <span className="news-time-ago">{formatTimeAgo(item.published_at)}</span>
                                        </div>
                                        <div className="news-card-title">{item.title}</div>
                                        <div className="news-card-footer">
                                            <span
                                                className="news-sentiment-tag"
                                                style={{
                                                    color: getSentimentColor(item.sentiment),
                                                    borderColor: getSentimentColor(item.sentiment),
                                                }}
                                            >
                                                {item.sentiment.toUpperCase()}
                                            </span>
                                            <span className="news-confidence">{(item.sentiment_score * 100).toFixed(0)}%</span>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>

                    {/* AI Agent */}
                    <div className="panel-section ai-panel">
                        <div className="panel-header">
                            <h3 className="panel-title">AI Agent</h3>
                        </div>
                        <div className="ai-chat-container">
                            <div className="ai-messages">
                                {chatMessages.length === 0 ? (
                                    <div className="ai-welcome">
                                        <div className="ai-welcome-icon">🤖</div>
                                        <div className="ai-welcome-text">Ask me anything about events or market intelligence</div>
                                        <div className="suggested-questions">
                                            <button onClick={() => setChatInput('What events are happening today?')}>Events today</button>
                                            <button onClick={() => setChatInput('Show me high impact events')}>High impact</button>
                                            <button onClick={() => setChatInput('What is the market sentiment?')}>Sentiment</button>
                                        </div>
                                    </div>
                                ) : (
                                    chatMessages.map((msg, i) => (
                                        <div key={i} className={`ai-message ${msg.role}`}>
                                            <div className="ai-message-avatar">{msg.role === 'user' ? '👤' : '🤖'}</div>
                                            <div className="ai-message-content">{msg.content}</div>
                                        </div>
                                    ))
                                )}
                            </div>
                            <form className="ai-input-form" onSubmit={handleChatSubmit}>
                                <input
                                    type="text"
                                    value={chatInput}
                                    onChange={(e) => setChatInput(e.target.value)}
                                    placeholder="Ask anything..."
                                    className="ai-input"
                                />
                                <button type="submit" className="ai-send-btn">
                                    →
                                </button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>

            {/* Status Bar */}
            <div className="status-bar">
                <div className="status-left">
                    <span className="status-dot connected"></span>
                    <span className="status-text">Connected to Intelligence API</span>
                </div>
                <div className="status-center">
                    <span className="status-text">
                        Showing {filteredEvents.length} of {events.length} events
                    </span>
                </div>
                <div className="status-right">
                    <span className="status-text">Aeon Nimbus Intelligence v2.0</span>
                </div>
            </div>
        </div>
    );
};
