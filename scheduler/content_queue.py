"""
Content Scheduler - Queue and schedule content posting

Supports:
- Content queue management
- Scheduled posting
- Retry logic for failed posts
- Multi-platform scheduling

Usage:
    scheduler = ContentScheduler()
    scheduler.enqueue("Hello world!", platform="x", scheduled_at=datetime.now())
    scheduler.run_pending()
"""

import json
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import logging
import uuid

logger = logging.getLogger(__name__)


class Platform(Enum):
    """Supported platforms"""
    X = "x"
    TELEGRAM = "telegram"
    YOUTUBE = "youtube"


class PostStatus(Enum):
    """Post status"""
    PENDING = "pending"
    QUEUED = "queued"
    POSTING = "posting"
    POSTED = "posted"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class ScheduledPost:
    """Represents a scheduled post"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    content: str = ""
    platform: str = "x"
    status: str = "pending"
    scheduled_at: str = ""
    posted_at: Optional[str] = None
    post_id: Optional[str] = None  # ID from platform
    post_url: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScheduledPost':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class ContentScheduler:
    """
    Content queue and scheduler
    
    Usage:
        scheduler = ContentScheduler()
        
        # Add to queue
        post = scheduler.enqueue(
            content="Hello from AI Lab!",
            platform="x",
            scheduled_at=datetime.now() + timedelta(hours=1)
        )
        
        # Process pending posts
        scheduler.run_pending()
        
        # Check status
        print(scheduler.get_queue_stats())
    """
    
    def __init__(self, queue_file: Optional[str] = None):
        self.queue_file = queue_file or str(
            Path(__file__).parent.parent / "data" / "content_queue.json"
        )
        self.queue: List[ScheduledPost] = []
        self._load_queue()
    
    def _load_queue(self):
        """Load queue from file"""
        try:
            with open(self.queue_file) as f:
                data = json.load(f)
                self.queue = [ScheduledPost.from_dict(item) for item in data]
                logger.info(f"Loaded {len(self.queue)} items from queue")
        except (FileNotFoundError, json.JSONDecodeError):
            self.queue = []
            logger.info("Starting with empty queue")
    
    def _save_queue(self):
        """Save queue to file"""
        Path(self.queue_file).parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.queue_file, 'w') as f:
            json.dump([post.to_dict() for post in self.queue], f, indent=2)
        
        logger.debug(f"Saved {len(self.queue)} items to queue")
    
    def enqueue(
        self,
        content: str,
        platform: str = "x",
        scheduled_at: Optional[datetime] = None,
        metadata: Optional[Dict] = None
    ) -> ScheduledPost:
        """
        Add content to the queue
        
        Args:
            content: Content to post
            platform: Target platform (x, telegram, youtube)
            scheduled_at: When to post (default: now)
            metadata: Additional metadata
        
        Returns:
            ScheduledPost with ID
        """
        post = ScheduledPost(
            content=content,
            platform=platform,
            status="queued",
            scheduled_at=(scheduled_at or datetime.now()).isoformat(),
            metadata=metadata or {}
        )
        
        self.queue.append(post)
        self._save_queue()
        
        logger.info(f"Enqueued post {post.id} for {platform}")
        return post
    
    def get_pending(self, platform: Optional[str] = None) -> List[ScheduledPost]:
        """Get pending posts, optionally filtered by platform"""
        now = datetime.now()
        
        pending = []
        for post in self.queue:
            if post.status not in ("queued", "pending", "retrying"):
                continue
            
            if platform and post.platform != platform:
                continue
            
            scheduled_time = datetime.fromisoformat(post.scheduled_at)
            if scheduled_time <= now:
                pending.append(post)
        
        return pending
    
    def run_pending(self, platform: Optional[str] = None) -> List[ScheduledPost]:
        """
        Process all pending posts
        
        Args:
            platform: Only process specific platform
        
        Returns:
            List of processed posts
        """
        pending = self.get_pending(platform)
        processed = []
        
        for post in pending:
            try:
                post.status = "posting"
                self._save_queue()
                
                # Post based on platform
                if post.platform == "x":
                    result = self._post_to_x(post)
                elif post.platform == "telegram":
                    result = self._post_to_telegram(post)
                elif post.platform == "youtube":
                    result = self._post_to_youtube(post)
                else:
                    raise ValueError(f"Unknown platform: {post.platform}")
                
                post.status = "posted"
                post.posted_at = datetime.now().isoformat()
                post.post_id = result.get("id")
                post.post_url = result.get("url")
                
                logger.info(f"Posted {post.id} to {post.platform}")
                processed.append(post)
                
            except Exception as e:
                logger.error(f"Failed to post {post.id}: {e}")
                
                post.retry_count += 1
                post.error = str(e)
                
                if post.retry_count >= post.max_retries:
                    post.status = "failed"
                    logger.error(f"Post {post.id} failed permanently after {post.retry_count} retries")
                else:
                    post.status = "retrying"
                    # Schedule retry in 5 minutes
                    post.scheduled_at = (datetime.now() + timedelta(minutes=5)).isoformat()
        
        self._save_queue()
        return processed
    
    def _post_to_x(self, post: ScheduledPost) -> Dict[str, Any]:
        """Post to X/Twitter"""
        try:
            from platforms.x_publisher import XPublisher
            publisher = XPublisher()
            tweet = publisher.post(post.content)
            return {"id": tweet.id, "url": tweet.url}
        except Exception as e:
            raise Exception(f"X posting failed: {e}")
    
    def _post_to_telegram(self, post: ScheduledPost) -> Dict[str, Any]:
        """Post to Telegram"""
        try:
            from platforms.telegram_publisher import TelegramPublisher
            publisher = TelegramPublisher()
            msg = publisher.post(post.content)
            return {"id": str(msg.message_id), "url": None}
        except Exception as e:
            raise Exception(f"Telegram posting failed: {e}")
    
    def _post_to_youtube(self, post: ScheduledPost) -> Dict[str, Any]:
        """Post to YouTube (placeholder - needs OAuth)"""
        # YouTube requires OAuth for posting
        # This is a placeholder
        return {"id": "pending_oauth", "url": None}
    
    def cancel(self, post_id: str) -> bool:
        """Cancel a queued post"""
        for post in self.queue:
            if post.id == post_id and post.status in ("queued", "pending"):
                post.status = "cancelled"
                self._save_queue()
                logger.info(f"Cancelled post {post_id}")
                return True
        return False
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        stats = {
            "total": len(self.queue),
            "by_status": {},
            "by_platform": {}
        }
        
        for post in self.queue:
            # By status
            status = post.status
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            
            # By platform
            platform = post.platform
            stats["by_platform"][platform] = stats["by_platform"].get(platform, 0) + 1
        
        return stats
    
    def get_history(self, limit: int = 10) -> List[ScheduledPost]:
        """Get recent posted items"""
        posted = [p for p in self.queue if p.status == "posted"]
        posted.sort(key=lambda x: x.posted_at or "", reverse=True)
        return posted[:limit]
    
    def clear_old(self, days: int = 7):
        """Clear old items from queue"""
        cutoff = datetime.now() - timedelta(days=days)
        
        self.queue = [
            post for post in self.queue
            if post.status in ("queued", "pending", "retrying") or
            (post.posted_at and datetime.fromisoformat(post.posted_at) > cutoff)
        ]
        
        self._save_queue()
        logger.info(f"Cleared old items, {len(self.queue)} remaining")


# Quick usage function
def quick_enqueue(content: str, platform: str = "x") -> ScheduledPost:
    """Quick enqueue a post"""
    scheduler = ContentScheduler()
    return scheduler.enqueue(content, platform)
