import React, { useState, useEffect } from 'react';
import './CleanApp.css';

interface Event {
  id: number;
  title: string;
  date: string;
  category: string;
  description: string;
  impact_score: number;
  tickers: string;
  phase: string;
  days_until: number;
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

export const CleanApp: React.FC = () => {
  const [events, setEvents] = useState<Event[]>([]);
  const [news, setNews] = useState<NewsItem[]>([]);
  const [stats, setStats] = useState<Stats>({ total_events: 0, total_news: 0, active_alerts: 0 });
  const [chatInput, setChatInput] = useState('');
  const [chatMessages, setChatMessages] = useState<Array<{ role: string; content: string }>>([]);
  const [selectedPhase, setSelectedPhase] = useState<string>('all');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');

  useEffect(() => {
    fetchEvents();
    fetchNews();
    fetchStats();

    const interval = setInterval(() => {
      fetchEvents();
      fetchNews();
      fetchStats();
    }, 10000);

    return () => clearInterval(interval);
  }, []);

  const fetchEvents = async () => {
    try {
      const response = await fetch('http://localhost:8001/api/events/live');
      const data = await response.json();
      setEvents(data.events || []);
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
      setChatMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
    } catch (error) {
      setChatMessages(prev => [...prev, { role: 'assistant', content: 'Error: Could not connect to AI agent.' }]);
    }
  };

  const getPhaseColor = (phase: string) => {
    if (phase.includes('Danger')) return 'var(--danger)';
    if (phase.includes('Euforia')) return 'var(--warning)';
    if (phase.includes('Accumulation')) return 'var(--success)';
    return 'var(--info)';
  };

  const getSentimentColor = (sentiment: string) => {
    if (sentiment === 'bullish') return 'var(--bullish)';
    if (sentiment === 'bearish') return 'var(--bearish)';
    return 'var(--neutral)';
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

  const filteredEvents = events.filter(event => {
    if (selectedPhase !== 'all' && !event.phase.includes(selectedPhase)) return false;
    if (selectedCategory !== 'all' && event.category !== selectedCategory) return false;
    return true;
  });

  const phaseGroups = {
    'Danger': events.filter(e => e.phase.includes('Danger')).length,
    'Euforia': events.filter(e => e.phase.includes('Euforia')).length,
    'Accumulation': events.filter(e => e.phase.includes('Accumulation')).length,
    'Pre-Rumor': events.filter(e => e.phase.includes('Pre-Rumor')).length,
  };

  return (
    <div className="clean-app">
      {/* Header */}
      <header className="header">
        <div className="header-left">
          <div className="logo">AEON NIMBUS</div>
          <div className="subtitle">INTELLIGENCE</div>
        </div>
        <div className="header-stats">
          <div className="stat">
            <span className="stat-label">EVENTS</span>
            <span className="stat-value">{stats.total_events}</span>
          </div>
          <div className="stat">
            <span className="stat-label">NEWS</span>
            <span className="stat-value">{stats.total_news}</span>
          </div>
          <div className="stat">
            <span className="stat-label">ALERTS</span>
            <span className="stat-value">{stats.active_alerts}</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="main-content">
        {/* Left Column - Events */}
        <div className="left-column">
          {/* Phase Overview */}
          <div className="section phase-overview">
            <div className="section-header">
              <h2>PHASE OVERVIEW</h2>
            </div>
            <div className="phase-grid">
              <div className="phase-item danger" onClick={() => setSelectedPhase(selectedPhase === 'Danger' ? 'all' : 'Danger')}>
                <div className="phase-name">DANGER ZONE</div>
                <div className="phase-count">{phaseGroups.Danger}</div>
                <div className="phase-range">D-0 to D-2</div>
              </div>
              <div className="phase-item euforia" onClick={() => setSelectedPhase(selectedPhase === 'Euforia' ? 'all' : 'Euforia')}>
                <div className="phase-name">EUFORIA</div>
                <div className="phase-count">{phaseGroups.Euforia}</div>
                <div className="phase-range">D-3 to D-9</div>
              </div>
              <div className="phase-item accumulation" onClick={() => setSelectedPhase(selectedPhase === 'Accumulation' ? 'all' : 'Accumulation')}>
                <div className="phase-name">ACCUMULATION</div>
                <div className="phase-count">{phaseGroups.Accumulation}</div>
                <div className="phase-range">D-10 to D-20</div>
              </div>
              <div className="phase-item pre-rumor" onClick={() => setSelectedPhase(selectedPhase === 'Pre-Rumor' ? 'all' : 'Pre-Rumor')}>
                <div className="phase-name">PRE-RUMOR</div>
                <div className="phase-count">{phaseGroups['Pre-Rumor']}</div>
                <div className="phase-range">D-20+</div>
              </div>
            </div>
          </div>

          {/* Events Table */}
          <div className="section events-section">
            <div className="section-header">
              <h2>EVENT TIMELINE</h2>
              <select
                className="filter-select"
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
              >
                <option value="all">ALL CATEGORIES</option>
                <option value="macro">MACRO</option>
                <option value="earnings">EARNINGS</option>
                <option value="commodity">COMMODITY</option>
                <option value="geopolitical">GEOPOLITICAL</option>
              </select>
            </div>
            <div className="events-table-container">
              <table className="events-table">
                <thead>
                  <tr>
                    <th>D</th>
                    <th>EVENT</th>
                    <th>CATEGORY</th>
                    <th>IMPACT</th>
                    <th>PHASE</th>
                    <th>DATE</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredEvents.map(event => (
                    <tr key={event.id}>
                      <td className="days-cell">D-{event.days_until}</td>
                      <td className="title-cell">{event.title}</td>
                      <td className="category-cell">{event.category}</td>
                      <td className="impact-cell">
                        <div className="impact-bar">
                          <div className="impact-fill" style={{ width: `${event.impact_score * 10}%` }} />
                        </div>
                        <span className="impact-score">{event.impact_score.toFixed(1)}</span>
                      </td>
                      <td>
                        <span className="phase-badge" style={{ color: getPhaseColor(event.phase) }}>
                          {event.phase.split(' ')[0]}
                        </span>
                      </td>
                      <td className="date-cell">{new Date(event.date).toLocaleDateString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right Column - News & Chat */}
        <div className="right-column">
          {/* Live News */}
          <div className="section news-section">
            <div className="section-header">
              <h2>LIVE NEWS FEED</h2>
              <div className="live-indicator">
                <span className="pulse-dot"></span>
                LIVE
              </div>
            </div>
            <div className="news-list">
              {news.map(item => (
                <div key={item.id} className="news-item">
                  <div className="news-header">
                    <span className="news-source">{item.source}</span>
                    <span className="news-time">{formatTimeAgo(item.published_at)}</span>
                  </div>
                  <div className="news-title">{item.title}</div>
                  <div className="news-footer">
                    <span className="sentiment-badge" style={{ color: getSentimentColor(item.sentiment) }}>
                      {item.sentiment.toUpperCase()}
                    </span>
                    <span className="sentiment-score">
                      {(item.sentiment_score * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* AI Chat */}
          <div className="section chat-section">
            <div className="section-header">
              <h2>AI AGENT</h2>
            </div>
            <div className="chat-container">
              <div className="chat-messages">
                {chatMessages.length === 0 ? (
                  <div className="chat-placeholder">
                    <p>Ask anything about events, news, or market intelligence...</p>
                    <div className="suggested-queries">
                      <button onClick={() => setChatInput('What events are happening this week?')}>
                        Events this week
                      </button>
                      <button onClick={() => setChatInput('What is the market sentiment?')}>
                        Market sentiment
                      </button>
                      <button onClick={() => setChatInput('Show me high impact events')}>
                        High impact events
                      </button>
                    </div>
                  </div>
                ) : (
                  chatMessages.map((msg, i) => (
                    <div key={i} className={`chat-message ${msg.role}`}>
                      <div className="message-role">{msg.role === 'user' ? '>' : '◆'}</div>
                      <div className="message-content">{msg.content}</div>
                    </div>
                  ))
                )}
              </div>
              <form className="chat-input-form" onSubmit={handleChatSubmit}>
                <input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  placeholder="Ask anything..."
                  className="chat-input"
                />
                <button type="submit" className="chat-submit">→</button>
              </form>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="footer">
        <div className="footer-left">
          <span className="status-dot"></span>
          <span>CONNECTED</span>
        </div>
        <div className="footer-right">
          <span>AEON NIMBUS INTELLIGENCE v2.0</span>
        </div>
      </footer>
    </div>
  );
};
