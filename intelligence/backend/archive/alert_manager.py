"""
Smart Alert System - Desktop notifications and push alerts
Multiple notification channels with intelligent routing
"""
import sqlite3
import os
import json
from datetime import datetime
from typing import List, Dict, Optional
import subprocess
import platform

DB_PATH = os.path.expanduser("~/.aeon/intelligence.db")

class AlertManager:
    """Intelligent alert system with multiple notification channels"""

    def __init__(self):
        self.init_alert_tables()
        self.platform = platform.system()

    def init_alert_tables(self):
        """Initialize alert system tables"""
        conn = sqlite3.connect(DB_PATH)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS alert_configurations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER DEFAULT 1,
                name TEXT NOT NULL,
                enabled BOOLEAN DEFAULT 1,
                alert_type TEXT NOT NULL,
                conditions_json TEXT NOT NULL,
                channels_json TEXT NOT NULL,
                cooldown_minutes INTEGER DEFAULT 60,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS alert_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_config_id INTEGER,
                event_id INTEGER,
                ticker TEXT,
                alert_type TEXT NOT NULL,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                severity TEXT DEFAULT 'medium',
                channel TEXT NOT NULL,
                sent_at TEXT NOT NULL,
                acknowledged BOOLEAN DEFAULT 0,
                FOREIGN KEY (alert_config_id) REFERENCES alert_configurations(id),
                FOREIGN KEY (event_id) REFERENCES events(id)
            );

            CREATE TABLE IF NOT EXISTS notification_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER DEFAULT 1,
                channel TEXT NOT NULL,
                enabled BOOLEAN DEFAULT 1,
                config_json TEXT,
                updated_at TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_alert_history_sent ON alert_history(sent_at);
        """)
        conn.commit()
        conn.close()

    def send_desktop_notification(self, title: str, message: str, urgency: str = 'normal'):
        """Send native desktop notification"""
        try:
            if self.platform == 'Darwin':  # macOS
                script = f'''
                    display notification "{message}" with title "{title}" sound name "default"
                '''
                subprocess.run(['osascript', '-e', script], check=True)
            elif self.platform == 'Linux':
                subprocess.run([
                    'notify-send',
                    '-u', urgency,
                    title,
                    message
                ], check=True)
            elif self.platform == 'Windows':
                # Windows 10 toast notification
                from win10toast import ToastNotifier
                toaster = ToastNotifier()
                toaster.show_toast(title, message, duration=10)

            return True
        except Exception as e:
            print(f"Desktop notification failed: {e}")
            return False

    def create_alert_config(self, name: str, alert_type: str, conditions: Dict,
                          channels: List[str], cooldown_minutes: int = 60):
        """Create new alert configuration"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO alert_configurations
            (name, alert_type, conditions_json, channels_json, cooldown_minutes, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, alert_type, json.dumps(conditions), json.dumps(channels),
              cooldown_minutes, datetime.now().isoformat()))

        conn.commit()
        config_id = cursor.lastrowid
        conn.close()

        return config_id

    def check_event_alerts(self):
        """Check all events and trigger alerts based on configurations"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row

        # Get active alert configs
        configs = conn.execute("""
            SELECT * FROM alert_configurations WHERE enabled = 1
        """).fetchall()

        alerts_sent = 0

        for config in configs:
            conditions = json.loads(config['conditions_json'])
            channels = json.loads(config['channels_json'])

            # Check events matching conditions
            if config['alert_type'] == 'countdown':
                # Alert when event reaches specific days countdown
                target_days = conditions.get('days_before', [])

                events = conn.execute("""
                    SELECT * FROM events
                    WHERE date(event_date) = date('now', ? || ' days')
                """, (f"+{target_days[0]}",)).fetchall() if target_days else []

                for event in events:
                    # Check cooldown
                    if self.is_in_cooldown(config['id'], event['id']):
                        continue

                    title = f"📅 Event Alert: D-{target_days[0]}"
                    message = f"{event['title']} is {target_days[0]} days away"

                    self.send_alert(
                        config['id'],
                        event['id'],
                        None,
                        config['alert_type'],
                        title,
                        message,
                        'medium',
                        channels
                    )
                    alerts_sent += 1

            elif config['alert_type'] == 'phase_change':
                # Alert when event enters specific phase
                target_phases = conditions.get('phases', [])

                events = conn.execute("""
                    SELECT * FROM events
                    WHERE phase IN ({})
                """.format(','.join('?' * len(target_phases))), target_phases).fetchall()

                for event in events:
                    if self.is_in_cooldown(config['id'], event['id']):
                        continue

                    phase_labels = {
                        'danger': '🔴 DANGER ZONE',
                        'euforia': '🟡 EUFORIA',
                        'accumulation': '🟢 ACCUMULATION',
                        'pre-rumor': '🔵 PRE-RUMOR'
                    }

                    title = f"Phase Alert: {phase_labels.get(event['phase'], event['phase'])}"
                    message = f"{event['title']} has entered {event['phase']} phase"

                    self.send_alert(
                        config['id'],
                        event['id'],
                        None,
                        config['alert_type'],
                        title,
                        message,
                        'high' if event['phase'] == 'danger' else 'medium',
                        channels
                    )
                    alerts_sent += 1

            elif config['alert_type'] == 'ticker':
                # Alert when specific ticker has upcoming event
                tickers = conditions.get('tickers', [])

                for ticker in tickers:
                    events = conn.execute("""
                        SELECT * FROM events
                        WHERE affected_assets LIKE ?
                        AND date(event_date) BETWEEN date('now') AND date('now', '+7 days')
                    """, (f'%{ticker}%',)).fetchall()

                    for event in events:
                        if self.is_in_cooldown(config['id'], event['id']):
                            continue

                        title = f"🎯 {ticker} Event Alert"
                        message = f"{event['title']} - D-{event['days_until']}"

                        self.send_alert(
                            config['id'],
                            event['id'],
                            ticker,
                            config['alert_type'],
                            title,
                            message,
                            'medium',
                            channels
                        )
                        alerts_sent += 1

        conn.close()
        return alerts_sent

    def send_alert(self, config_id: int, event_id: Optional[int], ticker: Optional[str],
                   alert_type: str, title: str, message: str, severity: str, channels: List[str]):
        """Send alert through configured channels"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        for channel in channels:
            if channel == 'desktop':
                urgency = 'critical' if severity == 'high' else 'normal'
                success = self.send_desktop_notification(title, message, urgency)
            elif channel == 'push':
                # Mobile push notification (would integrate with service)
                success = True  # Placeholder
            elif channel == 'email':
                # Email notification
                success = True  # Placeholder
            elif channel == 'webhook':
                # Webhook notification (Slack, Discord, etc)
                success = True  # Placeholder
            else:
                success = False

            if success:
                cursor.execute("""
                    INSERT INTO alert_history
                    (alert_config_id, event_id, ticker, alert_type, title, message, severity, channel, sent_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (config_id, event_id, ticker, alert_type, title, message, severity, channel,
                      datetime.now().isoformat()))

        conn.commit()
        conn.close()

    def is_in_cooldown(self, config_id: int, event_id: int) -> bool:
        """Check if alert is in cooldown period"""
        conn = sqlite3.connect(DB_PATH)

        # Get config cooldown
        config = conn.execute("""
            SELECT cooldown_minutes FROM alert_configurations WHERE id = ?
        """, (config_id,)).fetchone()

        if not config:
            conn.close()
            return False

        cooldown_minutes = config[0]

        # Check last alert
        last_alert = conn.execute("""
            SELECT sent_at FROM alert_history
            WHERE alert_config_id = ? AND event_id = ?
            ORDER BY sent_at DESC LIMIT 1
        """, (config_id, event_id)).fetchone()

        conn.close()

        if not last_alert:
            return False

        last_time = datetime.fromisoformat(last_alert[0])
        minutes_since = (datetime.now() - last_time).total_seconds() / 60

        return minutes_since < cooldown_minutes

    def get_alert_history(self, limit: int = 50):
        """Get recent alert history"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row

        history = conn.execute("""
            SELECT * FROM alert_history
            ORDER BY sent_at DESC LIMIT ?
        """, (limit,)).fetchall()

        conn.close()
        return [dict(h) for h in history]

# ═══════════════════════════════════════════════════════════
# PRESET ALERT CONFIGURATIONS
# ═══════════════════════════════════════════════════════════

def setup_default_alerts():
    """Set up useful default alert configurations"""
    manager = AlertManager()

    alerts = [
        {
            'name': 'Danger Zone Alerts',
            'type': 'phase_change',
            'conditions': {'phases': ['danger']},
            'channels': ['desktop', 'push'],
            'cooldown': 1440  # 24 hours
        },
        {
            'name': 'D-3 Countdown',
            'type': 'countdown',
            'conditions': {'days_before': [3]},
            'channels': ['desktop'],
            'cooldown': 1440
        },
        {
            'name': 'D-1 Warning',
            'type': 'countdown',
            'conditions': {'days_before': [1]},
            'channels': ['desktop', 'push'],
            'cooldown': 1440
        },
        {
            'name': 'FOMC Alerts',
            'type': 'ticker',
            'conditions': {'tickers': ['SPY', 'QQQ', 'TLT']},
            'channels': ['desktop', 'push'],
            'cooldown': 360
        },
    ]

    for alert in alerts:
        alert_id = manager.create_alert_config(
            alert['name'],
            alert['type'],
            alert['conditions'],
            alert['channels'],
            alert['cooldown']
        )
        print(f"✓ Created alert: {alert['name']} (ID: {alert_id})")

if __name__ == "__main__":
    setup_default_alerts()

    # Run alert check
    manager = AlertManager()
    sent = manager.check_event_alerts()
    print(f"\n✓ Checked alerts, sent {sent} notifications")
