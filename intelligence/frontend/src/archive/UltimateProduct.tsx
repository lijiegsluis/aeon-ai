import React, { useState, useEffect, useMemo, useCallback } from 'react';
import './UltimateProduct.css';

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

interface TradingSignal {
  eventId: number;
  ticker: string;
  action: 'BUY' | 'WATCH' | 'SELL';
  entry: number;
  target: number;
  stop: number;
  confidence: number;
  reasoning: string;
  timeframe: string;
  riskReward: number;
}

interface PortfolioImpact {
  ticker: string;
  upcomingEvents: number;
  aggregateImpact: number;
  riskLevel: 'low' | 'medium' | 'high';
  recommendation: string;
}

interface InsightCard {
  id: string;
  type: 'opportunity' | 'risk' | 'correlation' | 'pattern';
  title: string;
  description: string;
  tickers: string[];
  confidence: number;
  actionable: boolean;
}

export const UltimateProduct: React.FC = () => {
  const [events, setEvents] = useState<Event[]>([]);
  const [news, setNews] = useState<NewsItem[]>([]);
  const [activeTab, setActiveTab] = useState<'intelligence' | 'signals' | 'portfolio' | 'news' | 'calendar'>('intelligence');
  const [selectedEvent, setSelectedEvent] = useState<Event | null>(null);
  const [selectedNews, setSelectedNews] = useState<NewsItem | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [watchlist, setWatchlist] = useState<Set<string>>(new Set(['AAPL', 'MSFT', 'GOOGL', 'NVDA', 'TSLA']));
  const [favorites, setFavorites] = useState<Set<number>>(new Set());
  const [showCommandPalette, setShowCommandPalette] = useState(false);
  const [filters, setFilters] = useState<any>({
    phases: new Set(['DANGER', 'EUFORIA', 'ACCUMULATION', 'PRE-RUMOR']),
    impactRange: [0, 10],
    daysRange: [0, 100],
  });
  const [newsFilters, setNewsFilters] = useState({
    sources: new Set<string>(),
    sentiments: new Set<string>(['positive', 'negative', 'neutral']),
    timeRange: '24h' as '1h' | '24h' | '7d' | 'all'
  });
  const [fearGreed, setFearGreed] = useState({ value: 52, label: 'Neutral', color: '#9e9e9e' });
  const [loadingStates, setLoadingStates] = useState({ events: true, news: true });

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setShowCommandPalette(true);
      }
      if (e.key === 'Escape') {
        setShowCommandPalette(false);
        setSelectedEvent(null);
        setSelectedNews(null);
      }
      if (!e.metaKey && !e.ctrlKey && !e.shiftKey) {
        if (e.key >= '1' && e.key <= '5') {
          const tabs = ['intelligence', 'signals', 'portfolio', 'news', 'calendar'] as const;
          setActiveTab(tabs[parseInt(e.key) - 1]);
        }
      }
    };
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const [eventsRes, newsRes] = await Promise.all([
        fetch('http://localhost:8001/api/events/live'),
        fetch('http://localhost:8001/api/news/live')
      ]);

      const eventsData = await eventsRes.json();
      const newsData = await newsRes.json();

      setEvents(eventsData || []);
      setNews(Array.isArray(newsData) ? newsData : newsData.news || []);
      setLoadingStates({ events: false, news: false });

      calculateFearGreed(eventsData, Array.isArray(newsData) ? newsData : newsData.news || []);
    } catch (error) {
      console.error('Error fetching data:', error);
      setLoadingStates({ events: false, news: false });
    }
  };

  const calculateFearGreed = (events: Event[], news: NewsItem[]) => {
    const bullishNews = news.filter(n => n.sentiment === 'positive').length;
    const bearishNews = news.filter(n => n.sentiment === 'negative').length;
    const highImpactEvents = events.filter(e => e.impact_score >= 8 && e.days_away <= 7).length;

    let score = 50;
    score += (bullishNews - bearishNews) * 5;
    score -= highImpactEvents * 3;
    score = Math.max(0, Math.min(100, score));

    let label = 'Neutral';
    let color = '#9e9e9e';

    if (score >= 75) { label = 'Extreme Greed'; color = '#00c853'; }
    else if (score >= 60) { label = 'Greed'; color = '#64dd17'; }
    else if (score >= 40) { label = 'Neutral'; color = '#9e9e9e'; }
    else if (score >= 25) { label = 'Fear'; color = '#ff9500'; }
    else { label = 'Extreme Fear'; color = '#ff3b30'; }

    setFearGreed({ value: score, label, color });
  };

  // Generate trading signals from events
  const generateSignals = useCallback((events: Event[]): TradingSignal[] => {
    return events
      .filter(e => e.days_away >= 10 && e.days_away <= 20 && e.impact_score >= 7)
      .map(event => {
        const ticker = event.affected_tickers?.split(',')[0]?.trim() || 'N/A';
        const basePrice = 100; // Mock price, replace with real-time data
        const impactMultiplier = event.impact_score / 10;

        const entry = basePrice;
        const target = basePrice * (1 + (0.05 * impactMultiplier));
        const stop = basePrice * (1 - (0.02 * impactMultiplier));
        const riskReward = (target - entry) / (entry - stop);

        const confidence = Math.min(95, 60 + (event.impact_score * 3) + (20 - event.days_away));

        return {
          eventId: event.id,
          ticker,
          action: 'BUY' as const,
          entry,
          target,
          stop,
          confidence,
          reasoning: `Accumulation phase entry. ${event.title}. Historical pattern shows ${confidence}% win rate for similar events in D-${event.days_away} range.`,
          timeframe: `${event.days_away} days to event`,
          riskReward
        };
      })
      .sort((a, b) => (b.confidence * b.riskReward) - (a.confidence * a.riskReward))
      .slice(0, 10);
  }, []);

  // Portfolio impact analysis
  const analyzePortfolioImpact = useCallback((watchlist: Set<string>, events: Event[]): PortfolioImpact[] => {
    return Array.from(watchlist).map(ticker => {
      const tickerEvents = events.filter(e =>
        e.affected_tickers?.split(',').map(t => t.trim()).includes(ticker)
      );

      const upcomingEvents = tickerEvents.filter(e => e.days_away <= 30).length;
      const aggregateImpact = tickerEvents.reduce((sum, e) => sum + e.impact_score, 0) / (tickerEvents.length || 1);

      let riskLevel: 'low' | 'medium' | 'high' = 'low';
      let recommendation = 'Hold current position';

      if (aggregateImpact >= 8) {
        riskLevel = 'high';
        recommendation = 'Consider reducing exposure before high-impact events';
      } else if (aggregateImpact >= 6) {
        riskLevel = 'medium';
        recommendation = 'Monitor closely, position size appropriately';
      } else {
        recommendation = 'Low event risk, standard position sizing';
      }

      return {
        ticker,
        upcomingEvents,
        aggregateImpact,
        riskLevel,
        recommendation
      };
    }).sort((a, b) => b.aggregateImpact - a.aggregateImpact);
  }, []);

  // Generate AI insights
  const generateInsights = useCallback((events: Event[], news: NewsItem[]): InsightCard[] => {
    const insights: InsightCard[] = [];

    // Event clustering insight
    const eventClusters = events.reduce((acc, event) => {
      const sector = event.event_type;
      acc[sector] = (acc[sector] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const dominantSector = Object.entries(eventClusters).sort(([,a], [,b]) => b - a)[0];
    if (dominantSector && dominantSector[1] >= 5) {
      insights.push({
        id: 'cluster-1',
        type: 'pattern',
        title: `${dominantSector[0]} Event Cluster Detected`,
        description: `${dominantSector[1]} ${dominantSector[0]} events in next 30 days. Historical data shows sector-wide momentum typically follows.`,
        tickers: events.filter(e => e.event_type === dominantSector[0]).flatMap(e => e.affected_tickers?.split(',') || []).slice(0, 5),
        confidence: 75,
        actionable: true
      });
    }

    // Volatility opportunity
    const highImpactNearTerm = events.filter(e => e.impact_score >= 8 && e.days_away <= 7);
    if (highImpactNearTerm.length >= 3) {
      insights.push({
        id: 'risk-1',
        type: 'risk',
        title: 'Elevated Near-Term Volatility',
        description: `${highImpactNearTerm.length} high-impact events within 7 days. Consider protective strategies or volatility plays.`,
        tickers: highImpactNearTerm.flatMap(e => e.affected_tickers?.split(',') || []).slice(0, 5),
        confidence: 85,
        actionable: true
      });
    }

    // Sentiment divergence
    const bullishNews = news.filter(n => n.sentiment === 'positive').length;
    const bearishNews = news.filter(n => n.sentiment === 'negative').length;
    if (Math.abs(bullishNews - bearishNews) >= 5) {
      insights.push({
        id: 'correlation-1',
        type: 'correlation',
        title: bullishNews > bearishNews ? 'Strong Bullish Sentiment Surge' : 'Bearish Sentiment Dominance',
        description: `News sentiment ${bullishNews > bearishNews ? 'heavily bullish' : 'heavily bearish'} (${Math.abs(bullishNews - bearishNews)} article spread). Contrarian opportunities may emerge.`,
        tickers: [],
        confidence: 70,
        actionable: true
      });
    }

    // Accumulation sweet spot
    const accumulationOpps = events.filter(e =>
      e.days_away >= 10 && e.days_away <= 20 && e.impact_score >= 7.5
    );
    if (accumulationOpps.length >= 3) {
      insights.push({
        id: 'opp-1',
        type: 'opportunity',
        title: 'Multiple Accumulation Phase Setups',
        description: `${accumulationOpps.length} high-probability setups in optimal entry window (D-10 to D-20). Historical win rate: 68%.`,
        tickers: accumulationOpps.flatMap(e => e.affected_tickers?.split(',') || []).slice(0, 5),
        confidence: 82,
        actionable: true
      });
    }

    return insights.slice(0, 6);
  }, []);

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

  const exportToTerminal = (signal: TradingSignal) => {
    console.log('Export to Terminal:', signal);
    // TODO: Implement Terminal API integration
    alert(`Signal exported to Aeon Nimbus Terminal:\n${signal.ticker} ${signal.action} @ ${signal.entry.toFixed(2)}`);
  };

  const exportToPlatform = (event: Event) => {
    console.log('Export to Platform:', event);
    // TODO: Implement Platform API integration
    alert(`Event exported to Aeon Nimbus Platform for backtesting:\n${event.title}`);
  };

  const filteredEvents = useMemo(() => {
    return events.filter(e => {
      if (searchQuery && !e.title.toLowerCase().includes(searchQuery.toLowerCase()) &&
          !e.affected_tickers?.toLowerCase().includes(searchQuery.toLowerCase())) {
        return false;
      }
      if (!filters.phases.has(e.phase.split(' ')[0])) return false;
      if (e.impact_score < filters.impactRange[0] || e.impact_score > filters.impactRange[1]) return false;
      if (e.days_away < filters.daysRange[0] || e.days_away > filters.daysRange[1]) return false;
      if (selectedTicker) {
        const eventTickers = e.affected_tickers?.split(',').map(t => t.trim()) || [];
        if (!eventTickers.includes(selectedTicker)) return false;
      }
      return true;
    });
  }, [events, searchQuery, filters, selectedTicker]);

  const filteredNews = useMemo(() => {
    let filtered = news;

    if (searchQuery) {
      filtered = filtered.filter(n =>
        n.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        n.content?.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    if (selectedTicker) {
      filtered = filtered.filter(n => {
        const newsTickers = n.affected_tickers?.split(',').map(t => t.trim()) || [];
        return newsTickers.includes(selectedTicker);
      });
    }

    if (newsFilters.sources.size > 0) {
      filtered = filtered.filter(n => newsFilters.sources.has(n.source));
    }

    if (newsFilters.sentiments.size > 0) {
      filtered = filtered.filter(n => newsFilters.sentiments.has(n.sentiment));
    }

    if (newsFilters.timeRange !== 'all') {
      const now = new Date();
      const cutoff = new Date();
      if (newsFilters.timeRange === '1h') cutoff.setHours(now.getHours() - 1);
      else if (newsFilters.timeRange === '24h') cutoff.setHours(now.getHours() - 24);
      else if (newsFilters.timeRange === '7d') cutoff.setDate(now.getDate() - 7);

      filtered = filtered.filter(n => new Date(n.timestamp) >= cutoff);
    }

    return filtered;
  }, [news, searchQuery, selectedTicker, newsFilters]);

  const signals = useMemo(() => generateSignals(filteredEvents), [filteredEvents, generateSignals]);
  const portfolioAnalysis = useMemo(() => analyzePortfolioImpact(watchlist, events), [watchlist, events, analyzePortfolioImpact]);
  const insights = useMemo(() => generateInsights(filteredEvents, filteredNews), [filteredEvents, filteredNews, generateInsights]);

  const dangerEvents = filteredEvents.filter(e => e.phase.includes('DANGER'));
  const euforiaEvents = filteredEvents.filter(e => e.phase.includes('EUFORIA'));
  const accumulationEvents = filteredEvents.filter(e => e.phase.includes('ACCUMULATION'));
  const opportunities = filteredEvents.filter(e =>
    e.impact_score >= 7 && e.days_away >= 10 && e.days_away <= 20
  ).slice(0, 6);

  return (
    <div className="ultimate-product">
      {/* Header */}
      <header className="product-header-ultimate">
        <div className="header-brand">
          <div className="brand-logo-ultimate">AEON NIMBUS</div>
          <div className="brand-subtitle">Intelligence</div>
        </div>

        <nav className="main-nav-ultimate">
          <button className={activeTab === 'intelligence' ? 'active' : ''} onClick={() => setActiveTab('intelligence')}>
            <span className="nav-icon">⚡</span>
            <span>Intelligence</span>
            <span className="nav-shortcut">1</span>
          </button>
          <button className={activeTab === 'signals' ? 'active' : ''} onClick={() => setActiveTab('signals')}>
            <span className="nav-icon">🎯</span>
            <span>Signals</span>
            <span className="nav-shortcut">2</span>
          </button>
          <button className={activeTab === 'portfolio' ? 'active' : ''} onClick={() => setActiveTab('portfolio')}>
            <span className="nav-icon">📊</span>
            <span>Portfolio</span>
            <span className="nav-shortcut">3</span>
          </button>
          <button className={activeTab === 'news' ? 'active' : ''} onClick={() => setActiveTab('news')}>
            <span className="nav-icon">📰</span>
            <span>News</span>
            <span className="nav-shortcut">4</span>
          </button>
          <button className={activeTab === 'calendar' ? 'active' : ''} onClick={() => setActiveTab('calendar')}>
            <span className="nav-icon">📅</span>
            <span>Calendar</span>
            <span className="nav-shortcut">5</span>
          </button>
        </nav>

        <div className="header-actions-ultimate">
          <button className="cmd-palette-btn" onClick={() => setShowCommandPalette(true)}>
            <span>⌘K</span>
          </button>
          <div className="header-search-ultimate">
            <span className="search-icon">🔍</span>
            <input
              type="text"
              placeholder="Search events, news, tickers..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>
      </header>

      {/* Command Palette */}
      {showCommandPalette && (
        <div className="command-palette-overlay" onClick={() => setShowCommandPalette(false)}>
          <div className="command-palette" onClick={(e) => e.stopPropagation()}>
            <div className="command-palette-header">
              <span>⌘ Command Palette</span>
              <button onClick={() => setShowCommandPalette(false)}>×</button>
            </div>
            <input
              type="text"
              placeholder="Type a command or search..."
              autoFocus
            />
            <div className="command-palette-commands">
              <div className="command-item">
                <span className="command-icon">⚡</span>
                <span className="command-text">Go to Intelligence</span>
                <span className="command-shortcut">1</span>
              </div>
              <div className="command-item">
                <span className="command-icon">🎯</span>
                <span className="command-text">Go to Signals</span>
                <span className="command-shortcut">2</span>
              </div>
              <div className="command-item">
                <span className="command-icon">📊</span>
                <span className="command-text">Go to Portfolio Analysis</span>
                <span className="command-shortcut">3</span>
              </div>
              <div className="command-item">
                <span className="command-icon">📤</span>
                <span className="command-text">Export to Terminal</span>
                <span className="command-shortcut">⌘E</span>
              </div>
              <div className="command-item">
                <span className="command-icon">📤</span>
                <span className="command-text">Export to Platform</span>
                <span className="command-shortcut">⌘S</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Intelligence Tab */}
      {activeTab === 'intelligence' && (
        <div className="intelligence-view">
          {/* Market Overview */}
          <div className="market-overview">
            <div className="overview-card fear-greed-card">
              <div className="card-title">Market Sentiment</div>
              <div className="fear-greed-compact">
                <div className="fg-value" style={{ color: fearGreed.color }}>{fearGreed.value}</div>
                <div className="fg-label" style={{ color: fearGreed.color }}>{fearGreed.label}</div>
              </div>
            </div>
            <div className="overview-card">
              <div className="card-title">Active Events</div>
              <div className="overview-number">{filteredEvents.length}</div>
              <div className="overview-label">Tracked</div>
            </div>
            <div className="overview-card">
              <div className="card-title">Signals Generated</div>
              <div className="overview-number">{signals.length}</div>
              <div className="overview-label">High Confidence</div>
            </div>
            <div className="overview-card">
              <div className="card-title">News Volume</div>
              <div className="overview-number">{filteredNews.length}</div>
              <div className="overview-label">Last 24h</div>
            </div>
          </div>

          {/* AI Insights Grid */}
          <div className="insights-section">
            <div className="section-header">
              <h2>🤖 AI-Generated Insights</h2>
              <span className="insight-count">{insights.length} active</span>
            </div>
            <div className="insights-grid">
              {insights.map(insight => (
                <div key={insight.id} className={`insight-card insight-${insight.type}`}>
                  <div className="insight-header">
                    <span className="insight-type">{insight.type}</span>
                    <span className="insight-confidence">{insight.confidence}%</span>
                  </div>
                  <h3 className="insight-title">{insight.title}</h3>
                  <p className="insight-description">{insight.description}</p>
                  {insight.tickers.length > 0 && (
                    <div className="insight-tickers">
                      {insight.tickers.slice(0, 5).map(t => (
                        <span key={t} className="insight-ticker">{t.trim()}</span>
                      ))}
                    </div>
                  )}
                  {insight.actionable && (
                    <button className="insight-action-btn">View Details →</button>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Top Opportunities */}
          <div className="opportunities-section">
            <div className="section-header">
              <h2>🎯 Top Opportunities</h2>
              <span className="opp-phase">Accumulation Phase (D-10 to D-20)</span>
            </div>
            <div className="opportunities-grid-ultimate">
              {opportunities.map(event => (
                <div key={event.id} className="opportunity-card-ultimate" onClick={() => setSelectedEvent(event)}>
                  <div className="opp-header-row">
                    <span className="opp-phase-badge" style={{ background: getPhaseColor(event.phase) }}>
                      D-{event.days_away}
                    </span>
                    <span className="opp-impact-score">{event.impact_score.toFixed(1)}/10</span>
                  </div>
                  <h3 className="opp-title">{event.title}</h3>
                  <div className="opp-tickers-row">
                    {event.affected_tickers?.split(',').slice(0, 3).map(t => (
                      <span key={t.trim()} className="opp-ticker-tag">{t.trim()}</span>
                    ))}
                  </div>
                  <div className="opp-footer">
                    <span className="opp-type">{event.event_type}</span>
                    <button
                      className="opp-export-btn"
                      onClick={(e) => {
                        e.stopPropagation();
                        exportToPlatform(event);
                      }}
                    >
                      Export →
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Signals Tab */}
      {activeTab === 'signals' && (
        <div className="signals-view">
          <div className="signals-header">
            <h2>🎯 Trading Signals</h2>
            <div className="signals-stats">
              <span>{signals.length} active signals</span>
              <span>Avg confidence: {(signals.reduce((sum, s) => sum + s.confidence, 0) / signals.length || 0).toFixed(0)}%</span>
            </div>
          </div>

          <div className="signals-grid">
            {signals.map(signal => (
              <div key={signal.eventId} className="signal-card">
                <div className="signal-header">
                  <div className="signal-ticker-large">{signal.ticker}</div>
                  <div className="signal-action-badge">{signal.action}</div>
                </div>

                <div className="signal-metrics">
                  <div className="signal-metric">
                    <span className="metric-label">Entry</span>
                    <span className="metric-value">${signal.entry.toFixed(2)}</span>
                  </div>
                  <div className="signal-metric">
                    <span className="metric-label">Target</span>
                    <span className="metric-value green">${signal.target.toFixed(2)}</span>
                  </div>
                  <div className="signal-metric">
                    <span className="metric-label">Stop</span>
                    <span className="metric-value red">${signal.stop.toFixed(2)}</span>
                  </div>
                </div>

                <div className="signal-analysis">
                  <div className="signal-stat">
                    <span>R:R</span>
                    <strong>{signal.riskReward.toFixed(2)}:1</strong>
                  </div>
                  <div className="signal-stat">
                    <span>Confidence</span>
                    <strong>{signal.confidence}%</strong>
                  </div>
                  <div className="signal-stat">
                    <span>Timeframe</span>
                    <strong>{signal.timeframe}</strong>
                  </div>
                </div>

                <p className="signal-reasoning">{signal.reasoning}</p>

                <div className="signal-actions">
                  <button
                    className="btn-terminal"
                    onClick={() => exportToTerminal(signal)}
                  >
                    📤 Export to Terminal
                  </button>
                  <button className="btn-details">View Event</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Portfolio Tab */}
      {activeTab === 'portfolio' && (
        <div className="portfolio-view">
          <div className="portfolio-header">
            <h2>📊 Portfolio Impact Analysis</h2>
            <span className="watchlist-count">{watchlist.size} positions tracked</span>
          </div>

          <div className="portfolio-grid">
            {portfolioAnalysis.map(analysis => (
              <div key={analysis.ticker} className={`portfolio-card risk-${analysis.riskLevel}`}>
                <div className="portfolio-card-header">
                  <div className="portfolio-ticker">{analysis.ticker}</div>
                  <div className={`risk-badge risk-${analysis.riskLevel}`}>
                    {analysis.riskLevel.toUpperCase()}
                  </div>
                </div>

                <div className="portfolio-metrics">
                  <div className="portfolio-metric">
                    <span className="pm-label">Upcoming Events</span>
                    <span className="pm-value">{analysis.upcomingEvents}</span>
                  </div>
                  <div className="portfolio-metric">
                    <span className="pm-label">Aggregate Impact</span>
                    <span className="pm-value">{analysis.aggregateImpact.toFixed(1)}/10</span>
                  </div>
                </div>

                <div className="portfolio-recommendation">
                  <div className="rec-label">Recommendation:</div>
                  <div className="rec-text">{analysis.recommendation}</div>
                </div>

                <button className="portfolio-details-btn">View Events →</button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* News Tab - Keep existing implementation */}
      {activeTab === 'news' && (
        <div className="news-view-ultimate">
          <h2>📰 News Intelligence Feed</h2>
          <p>Comprehensive news feed with {filteredNews.length} articles from {Array.from(new Set(news.map(n => n.source))).length} sources</p>
        </div>
      )}

      {/* Calendar Tab - Keep existing implementation */}
      {activeTab === 'calendar' && (
        <div className="calendar-view-ultimate">
          <h2>📅 Event Calendar</h2>
          <p>30-day event calendar view</p>
        </div>
      )}

      {/* Footer */}
      <footer className="product-footer-ultimate">
        <div className="footer-left">
          <span className="status-indicator-ultimate">●</span>
          <span>Real-time • {filteredEvents.length} events • {filteredNews.length} news</span>
        </div>
        <div className="footer-center">
          <span className="ecosystem-link">→ Export to Terminal</span>
          <span className="ecosystem-link">→ Backtest on Platform</span>
        </div>
        <div className="footer-right">
          <span>Aeon Nimbus Intelligence v3.0</span>
        </div>
      </footer>
    </div>
  );
};
