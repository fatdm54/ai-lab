"""
X/Twitter Publisher - Auto-post to X/Twitter

Supports:
- Single tweet posting
- Thread creation
- Scheduled posting
- Engagement tracking

Requires:
- X API v2 credentials (api_key, api_secret, access_token, etc.)
- Free tier: 1500 read/month, 50 write/month

Usage:
    publisher = XPublisher()
    publisher.post("Hello world!")
    publisher.post_thread(["Tweet 1", "Tweet 2", "Tweet 3"])
"""

import json
import time
import hashlib
import hmac
import base64
import urllib.parse
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import logging

import urllib.request
import urllib.error

logger = logging.getLogger(__name__)


@dataclass
class Tweet:
    """Represents a tweet"""
    id: Optional[str] = None
    text: str = ""
    created_at: Optional[str] = None
    metrics: Optional[Dict[str, int]] = None
    url: Optional[str] = None


class XPublisher:
    """
    X/Twitter publisher using OAuth 1.0a
    
    Usage:
        publisher = XPublisher()
        
        # Post single tweet
        tweet = publisher.post("Hello from AI Lab!")
        
        # Post thread
        tweets = publisher.post_thread([
            "1/ First tweet",
            "2/ Second tweet",
            "3/ Third tweet"
        ])
    """
    
    API_BASE = "https://api.x.com/2"
    OAUTH_BASE = "https://api.x.com/oauth"
    
    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self._validate_config()
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, str]:
        """Load X API credentials from config"""
        if config_path:
            with open(config_path) as f:
                return json.load(f).get("x_twitter", {})
        
        # Try standard locations
        import os
        candidates = [
            os.path.join(os.path.dirname(__file__), "..", "config", "secrets.json"),
            os.path.expanduser("~/.hermes/credentials/api_keys.json"),
        ]
        
        for path in candidates:
            try:
                with open(path) as f:
                    data = json.load(f)
                    if "x_twitter" in data:
                        return data["x_twitter"]
            except FileNotFoundError:
                continue
        
        return {}
    
    def _validate_config(self):
        """Validate required credentials"""
        required = ["api_key", "api_secret", "access_token", "access_token_secret"]
        missing = [k for k in required if not self.config.get(k)]
        
        if missing:
            logger.warning(f"Missing X API credentials: {missing}")
            logger.warning("X publisher will not work without credentials")
    
    def _generate_oauth_signature(self, method: str, url: str, params: Dict[str, str]) -> str:
        """Generate OAuth 1.0a signature"""
        # Sort parameters
        sorted_params = sorted(params.items())
        
        # Create parameter string
        param_string = "&".join(f"{k}={urllib.parse.quote(str(v), safe='')}" for k, v in sorted_params)
        
        # Create signature base string
        base_string = f"{method.upper()}&{urllib.parse.quote(url, safe='')}&{urllib.parse.quote(param_string, safe='')}"
        
        # Create signing key
        signing_key = f"{urllib.parse.quote(self.config['api_secret'], safe='')}&{urllib.parse.quote(self.config['access_token_secret'], safe='')}"
        
        # Generate signature
        signature = base64.b64encode(
            hmac.new(
                signing_key.encode(),
                base_string.encode(),
                hashlib.sha256
            ).digest()
        ).decode()
        
        return signature
    
    def _generate_oauth_header(self, method: str, url: str, extra_params: Optional[Dict] = None) -> Dict[str, str]:
        """Generate OAuth 1.0a authorization header"""
        oauth_params = {
            "oauth_consumer_key": self.config["api_key"],
            "oauth_nonce": str(int(time.time() * 1000)),
            "oauth_signature_method": "HMAC-SHA256",
            "oauth_timestamp": str(int(time.time())),
            "oauth_token": self.config["access_token"],
            "oauth_version": "1.0"
        }
        
        if extra_params:
            all_params = {**oauth_params, **extra_params}
        else:
            all_params = oauth_params
        
        signature = self._generate_oauth_signature(method, url, all_params)
        oauth_params["oauth_signature"] = signature
        
        # Create header
        header_parts = [f'{k}="{urllib.parse.quote(str(v), safe="")}"' for k, v in sorted(oauth_params.items())]
        return {"Authorization": f"OAuth {', '.join(header_parts)}"}
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated API request"""
        url = f"{self.API_BASE}/{endpoint}"
        
        headers = self._generate_oauth_header(method, url, data)
        headers["Content-Type"] = "application/json"
        
        body = json.dumps(data).encode() if data else None
        
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        
        try:
            resp = urllib.request.urlopen(req, timeout=30)
            return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()[:500]
            logger.error(f"X API error {e.code}: {error_body}")
            raise Exception(f"X API error: {e.code} - {error_body}")
    
    def post(self, text: str) -> Tweet:
        """
        Post a single tweet
        
        Args:
            text: Tweet text (max 280 chars)
        
        Returns:
            Tweet object with ID and URL
        """
        if len(text) > 280:
            raise ValueError(f"Tweet too long: {len(text)} chars (max 280)")
        
        if not self.config.get("api_key"):
            raise Exception("X API credentials not configured")
        
        result = self._make_request("POST", "tweets", {"text": text})
        
        tweet_data = result.get("data", {})
        tweet_id = tweet_data.get("id", "")
        
        return Tweet(
            id=tweet_id,
            text=text,
            url=f"https://x.com/i/status/{tweet_id}"
        )
    
    def post_thread(self, tweets: List[str]) -> List[Tweet]:
        """
        Post a thread of tweets
        
        Args:
            tweets: List of tweet texts
        
        Returns:
            List of Tweet objects
        """
        if not tweets:
            raise ValueError("No tweets provided")
        
        results = []
        reply_to = None
        
        for i, text in enumerate(tweets):
            if len(text) > 280:
                raise ValueError(f"Tweet {i+1} too long: {len(text)} chars")
            
            # Add thread indicator if not first tweet
            if i > 0 and "🧵" not in text:
                text = f"🧵 {i+1}/{len(tweets)} {text}"
            
            # Post tweet
            if reply_to:
                # For replies, we need to add reply parameters
                result = self._make_request("POST", "tweets", {
                    "text": text,
                    "reply": {"in_reply_to_tweet_id": reply_to}
                })
            else:
                result = self._make_request("POST", "tweets", {"text": text})
            
            tweet_data = result.get("data", {})
            tweet_id = tweet_data.get("id", "")
            
            tweet = Tweet(
                id=tweet_id,
                text=text,
                url=f"https://x.com/i/status/{tweet_id}"
            )
            
            results.append(tweet)
            reply_to = tweet_id
            
            # Rate limit: wait between tweets
            if i < len(tweets) - 1:
                time.sleep(2)
        
        return results
    
    def get_tweet(self, tweet_id: str) -> Optional[Tweet]:
        """Get tweet details by ID"""
        try:
            result = self._make_request("GET", f"tweets/{tweet_id}")
            data = result.get("data", {})
            
            return Tweet(
                id=data.get("id"),
                text=data.get("text"),
                created_at=data.get("created_at"),
                metrics=data.get("public_metrics", {})
            )
        except Exception as e:
            logger.error(f"Failed to get tweet: {e}")
            return None
    
    def get_recent_tweets(self, count: int = 10) -> List[Tweet]:
        """Get recent tweets from authenticated user"""
        # This requires user ID - simplified version
        try:
            result = self._make_request("GET", f"users/me/tweets?max_results={count}")
            tweets = []
            
            for data in result.get("data", []):
                tweets.append(Tweet(
                    id=data.get("id"),
                    text=data.get("text"),
                    created_at=data.get("created_at"),
                    metrics=data.get("public_metrics", {})
                ))
            
            return tweets
        except Exception as e:
            logger.error(f"Failed to get tweets: {e}")
            return []
    
    def schedule_post(self, text: str, scheduled_time: datetime) -> Dict[str, Any]:
        """
        Schedule a tweet (requires X Premium)
        
        Note: This is a placeholder - X Premium API is paid
        For free tier, use the scheduler module instead
        """
        # For free tier, we'll queue the post
        return {
            "text": text,
            "scheduled_at": scheduled_time.isoformat(),
            "status": "queued",
            "message": "Free tier: will be posted when scheduler runs"
        }


# Quick usage function
def quick_post(text: str) -> Tweet:
    """Quick post to X"""
    publisher = XPublisher()
    return publisher.post(text)
