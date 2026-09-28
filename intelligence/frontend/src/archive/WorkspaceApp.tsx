import React, { useState, useEffect } from 'react';
import { Window } from './components/Window';
import './App.css';
import './WorkspaceApp.css';

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

interface WorkspaceWindow {
  id: string;
  type: 'events' | 'news' | 'chat' | 'calendar' | 'stats';
  title: string;
  icon: string;
  visible: boolean;
  position: { x: number; y: number };
  size: { width: number; height: number };
  zIndex: number;
}

export const WorkspaceApp: React.FC = () => {
  const [events, setEvents] = useState<Event[]>([]);
  const [news, setNews] = useState<NewsItem[]>([]);
  const [stats, setStats] = useState<Stats>({ total_events: 0, total_news: 0, active_alerts: 0 });
  const [windows, setWindows] = useState<WorkspaceWindow[]>([
    {
      id: 'events',
      type: 'events',
      title: 'EVENT TIMELINE',
      icon: '📊',
      visible: true,
      position: { x: 20, y: 100 },
      size: { width: 600, height: 500 },
      zIndex: 1,
    },
    {
      id: 'news',
      type: 'news',
      title: 'LIVE NEWS FEED',
      icon: '📰',
      visible: true,
      position: { x: 640, y: 100 },
      size: { width: 500, height: 500 },
      zIndex: 1,
    },
    {
      id: 'chat',
      type: 'chat',
      title: 'AI AGENT',
      icon: '🤖',
      visible: true,
      position: { x: 1160, y: 100 },
      size: { width: 400, height: 500 },
      zIndex: 1,
    },
  ]);
  const [chatInput, setChatInput] = useState('');
  const [chatMessages, setChatMessages] = useState<Array<{ role: string; content: string }>>([]);
  const [maxZIndex, setMaxZIndex] = useState(3);

  // Fetch data
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

  const bringToFront = (windowId: string) => {
    const newMaxZ = maxZIndex + 1;
    setMaxZIndex(newMaxZ);
    setWindows(windows.map(w => w.id === windowId ? { ...w, zIndex: newMaxZ } : w));
  };

  const closeWindow = (windowId: string) => {
    setWindows(windows.map(w => w.id === windowId ? { ...w, visible: false } : w));
  };

  const openWindow = (windowId: string) => {
    const newMaxZ = maxZIndex + 1;
    setMaxZIndex(newMaxZ);
    setWindows(windows.map(w => w.id === windowId ? { ...w, visible: true, zIndex: newMaxZ } : w));
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

  return (
    <div className="workspace-app">
      {/* Header */}
      <div className="workspace-header">
        <div className="workspace-header-content">
          <div className="logo-section">
            <div className="logo">AEON NIMBUS</div>
            <div className="subtitle">INTELLIGENCE</div>
          </div>

          <div className="stats-bar">
            <div className="stat-item">
              <div className="stat-label">Events</div>
              <div className="stat-value">{stats.total_events}</div>
            </div>
            <div className="stat-item">
              <div className="stat-label">News</div>
              <div className="stat-value">{stats.total_news}</div>
            </div>
            <div className="stat-item">
              <div className="stat-label">Alerts</div>
              <div className="stat-value">{stats.active_alerts}</div>
            </div>
          </div>

          <div className="window-controls-bar">
            {windows.map(w => (
              <button
                key={w.id}
                className={`window-toggle ${w.visible ? 'active' : ''}`}
                onClick={() => w.visible ? closeWindow(w.id) : openWindow(w.id)}
              >
                <span className="window-toggle-icon">{w.icon}</span>
                <span className="window-toggle-label">{w.title}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Workspace Canvas */}
      <div className="workspace-canvas">
        {windows.map(window => {
          if (!window.visible) return null;

          return (
            <Window
              key={window.id}
              id={window.id}
              title={window.title}
              icon={window.icon}
              defaultPosition={window.position}
              defaultSize={window.size}
              zIndex={window.zIndex}
              onClose={() => closeWindow(window.id)}
              onFocus={() => bringToFront(window.id)}
            >
              {window.type === 'events' && (
                <div className="window-events">
                  <div className="terminal-table">
                    <table>
                      <thead>
                        <tr>
                          <th>D</th>
                          <th>EVENT</th>
                          <th>CATEGORY</th>
                          <th>IMPACT</th>
                          <th>PHASE</th>
                        </tr>
                      </thead>
                      <tbody>
                        {events.slice(0, 15).map(event => (
                          <tr key={event.id}>
                            <td className="mono-cell cyan-text">D-{event.days_until}</td>
                            <td className="event-title-cell">{event.title}</td>
                            <td className="category-cell">{event.category}</td>
                            <td>
                              <div className="impact-bar">
                                <div
                                  className="impact-fill"
                                  style={{ width: `${event.impact_score * 10}%` }}
                                />
                              </div>
                            </td>
                            <td>
                              <span
                                className="phase-badge"
                                style={{ color: getPhaseColor(event.phase) }}
                              >
                                {event.phase.split(' ')[0]}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {window.type === 'news' && (
                <div className="window-news">
                  <div className="news-feed">
                    {news.map(item => (
                      <div key={item.id} className="news-feed-item">
                        <div className="news-feed-header">
                          <span className="news-feed-source">{item.source}</span>
                          <span className="news-feed-time">{formatTimeAgo(item.published_at)}</span>
                        </div>
                        <div className="news-feed-title">{item.title}</div>
                        <div className="news-feed-footer">
                          <span
                            className="sentiment-badge"
                            style={{ color: getSentimentColor(item.sentiment) }}
                          >
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
              )}

              {window.type === 'chat' && (
                <div className="window-chat">
                  <div className="chat-messages">
                    {chatMessages.map((msg, i) => (
                      <div key={i} className={`chat-message ${msg.role}`}>
                        <div className="chat-message-role">
                          {msg.role === 'user' ? '>' : '◆'}
                        </div>
                        <div className="chat-message-content">{msg.content}</div>
                      </div>
                    ))}
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
              )}
            </Window>
          );
        })}
      </div>

      {/* Status Bar */}
      <div className="workspace-status-bar">
        <div className="status-left">
          <span className="status-indicator active"></span>
          <span className="status-text">CONNECTED</span>
        </div>
        <div className="status-right">
          <span className="status-text">AEON NIMBUS INTELLIGENCE v2.0</span>
        </div>
      </div>
    </div>
  );
};
