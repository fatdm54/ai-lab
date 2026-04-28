"""
Global settings for AI Lab
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)


@dataclass
class APISettings:
    """API configuration"""
    # Rate limits (requests per minute)
    google_rpm: int = 10
    groq_rpm: int = 30
    mistral_rpm: int = 30
    
    # Timeout in seconds
    request_timeout: int = 30
    
    # Max retries on failure
    max_retries: int = 3


@dataclass
class ContentSettings:
    """Content generation settings"""
    # Daily content limits
    x_daily_posts: int = 5
    telegram_daily_posts: int = 3
    youtube_weekly_videos: int = 2
    
    # Content pillars
    content_pillars: list = field(default_factory=lambda: [
        "ai_tools",      # AI 工具推荐
        "income_experiment",  # 收入实验
        "tutorial",      # 教程
        "industry_insight",  # 行业洞察
        "automation",    # 自动化技巧
    ])
    
    # Languages
    primary_language: str = "zh-CN"
    secondary_language: str = "en"


@dataclass
class AnalyticsSettings:
    """Analytics configuration"""
    # Database
    db_path: str = str(DATA_DIR / "analytics.db")
    
    # Tracking intervals
    track_interval_minutes: int = 60
    
    # Report generation
    daily_report: bool = True
    weekly_report: bool = True


@dataclass
class SchedulerSettings:
    """Scheduler configuration"""
    # Content queue
    queue_file: str = str(DATA_DIR / "content_queue.json")
    
    # Post times (24h format)
    x_post_times: list = field(default_factory=lambda: [
        "09:00", "12:00", "18:00", "21:00"
    ])
    
    telegram_post_times: list = field(default_factory=lambda: [
        "10:00", "15:00", "20:00"
    ])


@dataclass
class Settings:
    """Main settings container"""
    api: APISettings = field(default_factory=APISettings)
    content: ContentSettings = field(default_factory=ContentSettings)
    analytics: AnalyticsSettings = field(default_factory=AnalyticsSettings)
    scheduler: SchedulerSettings = field(default_factory=SchedulerSettings)
    
    # Environment
    debug: bool = os.getenv("AI_LAB_DEBUG", "false").lower() == "true"
    verbose: bool = os.getenv("AI_LAB_VERBOSE", "false").lower() == "true"


# Global settings instance
settings = Settings()
