"""
Sentiment Analysis Module using FinBERT
Analyzes financial news sentiment for tickers and market events
"""

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np


class SentimentAnalyzer:
    def __init__(self, db_path: str = "~/.aeon/intelligence.db"):
        self.db_path = db_path.replace("~", str(__import__("pathlib").Path.home()))
        self.model_name = "ProsusAI/finbert"

        print("Loading FinBERT model...")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
        self.model.eval()
        print("FinBERT model loaded successfully")

        self._init_db()

    def _init_db(self):
        """Initialize sentiment tracking tables"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Sentiment snapshots table
        c.execute('''
            CREATE TABLE IF NOT EXISTS sentiment_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                positive REAL,
                negative REAL,
                neutral REAL,
                overall_score REAL,
                confidence REAL,
                sample_size INTEGER,
                trend TEXT
            )
        ''')

        # News sentiment table (links news items to sentiment)
        c.execute('''
            CREATE TABLE IF NOT EXISTS news_sentiment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                news_id INTEGER,
                ticker TEXT,
                title TEXT,
                content TEXT,
                positive REAL,
                negative REAL,
                neutral REAL,
                sentiment_label TEXT,
                confidence REAL,
                analyzed_at TEXT,
                FOREIGN KEY (news_id) REFERENCES news_feed(id)
            )
        ''')

        conn.commit()
        conn.close()

    def analyze_text(self, text: str) -> Dict[str, float]:
        """Analyze sentiment of a single text"""
        if not text or len(text.strip()) == 0:
            return {"positive": 0.33, "negative": 0.33, "neutral": 0.34, "confidence": 0.0}

        # Tokenize and analyze
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)

        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)

        # FinBERT outputs: [positive, negative, neutral]
        result = {
            "positive": float(probs[0][0].item()),
            "negative": float(probs[0][1].item()),
            "neutral": float(probs[0][2].item()),
            "confidence": float(probs[0].max().item())
        }

        return result

    def analyze_news_item(self, news_id: int, ticker: str, title: str, content: str) -> Dict:
        """Analyze sentiment of a news item and store it"""
        # Combine title and content for analysis (title weighted more)
        combined_text = f"{title}. {title}. {content[:500]}"

        sentiment = self.analyze_text(combined_text)

        # Determine label
        scores = {"positive": sentiment["positive"],
                  "negative": sentiment["negative"],
                  "neutral": sentiment["neutral"]}
        label = max(scores, key=scores.get)

        # Store in database
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''
            INSERT INTO news_sentiment
            (news_id, ticker, title, content, positive, negative, neutral, sentiment_label, confidence, analyzed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            news_id, ticker, title, content[:500],
            sentiment["positive"], sentiment["negative"], sentiment["neutral"],
            label, sentiment["confidence"],
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

        return {**sentiment, "label": label}

    def analyze_ticker_sentiment(self, ticker: str, hours: int = 24) -> Dict:
        """Aggregate sentiment for a ticker from recent news"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        # Get recent news for ticker
        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()

        c.execute('''
            SELECT title, content FROM news_feed
            WHERE timestamp >= ? AND affected_tickers LIKE ?
            ORDER BY timestamp DESC LIMIT 50
        ''', (cutoff, f'%{ticker}%'))

        news_items = c.fetchall()

        if not news_items:
            return {
                "ticker": ticker,
                "positive": 0.33,
                "negative": 0.33,
                "neutral": 0.34,
                "overall_score": 0.0,
                "confidence": 0.0,
                "sample_size": 0,
                "trend": "insufficient_data"
            }

        # Analyze each news item
        sentiments = []
        for title, content in news_items:
            combined = f"{title}. {content[:500]}"
            sentiment = self.analyze_text(combined)
            sentiments.append(sentiment)

        # Aggregate
        avg_positive = np.mean([s["positive"] for s in sentiments])
        avg_negative = np.mean([s["negative"] for s in sentiments])
        avg_neutral = np.mean([s["neutral"] for s in sentiments])
        avg_confidence = np.mean([s["confidence"] for s in sentiments])

        # Calculate overall score (-1 to 1)
        overall_score = avg_positive - avg_negative

        # Determine trend (compare last 6 hours vs previous 18 hours)
        recent_cutoff = (datetime.now() - timedelta(hours=6)).isoformat()
        c.execute('''
            SELECT title, content FROM news_feed
            WHERE timestamp >= ? AND affected_tickers LIKE ?
        ''', (recent_cutoff, f'%{ticker}%'))
        recent_news = c.fetchall()

        trend = "neutral"
        if len(recent_news) >= 3:
            recent_sentiments = [self.analyze_text(f"{t}. {c[:500]}") for t, c in recent_news]
            recent_score = np.mean([s["positive"] - s["negative"] for s in recent_sentiments])

            if recent_score > overall_score + 0.1:
                trend = "improving"
            elif recent_score < overall_score - 0.1:
                trend = "deteriorating"

        result = {
            "ticker": ticker,
            "positive": float(avg_positive),
            "negative": float(avg_negative),
            "neutral": float(avg_neutral),
            "overall_score": float(overall_score),
            "confidence": float(avg_confidence),
            "sample_size": len(sentiments),
            "trend": trend,
            "timestamp": datetime.now().isoformat()
        }

        # Store snapshot
        c.execute('''
            INSERT INTO sentiment_snapshots
            (ticker, timestamp, positive, negative, neutral, overall_score, confidence, sample_size, trend)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            ticker, result["timestamp"],
            result["positive"], result["negative"], result["neutral"],
            result["overall_score"], result["confidence"], result["sample_size"], result["trend"]
        ))

        conn.commit()
        conn.close()

        return result

    def analyze_market_sentiment(self, tickers: List[str] = None) -> Dict:
        """Aggregate sentiment across multiple tickers or entire market"""
        if tickers is None:
            # Default to major indices and popular stocks
            tickers = ["SPY", "QQQ", "AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "GOOGL", "META"]

        sentiments = {}
        for ticker in tickers:
            sentiments[ticker] = self.analyze_ticker_sentiment(ticker, hours=24)

        # Calculate market aggregate
        valid_sentiments = [s for s in sentiments.values() if s["sample_size"] > 0]

        if not valid_sentiments:
            return {
                "market_sentiment": "neutral",
                "overall_score": 0.0,
                "confidence": 0.0,
                "tickers": sentiments
            }

        market_score = np.mean([s["overall_score"] for s in valid_sentiments])
        market_confidence = np.mean([s["confidence"] for s in valid_sentiments])

        # Classify market sentiment
        if market_score > 0.2:
            market_sentiment = "bullish"
        elif market_score < -0.2:
            market_sentiment = "bearish"
        else:
            market_sentiment = "neutral"

        return {
            "market_sentiment": market_sentiment,
            "overall_score": float(market_score),
            "confidence": float(market_confidence),
            "timestamp": datetime.now().isoformat(),
            "tickers": sentiments
        }

    def get_sentiment_history(self, ticker: str, days: int = 7) -> List[Dict]:
        """Get historical sentiment for a ticker"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        c.execute('''
            SELECT timestamp, positive, negative, neutral, overall_score, confidence, sample_size, trend
            FROM sentiment_snapshots
            WHERE ticker = ? AND timestamp >= ?
            ORDER BY timestamp DESC
        ''', (ticker, cutoff))

        rows = c.fetchall()
        conn.close()

        return [{
            "timestamp": row[0],
            "positive": row[1],
            "negative": row[2],
            "neutral": row[3],
            "overall_score": row[4],
            "confidence": row[5],
            "sample_size": row[6],
            "trend": row[7]
        } for row in rows]


if __name__ == "__main__":
    print("Initializing Sentiment Analyzer with FinBERT...")
    analyzer = SentimentAnalyzer()

    # Test with sample text
    test_text = "Apple stock surges to new all-time high after strong earnings beat expectations"
    result = analyzer.analyze_text(test_text)
    print(f"\nTest analysis: {test_text}")
    print(f"Sentiment: {result}")

    # Analyze specific ticker (if news exists)
    print("\n\nAnalyzing AAPL sentiment from recent news...")
    ticker_sentiment = analyzer.analyze_ticker_sentiment("AAPL", hours=168)  # 7 days
    print(f"AAPL Sentiment: {ticker_sentiment}")

    print("\n✅ Sentiment Analyzer initialized and ready")
