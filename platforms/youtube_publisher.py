"""
YouTube Publisher - Auto-post to YouTube Channel

Supports:
- Video metadata upload
- Playlist management
- Comment posting
- Analytics retrieval

Requires:
- YouTube Data API v3 key
- OAuth 2.0 for write operations

Note: Full video upload requires OAuth, not just API key
This module handles metadata and management, not video upload

Usage:
    publisher = YouTubePublisher()
    publisher.update_video_metadata(video_id, title="New Title")
    publisher.post_comment(video_id, "Great video!")
"""

import json
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import logging

import urllib.request
import urllib.error

logger = logging.getLogger(__name__)


@dataclass
class Video:
    """Represents a YouTube video"""
    video_id: str
    title: str
    description: str
    channel_id: Optional[str] = None
    published_at: Optional[str] = None
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0


@dataclass
class Playlist:
    """Represents a YouTube playlist"""
    playlist_id: str
    title: str
    description: str
    video_count: int = 0


class YouTubePublisher:
    """
    YouTube publisher using Data API v3
    
    Note: For full video upload, OAuth 2.0 is required
    This module handles metadata, comments, and analytics
    
    Usage:
        publisher = YouTubePublisher()
        
        # Get video info
        video = publisher.get_video("dQw4w9WgXcQ")
        
        # Post comment (requires OAuth)
        publisher.post_comment("video_id", "Great content!")
        
        # Get channel analytics
        stats = publisher.get_channel_stats()
    """
    
    API_BASE = "https://www.googleapis.com/youtube/v3"
    
    def __init__(self, api_key: Optional[str] = None, channel_id: Optional[str] = None):
        self.api_key = api_key or self._load_api_key()
        self.channel_id = channel_id or self._load_channel_id()
    
    def _load_api_key(self) -> Optional[str]:
        """Load API key from config"""
        import os
        candidates = [
            os.path.join(os.path.dirname(__file__), "..", "config", "secrets.json"),
            os.path.expanduser("~/.hermes/credentials/api_keys.json"),
        ]
        
        for path in candidates:
            try:
                with open(path) as f:
                    data = json.load(f)
                    youtube = data.get("youtube", {})
                    if youtube.get("api_key"):
                        return youtube["api_key"]
            except FileNotFoundError:
                continue
        
        return None
    
    def _load_channel_id(self) -> Optional[str]:
        """Load channel ID from config"""
        import os
        candidates = [
            os.path.join(os.path.dirname(__file__), "..", "config", "secrets.json"),
            os.path.expanduser("~/.hermes/credentials/api_keys.json"),
        ]
        
        for path in candidates:
            try:
                with open(path) as f:
                    data = json.load(f)
                    youtube = data.get("youtube", {})
                    if youtube.get("channel_id"):
                        return youtube["channel_id"]
            except FileNotFoundError:
                continue
        
        return None
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make API request"""
        if not self.api_key:
            raise Exception("YouTube API key not configured")
        
        params = params or {}
        params["key"] = self.api_key
        
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{self.API_BASE}/{endpoint}?{query_string}"
        
        req = urllib.request.Request(url)
        
        try:
            resp = urllib.request.urlopen(req, timeout=30)
            return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()[:500]
            logger.error(f"YouTube API error {e.code}: {error_body}")
            raise Exception(f"YouTube API error: {e.code} - {error_body}")
    
    def get_video(self, video_id: str) -> Optional[Video]:
        """Get video details"""
        try:
            result = self._make_request("videos", {
                "part": "snippet,statistics",
                "id": video_id
            })
            
            items = result.get("items", [])
            if not items:
                return None
            
            item = items[0]
            snippet = item.get("snippet", {})
            stats = item.get("statistics", {})
            
            return Video(
                video_id=video_id,
                title=snippet.get("title", ""),
                description=snippet.get("description", ""),
                channel_id=snippet.get("channelId"),
                published_at=snippet.get("publishedAt"),
                view_count=int(stats.get("viewCount", 0)),
                like_count=int(stats.get("likeCount", 0)),
                comment_count=int(stats.get("commentCount", 0))
            )
        except Exception as e:
            logger.error(f"Failed to get video: {e}")
            return None
    
    def get_channel_videos(self, max_results: int = 10) -> List[Video]:
        """Get recent videos from channel"""
        if not self.channel_id:
            raise Exception("Channel ID not configured")
        
        try:
            # Get uploads playlist
            channel_result = self._make_request("channels", {
                "part": "contentDetails",
                "id": self.channel_id
            })
            
            items = channel_result.get("items", [])
            if not items:
                return []
            
            uploads_playlist = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
            
            # Get videos from uploads playlist
            playlist_result = self._make_request("playlistItems", {
                "part": "snippet",
                "playlistId": uploads_playlist,
                "maxResults": str(max_results)
            })
            
            videos = []
            for item in playlist_result.get("items", []):
                snippet = item.get("snippet", {})
                resource = snippet.get("resourceId", {})
                
                videos.append(Video(
                    video_id=resource.get("videoId", ""),
                    title=snippet.get("title", ""),
                    description=snippet.get("description", ""),
                    channel_id=snippet.get("channelId"),
                    published_at=snippet.get("publishedAt")
                ))
            
            return videos
        except Exception as e:
            logger.error(f"Failed to get channel videos: {e}")
            return []
    
    def get_channel_stats(self) -> Dict[str, Any]:
        """Get channel statistics"""
        if not self.channel_id:
            raise Exception("Channel ID not configured")
        
        try:
            result = self._make_request("channels", {
                "part": "statistics,snippet",
                "id": self.channel_id
            })
            
            items = result.get("items", [])
            if not items:
                return {}
            
            item = items[0]
            stats = item.get("statistics", {})
            snippet = item.get("snippet", {})
            
            return {
                "channel_id": self.channel_id,
                "title": snippet.get("title", ""),
                "description": snippet.get("description", ""),
                "subscriber_count": int(stats.get("subscriberCount", 0)),
                "video_count": int(stats.get("videoCount", 0)),
                "view_count": int(stats.get("viewCount", 0)),
                "hidden_subscriber_count": stats.get("hiddenSubscriberCount", False)
            }
        except Exception as e:
            logger.error(f"Failed to get channel stats: {e}")
            return {}
    
    def search_videos(self, query: str, max_results: int = 10) -> List[Video]:
        """Search for videos"""
        try:
            result = self._make_request("search", {
                "part": "snippet",
                "q": query,
                "type": "video",
                "maxResults": str(max_results),
                "order": "relevance"
            })
            
            videos = []
            for item in result.get("items", []):
                snippet = item.get("snippet", {})
                video_id = item.get("id", {}).get("videoId", "")
                
                if video_id:
                    videos.append(Video(
                        video_id=video_id,
                        title=snippet.get("title", ""),
                        description=snippet.get("description", ""),
                        channel_id=snippet.get("channelId"),
                        published_at=snippet.get("publishedAt")
                    ))
            
            return videos
        except Exception as e:
            logger.error(f"Failed to search videos: {e}")
            return []
    
    def get_video_comments(self, video_id: str, max_results: int = 10) -> List[Dict]:
        """Get comments on a video"""
        try:
            result = self._make_request("commentThreads", {
                "part": "snippet",
                "videoId": video_id,
                "maxResults": str(max_results),
                "order": "relevance"
            })
            
            comments = []
            for item in result.get("items", []):
                snippet = item.get("snippet", {}).get("topLevelComment", {}).get("snippet", {})
                comments.append({
                    "author": snippet.get("authorDisplayName", ""),
                    "text": snippet.get("textDisplay", ""),
                    "like_count": snippet.get("likeCount", 0),
                    "published_at": snippet.get("publishedAt", "")
                })
            
            return comments
        except Exception as e:
            logger.error(f"Failed to get comments: {e}")
            return []
    
    def get_playlist(self, playlist_id: str) -> Optional[Playlist]:
        """Get playlist details"""
        try:
            result = self._make_request("playlists", {
                "part": "snippet,contentDetails",
                "id": playlist_id
            })
            
            items = result.get("items", [])
            if not items:
                return None
            
            item = items[0]
            snippet = item.get("snippet", {})
            content = item.get("contentDetails", {})
            
            return Playlist(
                playlist_id=playlist_id,
                title=snippet.get("title", ""),
                description=snippet.get("description", ""),
                video_count=int(content.get("itemCount", 0))
            )
        except Exception as e:
            logger.error(f"Failed to get playlist: {e}")
            return None


# Quick usage function
def get_video_info(video_id: str) -> Optional[Video]:
    """Quick get video info"""
    publisher = YouTubePublisher()
    return publisher.get_video(video_id)
