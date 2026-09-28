"""
Enhanced LangChain Agent for Natural Language Intelligence Interface
Powered by Claude with specialized tools for market intelligence
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os

from langchain_anthropic import ChatAnthropic
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory

# Import our backend modules
import sys
sys.path.append(os.path.dirname(__file__))

from portfolio_tracker import PortfolioTracker
from alert_manager import AlertManager
from pattern_analyzer import PatternAnalyzer


class IntelligenceAgent:
    """Natural language interface for Aeon Nimbus Intelligence"""

    def __init__(self, db_path: str = "~/.aeon/intelligence.db"):
        self.db_path = db_path.replace("~", str(__import__("pathlib").Path.home()))

        # Initialize backend services
        self.portfolio = PortfolioTracker(db_path)
        self.alerts = AlertManager(db_path)
        self.patterns = PatternAnalyzer(db_path)

        # Initialize LangChain components
        self.llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            temperature=0.7,
            api_key=os.environ.get("ANTHROPIC_API_KEY", "")
        )

        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )

        # Define tools
        self.tools = self._create_tools()

        # Create agent
        self.agent = self._create_agent()
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            max_iterations=5
        )

    def _create_tools(self) -> List[Tool]:
        """Create specialized tools for the agent"""
        return [
            Tool(
                name="get_upcoming_events",
                func=self._get_upcoming_events,
                description="Get upcoming market events. Input: number of days ahead (default 7)"
            ),
            Tool(
                name="analyze_ticker",
                func=self._analyze_ticker,
                description="Complete analysis of a ticker including events, sentiment, patterns. Input: ticker symbol"
            ),
            Tool(
                name="check_portfolio",
                func=self._check_portfolio,
                description="Check portfolio exposure to upcoming events. No input needed."
            ),
            Tool(
                name="search_news",
                func=self._search_news,
                description="Search recent news by keyword or ticker. Input: search query"
            ),
            Tool(
                name="get_pattern",
                func=self._get_pattern,
                description="Get historical pattern for ticker and event type. Input: 'TICKER,EVENT_TYPE'"
            ),
            Tool(
                name="get_phase_recommendation",
                func=self._get_phase_recommendation,
                description="Get trading recommendation based on D-X phase. Input: ticker symbol"
            ),
            Tool(
                name="market_overview",
                func=self._market_overview,
                description="Get current market sentiment and major events. No input needed."
            )
        ]

    def _create_agent(self):
        """Create ReAct agent with custom prompt"""
        template = """You are the Aeon Nimbus Intelligence assistant, an expert in market events and event-driven trading.

You help users understand upcoming market events, analyze ticker exposure, and provide actionable insights based on the D-X countdown system:
- DANGER ZONE (D-0 to D-2): Event happening, volatility high
- EUFORIA (D-3 to D-9): Peak speculation, consider taking profits
- ACCUMULATION (D-10 to D-20): Buy the rumor phase
- PRE-RUMOR (D-20+): Early positioning

