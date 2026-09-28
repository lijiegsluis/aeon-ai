import React, { useState, useEffect } from 'react';
import './Platform.css';

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

interface Signal {
  id: number;
  ticker: string;
  action: string;
  entry: number;
  target: number;
  stop: number;
  confidence: number;
  reasoning: string;
  timeframe: string;
  risk_reward: number;
}

interface Insight {
  id: string;
  type: string;
  title: string;
  description: string;
  tickers: string[];
  confidence: number;
}

interface FearGreed {
  value: number;
  label: string;
  color: string;
}

function Platform() {
  const [activeView, setActiveView] = useState<'overview' | 'signals' | 'events' | 'news'>('overview');
  const [events, setEvents] = useState<Event[]>([]);
  const [news, setNews] = useState<NewsItem[]>([]);
  const [signals, setSignals] = useState<Signal[]>([]);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [fearGreed, setFearGreed] = useState<FearGreed | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchAllData();
    const interval = setInterval(fetchAllData, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchAllData = async () => {
    try {
      const [eventsRes, newsRes, signalsRes, insightsRes, fearGreedRes] = await Promise.all([
        fetch('http://localhost:8001/api/events/live'),
        fetch('http://localhost:8001/api/news/live'),
        fetch('http://localhost:8001/api/signals'),
        fetch('http://localhost:8001/api/insights'),
        fetch('http://localhost:8001/api/fear-greed')
      ]);

      const [eventsData, newsData, signalsData, insightsData, fearGreedData] = await Promise.all([
        eventsRes.json(),
        newsRes.json(),
        signalsRes.json(),
        insightsRes.json(),
        fearGreedRes.json()
      ]);

      setEvents(Array.isArray(eventsData) ? eventsData : []);
      setNews(Array.isArray(newsData) ? newsData : (newsData.news || []));
      setSignals(Array.isArray(signalsData) ? signalsData : (signalsData.signals || []));
      setInsights(Array.isArray(insightsData) ? insightsData : (insightsData.insights || []));
      setFearGreed(fearGreedData);
      setLoading(false);
      setError(null);
    } catch (err) {
      console.error('Fetch error:', err);
      setError('Connection error');
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="platform">
        <div className="loading-screen">
          <div className="loading-spinner" />
          <div className="loading-text">INITIALIZING SYSTEM</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="platform">
        <div className="error-screen">
          <div className="error-icon">⚠</div>
          <div className="error-title">CONNECTION FAILED</div>
          <div className="error-message">{error}</div>
          <button className="error-button" onClick={fetchAllData}>RETRY</button>
        </div>
      </div>
    );
  }

  return (
    <div className="platform">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="logo">
            <div className="logo-text">AEON NIMBUS</div>
            <div className="logo-sub">INTELLIGENCE</div>
          </div>
        </div>

        <nav className="sidebar-nav">
          <button
            className={`nav-item ${activeView === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveView('overview')}
          >
            <span className="nav-icon">◆</span>
            <span className="nav-label">OVERVIEW</span>
          </button>
          <button
            className={`nav-item ${activeView === 'signals' ? 'active' : ''}`}
            onClick={() => setActiveView('signals')}
          >
            <span className="nav-icon">▲</span>
            <span className="nav-label">SIGNALS</span>
          </button>
          <button
            className={`nav-item ${activeView === 'events' ? 'active' : ''}`}
            onClick={() => setActiveView('events')}
          >
            <span className="nav-icon">●</span>
            <span className="nav-label">EVENTS</span>
          </button>
          <button
            className={`nav-item ${activeView === 'news' ? 'active' : ''}`}
            onClick={() => setActiveView('news')}
          >
            <span className="nav-icon">■</span>
            <span className="nav-label">NEWS</span>
          </button>
        </nav>

        <div className="sidebar-footer">
          <div className="connection-status">
            <span className="status-indicator" />
            <span className="status-text">LIVE</span>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <header className="content-header">
          <h1 className="page-title">
            {activeView === 'overview' && 'MARKET OVERVIEW'}
            {activeView === 'signals' && 'TRADING SIGNALS'}
            {activeView === 'events' && 'EVENT TRACKER'}
            {activeView === 'news' && 'MARKET NEWS'}
          </h1>
          <div className="header-stats">
            <div className="stat">
              <span className="stat-label">EVENTS</span>
              <span className="stat-value">{events.length}</span>
            </div>
            <div className="stat">
              <span className="stat-label">SIGNALS</span>
              <span className="stat-value">{signals.length}</span>
            </div>
            {fearGreed && (
              <div className="stat">
                <span className="stat-label">FEAR & GREED</span>
                <span className="stat-value" style={{ color: fearGreed.color }}>
                  {fearGreed.value}
                </span>
              </div>
            )}
          </div>
        </header>

        <div className="content-body">
          {activeView === 'overview' && (
            <OverviewView events={events} insights={insights} fearGreed={fearGreed} />
          )}
          {activeView === 'signals' && <SignalsView signals={signals} />}
          {activeView === 'events' && <EventsView events={events} />}
          {activeView === 'news' && <NewsView news={news} />}
        </div>
      </main>
    </div>
  );
}

// Overview View
const OverviewView: React.FC<{
  events: Event[];
  insights: Insight[];
  fearGreed: FearGreed | null;
}> = ({ events, insights, fearGreed }) => {
  const danger = events.filter(e => e.phase === 'DANGER');
  const accumulation = events.filter(e => e.phase === 'ACCUMULATION');

  return (
    <div className="overview-view">
      {/* Metrics Grid */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-title">DANGER PHASE</span>
            <span className="metric-badge danger">{danger.length}</span>
          </div>
          <div className="metric-content">
            <div className="metric-number danger-text">{danger.length}</div>
            <div className="metric-subtitle">Events next 48h</div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-title">ACCUMULATION</span>
            <span className="metric-badge success">{accumulation.length}</span>
          </div>
          <div className="metric-content">
            <div className="metric-number success-text">{accumulation.length}</div>
            <div className="metric-subtitle">Optimal entry zone</div>
          </div>
        </div>

        {fearGreed && (
          <div className="metric-card">
            <div className="metric-header">
              <span className="metric-title">FEAR & GREED INDEX</span>
            </div>
            <div className="metric-content">
              <div className="metric-number" style={{ color: fearGreed.color }}>
                {fearGreed.value}
              </div>
              <div className="metric-subtitle">{fearGreed.label}</div>
            </div>
          </div>
        )}
      </div>

      {/* Insights */}
      {insights.length > 0 && (
        <section className="insights-section">
          <h2 className="section-title">AI INSIGHTS</h2>
          <div className="insights-grid">
            {insights.map(insight => (
              <div key={insight.id} className={`insight-card insight-${insight.type}`}>
                <div className="insight-header">
                  <span className="insight-type">{insight.type.toUpperCase()}</span>
                  <span className="insight-confidence">{insight.confidence}%</span>
                </div>
                <h3 className="insight-title">{insight.title}</h3>
                <p className="insight-description">{insight.description}</p>
                <div className="insight-tickers">
                  {insight.tickers.slice(0, 6).map((ticker, i) => (
                    <span key={i} className="ticker-chip">{ticker}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Top Events */}
      <section className="top-events-section">
        <h2 className="section-title">TOP OPPORTUNITIES</h2>
        <div className="events-table">
          {accumulation.slice(0, 10).map(event => (
            <div key={event.id} className="event-row">
              <div className="event-ticker">{event.affected_tickers.split(',')[0]}</div>
              <div className="event-info">
                <div className="event-name">{event.title}</div>
                <div className="event-meta">D-{event.days_away} • {event.event_type}</div>
              </div>
              <div className="event-phase-badge accumulation">ACCUMULATION</div>
              <div className="event-impact">{event.impact_score.toFixed(1)}</div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};

// Signals View
const SignalsView: React.FC<{ signals: Signal[] }> = ({ signals }) => {
  return (
    <div className="signals-view">
      <div className="signals-grid">
        {signals.map(signal => (
          <div key={signal.id} className="signal-card">
            <div className="signal-header">
              <div className="signal-ticker">{signal.ticker}</div>
              <div className={`signal-action action-${signal.action.toLowerCase()}`}>
                {signal.action}
              </div>
            </div>

            <div className="signal-prices">
              <div className="price-box">
                <span className="price-label">ENTRY</span>
                <span className="price-value">${signal.entry.toFixed(2)}</span>
              </div>
              <div className="price-box">
                <span className="price-label">TARGET</span>
                <span className="price-value success-text">${signal.target.toFixed(2)}</span>
              </div>
              <div className="price-box">
                <span className="price-label">STOP</span>
                <span className="price-value danger-text">${signal.stop.toFixed(2)}</span>
              </div>
            </div>

            <div className="signal-stats">
              <div className="signal-stat">
                <span>R:R</span>
                <strong>{signal.risk_reward.toFixed(2)}:1</strong>
              </div>
              <div className="signal-stat">
                <span>CONFIDENCE</span>
                <strong>{signal.confidence}%</strong>
              </div>
            </div>

            <div className="signal-reasoning">{signal.reasoning}</div>

            <button className="signal-button">EXPORT TO TERMINAL</button>
          </div>
        ))}
      </div>

      {signals.length === 0 && (
        <div className="empty-state">
          <div className="empty-icon">📊</div>
          <div className="empty-text">No active signals</div>
        </div>
      )}
    </div>
  );
};

// Events View
const EventsView: React.FC<{ events: Event[] }> = ({ events }) => {
  return (
    <div className="events-view">
      <div className="events-list">
        {events.map(event => (
          <div key={event.id} className="event-card">
            <div className="event-card-header">
              <div className="event-ticker-badge">{event.affected_tickers.split(',')[0]}</div>
              <div className={`phase-badge phase-${event.phase.toLowerCase()}`}>
                {event.phase}
              </div>
            </div>
            <h3 className="event-card-title">{event.title}</h3>
            <div className="event-card-meta">
              D-{event.days_away} • {event.event_type} • Impact {event.impact_score.toFixed(1)}/10
            </div>
            {event.recommendation && (
              <div className="event-recommendation">{event.recommendation}</div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

// News View
const NewsView: React.FC<{ news: NewsItem[] }> = ({ news }) => {
  return (
    <div className="news-view">
      <div className="news-grid">
        {news.slice(0, 30).map(item => (
          <div key={item.id} className="news-card">
            <div className="news-header">
              <span className={`sentiment-badge sentiment-${item.sentiment}`}>
                {item.sentiment.toUpperCase()}
              </span>
              <span className="news-time">
                {new Date(item.timestamp).toLocaleTimeString()}
              </span>
            </div>
            <h3 className="news-title">{item.title}</h3>
            <p className="news-content">{item.content}</p>
            <div className="news-footer">
              <span className="news-source">{item.source}</span>
              <span className="news-ticker">{item.affected_tickers}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Platform;
