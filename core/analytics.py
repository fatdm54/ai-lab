"""
Analytics Tracker - Track engagement, revenue, and growth

Supports:
- Multi-platform analytics
- Revenue tracking
- Growth metrics
- Daily/weekly reports

Usage:
    tracker = AnalyticsTracker()
    tracker.record_engagement("x", "tweet_123", {"likes": 10, "retweets": 5})
    tracker.record_revenue("affiliate", 25.00)
    report = tracker.get_daily_report()
"""

import json
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class EngagementRecord:
    """Record engagement metrics"""
    platform: str
    content_id: str
    metrics: Dict[str, int]
    recorded_at: str = ""
    
    def __post_init__(self):
        if not self.recorded_at:
            self.recorded_at = datetime.now().isoformat()


@dataclass
class RevenueRecord:
    """Record revenue"""
    source: str
    amount: float
    currency: str = "USD"
    description: str = ""
    recorded_at: str = ""
    
    def __post_init__(self):
        if not self.recorded_at:
            self.recorded_at = datetime.now().isoformat()


class AnalyticsTracker:
    """
    Analytics and revenue tracking
    
    Usage:
        tracker = AnalyticsTracker()
        
        # Record engagement
        tracker.record_engagement("x", "tweet_123", {
            "likes": 10,
            "retweets": 5,
            "replies": 2
        })
        
        # Record revenue
        tracker.record_revenue("affiliate", 25.00, "Amazon commission")
        
        # Get reports
        daily = tracker.get_daily_report()
        weekly = tracker.get_weekly_report()
    """
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or str(
            Path(__file__).parent.parent / "data" / "analytics.db"
        )
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS engagement (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    content_id TEXT NOT NULL,
                    metrics TEXT NOT NULL,
                    recorded_at TEXT NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS revenue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source TEXT NOT NULL,
                    amount REAL NOT NULL,
                    currency TEXT DEFAULT 'USD',
                    description TEXT,
                    recorded_at TEXT NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS followers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    count INTEGER NOT NULL,
                    recorded_at TEXT NOT NULL
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    posts_count INTEGER DEFAULT 0,
                    engagement_total INTEGER DEFAULT 0,
                    revenue_total REAL DEFAULT 0,
                    followers_change INTEGER DEFAULT 0,
                    UNIQUE(date, platform)
                )
            """)
    
    def record_engagement(self, platform: str, content_id: str, metrics: Dict[str, int]):
        """Record engagement for a piece of content"""
        record = EngagementRecord(platform, content_id, metrics)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO engagement (platform, content_id, metrics, recorded_at) VALUES (?, ?, ?, ?)",
                (platform, content_id, json.dumps(metrics), record.recorded_at)
            )
        
        logger.debug(f"Recorded engagement for {platform}/{content_id}")
    
    def record_revenue(self, source: str, amount: float, description: str = "", currency: str = "USD"):
        """Record revenue"""
        record = RevenueRecord(source, amount, currency, description)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO revenue (source, amount, currency, description, recorded_at) VALUES (?, ?, ?, ?, ?)",
                (source, amount, currency, description, record.recorded_at)
            )
        
        logger.info(f"Recorded revenue: ${amount} from {source}")
    
    def record_followers(self, platform: str, count: int):
        """Record current follower count"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO followers (platform, count, recorded_at) VALUES (?, ?, ?)",
                (platform, count, datetime.now().isoformat())
            )
    
    def get_engagement_stats(self, platform: Optional[str] = None, days: int = 7) -> Dict[str, Any]:
        """Get engagement statistics"""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            if platform:
                rows = conn.execute(
                    "SELECT metrics FROM engagement WHERE platform = ? AND recorded_at > ?",
                    (platform, cutoff)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT metrics FROM engagement WHERE recorded_at > ?",
                    (cutoff,)
                ).fetchall()
            
            total = {"likes": 0, "retweets": 0, "replies": 0, "views": 0}
            
            for row in rows:
                metrics = json.loads(row[0])
                for key, value in metrics.items():
                    total[key] = total.get(key, 0) + value
            
            return {
                "period_days": days,
                "platform": platform or "all",
                "total_engagement": sum(total.values()),
                "breakdown": total
            }
    
    def get_revenue_stats(self, days: int = 30) -> Dict[str, Any]:
        """Get revenue statistics"""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT source, amount, currency FROM revenue WHERE recorded_at > ?",
                (cutoff,)
            ).fetchall()
            
            by_source = {}
            total = 0
            
            for source, amount, currency in rows:
                if currency != "USD":
                    # Simple conversion (should be improved)
                    amount = amount * 1.0  # Placeholder
                
                by_source[source] = by_source.get(source, 0) + amount
                total += amount
            
            return {
                "period_days": days,
                "total_revenue": total,
                "by_source": by_source,
                "currency": "USD"
            }
    
    def get_follower_stats(self, platform: Optional[str] = None) -> Dict[str, Any]:
        """Get follower statistics"""
        with sqlite3.connect(self.db_path) as conn:
            if platform:
                rows = conn.execute(
                    "SELECT count, recorded_at FROM followers WHERE platform = ? ORDER BY recorded_at DESC LIMIT 10",
                    (platform,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT platform, count, recorded_at FROM followers ORDER BY recorded_at DESC LIMIT 10",
                    ()
                ).fetchall()
            
            if not rows:
                return {"platform": platform or "all", "current": 0, "history": []}
            
            current = rows[0][1] if platform else rows[0][1]
            history = [{"count": r[0] if platform else r[1], "date": r[1] if platform else r[2]} for r in rows]
            
            return {
                "platform": platform or "all",
                "current": current,
                "history": history
            }
    
    def get_daily_report(self, date: Optional[str] = None) -> Dict[str, Any]:
        """Get daily report"""
        target_date = date or datetime.now().strftime("%Y-%m-%d")
        start = f"{target_date}T00:00:00"
        end = f"{target_date}T23:59:59"
        
        with sqlite3.connect(self.db_path) as conn:
            # Posts count
            posts = conn.execute(
                "SELECT platform, COUNT(*) FROM engagement WHERE recorded_at BETWEEN ? AND ? GROUP BY platform",
                (start, end)
            ).fetchall()
            
            # Revenue
            revenue = conn.execute(
                "SELECT SUM(amount) FROM revenue WHERE recorded_at BETWEEN ? AND ?",
                (start, end)
            ).fetchone()[0] or 0
            
            return {
                "date": target_date,
                "posts_by_platform": {p: c for p, c in posts},
                "total_posts": sum(c for _, c in posts),
                "revenue": revenue
            }
    
    def get_weekly_report(self) -> Dict[str, Any]:
        """Get weekly report"""
        end = datetime.now()
        start = end - timedelta(days=7)
        
        engagement = self.get_engagement_stats(days=7)
        revenue = self.get_revenue_stats(days=7)
        
        return {
            "period": f"{start.strftime('%Y-%m-%d')} to {end.strftime('%Y-%m-%d')}",
            "engagement": engagement,
            "revenue": revenue
        }
    
    def get_growth_rate(self, platform: str, days: int = 30) -> float:
        """Calculate follower growth rate"""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                "SELECT count, recorded_at FROM followers WHERE platform = ? ORDER BY recorded_at DESC LIMIT 2",
                (platform,)
            ).fetchall()
            
            if len(rows) < 2:
                return 0.0
            
            current, current_date = rows[0]
            previous, previous_date = rows[1]
            
            if previous == 0:
                return 0.0
            
            return ((current - previous) / previous) * 100


# Quick usage function
def quick_record_revenue(source: str, amount: float):
    """Quick record revenue"""
    tracker = AnalyticsTracker()
    tracker.record_revenue(source, amount)