You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}"""

        prompt = PromptTemplate.from_template(template)

        return create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )

    # Tool implementations

    def _get_upcoming_events(self, days: str = "7") -> str:
        """Get upcoming events"""
        try:
            days = int(days)
        except:
            days = 7

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        cutoff = (datetime.now() + timedelta(days=days)).isoformat()

        c.execute('''
            SELECT title, date, event_type, phase, affected_tickers
            FROM events
            WHERE date <= ? AND date >= ?
            ORDER BY date ASC LIMIT 20
        ''', (cutoff, datetime.now().isoformat()))

        events = c.fetchall()
        conn.close()

        if not events:
            return f"No events found in next {days} days"

        result = f"Upcoming events in next {days} days:\n\n"
        for title, date, event_type, phase, tickers in events:
            days_away = (datetime.fromisoformat(date) - datetime.now()).days
            result += f"• D-{days_away}: {title} ({event_type}) - Phase: {phase}\n"
            if tickers:
                result += f"  Tickers: {tickers}\n"

        return result

    def _analyze_ticker(self, ticker: str) -> str:
        """Complete ticker analysis"""
        ticker = ticker.upper().strip()

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Get upcoming events
        c.execute('''
            SELECT title, date, event_type, phase
            FROM events
            WHERE affected_tickers LIKE ? AND date >= ?
            ORDER BY date ASC LIMIT 5
        ''', (f'%{ticker}%', datetime.now().isoformat()))

        events = c.fetchall()

        result = f"Analysis for {ticker}:\n\n"

        if events:
            result += "Upcoming Events:\n"
            for title, date, event_type, phase in events:
                days_away = (datetime.fromisoformat(date) - datetime.now()).days
                result += f"• D-{days_away}: {title} - {phase}\n"
        else:
            result += "No upcoming events found\n"

        # Check if in portfolio
        c.execute('SELECT quantity, entry_price FROM portfolio_positions WHERE ticker = ?', (ticker,))
        position = c.fetchone()

        if position:
            result += f"\nPortfolio: {position[0]} shares at ${position[1]}\n"

        conn.close()
        return result

    def _check_portfolio(self, _: str = "") -> str:
        """Check portfolio exposure"""
        summary = self.portfolio.get_portfolio_summary()

        if not summary["positions"]:
            return "Portfolio is empty"

        result = "Portfolio Summary:\n\n"
        for pos in summary["positions"]:
            result += f"• {pos['ticker']}: {pos['quantity']} shares @ ${pos['entry_price']}\n"
            result += f"  P&L: ${pos['unrealized_pnl']:.2f}\n"
            if pos['events']:
                result += f"  Upcoming events: {len(pos['events'])}\n"

        result += f"\nTotal Portfolio Value: ${summary['total_value']:.2f}\n"
        result += f"Total P&L: ${summary['total_pnl']:.2f}\n"

        return result

    def _search_news(self, query: str) -> str:
        """Search recent news"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        cutoff = (datetime.now() - timedelta(hours=24)).isoformat()

        c.execute('''
            SELECT title, source, timestamp, affected_tickers
            FROM news_feed
            WHERE (title LIKE ? OR content LIKE ?) AND timestamp >= ?
            ORDER BY timestamp DESC LIMIT 10
        ''', (f'%{query}%', f'%{query}%', cutoff))

        news = c.fetchall()
        conn.close()

        if not news:
            return f"No recent news found for: {query}"

        result = f"Recent news about '{query}':\n\n"
        for title, source, timestamp, tickers in news:
            time_str = datetime.fromisoformat(timestamp).strftime("%H:%M")
            result += f"• [{time_str}] {title} ({source})\n"
            if tickers:
                result += f"  Tickers: {tickers}\n"

        return result

    def _get_pattern(self, input_str: str) -> str:
        """Get historical pattern"""
        try:
            ticker, event_type = input_str.split(',')
            ticker = ticker.strip().upper()
            event_type = event_type.strip()
        except:
            return "Invalid input. Use format: TICKER,EVENT_TYPE"

        pattern = self.patterns.analyze_historical_pattern(ticker, event_type)

        if not pattern or pattern["sample_size"] == 0:
            return f"No historical pattern found for {ticker} {event_type}"

        result = f"Historical Pattern: {ticker} around {event_type}\n\n"
        result += f"Sample size: {pattern['sample_size']} events\n"
        result += f"Average move D-10 to D-1: {pattern['avg_pre_event_move']:.2f}%\n"
        result += f"Average move D-1 to D+1: {pattern['avg_event_move']:.2f}%\n"
        result += f"Win rate: {pattern['win_rate']:.1f}%\n"

        return result

    def _get_phase_recommendation(self, ticker: str) -> str:
        """Get recommendation based on phase"""
        ticker = ticker.upper().strip()

        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''
            SELECT title, date, phase, recommendation
            FROM events
            WHERE affected_tickers LIKE ? AND date >= ?
            ORDER BY date ASC LIMIT 1
        ''', (f'%{ticker}%', datetime.now().isoformat()))

        event = c.fetchone()
        conn.close()

        if not event:
            return f"No upcoming events for {ticker}"

        title, date, phase, rec = event
        days_away = (datetime.fromisoformat(date) - datetime.now()).days

        return f"{ticker} next event: {title} (D-{days_away})\nPhase: {phase}\nRecommendation: {rec}"

    def _market_overview(self, _: str = "") -> str:
        """Get market overview"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Count events in next 7 days
        cutoff = (datetime.now() + timedelta(days=7)).isoformat()
        c.execute('SELECT COUNT(*) FROM events WHERE date >= ? AND date <= ?',
                  (datetime.now().isoformat(), cutoff))
        event_count = c.fetchone()[0]

        # Get major events
        c.execute('''
            SELECT title, date, event_type
            FROM events
            WHERE date >= ? AND (event_type = 'earnings' OR event_type = 'macro')
            ORDER BY date ASC LIMIT 5
        ''', (datetime.now().isoformat(),))

        major_events = c.fetchall()
        conn.close()

        result = f"Market Overview:\n\n"
        result += f"Events in next 7 days: {event_count}\n\n"

        if major_events:
            result += "Major upcoming events:\n"
            for title, date, event_type in major_events:
                days_away = (datetime.fromisoformat(date) - datetime.now()).days
                result += f"• D-{days_away}: {title} ({event_type})\n"

        return result

    async def chat(self, message: str) -> str:
        """Process natural language query"""
        try:
            response = await self.agent_executor.ainvoke({"input": message})
            return response["output"]
        except Exception as e:
            return f"I encountered an error: {str(e)}"

    def chat_sync(self, message: str) -> str:
        """Synchronous version of chat"""
        try:
            response = self.agent_executor.invoke({"input": message})
            return response["output"]
        except Exception as e:
            return f"I encountered an error: {str(e)}"


if __name__ == "__main__":
    import asyncio

    print("Initializing Intelligence Agent with LangChain...")
    agent = IntelligenceAgent()

    # Test queries
    test_queries = [
        "What events are coming up in the next 7 days?",
        "Analyze AAPL",
        "What's the market overview?",
    ]

    print("\nTesting agent with sample queries...\n")
    for query in test_queries:
        print(f"Q: {query}")
        response = agent.chat_sync(query)
        print(f"A: {response}\n")

    print("✅ Intelligence Agent ready for natural language queries")
