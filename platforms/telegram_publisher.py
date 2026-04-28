"""
Telegram Publisher - Auto-post to Telegram Channel/Bot

Supports:
- Channel posting
- Bot messaging
- Media posting (photos, documents)
- Inline keyboard

Requires:
- Telegram Bot Token (from @BotFather)
- Channel ID (e.g., @channel_name or -100xxxxxxxxxx)

Usage:
    publisher = TelegramPublisher()
    publisher.post("Hello channel!")
    publisher.post_photo("caption", "photo_url")
"""

import json
import time
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass
from datetime import datetime
import logging

import urllib.request
import urllib.error

logger = logging.getLogger(__name__)


@dataclass
class Message:
    """Represents a Telegram message"""
    message_id: Optional[int] = None
    chat_id: Optional[str] = None
    text: str = ""
    date: Optional[int] = None
    edit_date: Optional[int] = None


class TelegramPublisher:
    """
    Telegram publisher using Bot API
    
    Usage:
        publisher = TelegramPublisher()
        
        # Post to channel
        msg = publisher.post("Hello from AI Lab!")
        
        # Post with photo
        msg = publisher.post_photo("Check this out!", "https://example.com/photo.jpg")
        
        # Post with keyboard
        publisher.post(
            "Choose an option:",
            reply_markup={"inline_keyboard": [[{"text": "Option 1", "callback_data": "opt1"}]]}
        )
    """
    
    API_BASE = "https://api.telegram.org"
    
    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        self.bot_token = bot_token or self._load_bot_token()
        self.chat_id = chat_id or self._load_chat_id()
        
        if not self.bot_token:
            logger.warning("Telegram bot token not configured")
    
    def _load_bot_token(self) -> Optional[str]:
        """Load bot token from config"""
        import os
        candidates = [
            os.path.join(os.path.dirname(__file__), "..", "config", "secrets.json"),
            os.path.expanduser("~/.hermes/credentials/api_keys.json"),
        ]
        
        for path in candidates:
            try:
                with open(path) as f:
                    data = json.load(f)
                    telegram = data.get("telegram", {})
                    if telegram.get("bot_token"):
                        return telegram["bot_token"]
            except FileNotFoundError:
                continue
        
        return None
    
    def _load_chat_id(self) -> Optional[str]:
        """Load chat ID from config"""
        import os
        candidates = [
            os.path.join(os.path.dirname(__file__), "..", "config", "secrets.json"),
            os.path.expanduser("~/.hermes/credentials/api_keys.json"),
        ]
        
        for path in candidates:
            try:
                with open(path) as f:
                    data = json.load(f)
                    telegram = data.get("telegram", {})
                    if telegram.get("channel_id"):
                        return telegram["channel_id"]
            except FileNotFoundError:
                continue
        
        return None
    
    def _make_request(self, method: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make API request to Telegram"""
        url = f"{self.API_BASE}/bot{self.bot_token}/{method}"
        
        body = json.dumps(data).encode() if data else None
        
        req = urllib.request.Request(url, data=body, headers={
            "Content-Type": "application/json"
        })
        
        try:
            resp = urllib.request.urlopen(req, timeout=30)
            return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()[:500]
            logger.error(f"Telegram API error {e.code}: {error_body}")
            raise Exception(f"Telegram API error: {e.code} - {error_body}")
    
    def post(
        self,
        text: str,
        chat_id: Optional[str] = None,
        reply_markup: Optional[Dict] = None,
        parse_mode: Optional[str] = "HTML",
        disable_web_page_preview: bool = False
    ) -> Message:
        """
        Post text message to channel/chat
        
        Args:
            text: Message text (supports HTML/Markdown)
            chat_id: Target chat ID (default: configured channel)
            reply_markup: Inline keyboard markup
            parse_mode: HTML or Markdown
            disable_web_page_preview: Disable link previews
        
        Returns:
            Message object
        """
        if not self.bot_token:
            raise Exception("Telegram bot token not configured")
        
        target_chat = chat_id or self.chat_id
        if not target_chat:
            raise Exception("No chat ID specified")
        
        payload = {
            "chat_id": target_chat,
            "text": text,
            "disable_web_page_preview": disable_web_page_preview
        }
        
        if parse_mode:
            payload["parse_mode"] = parse_mode
        
        if reply_markup:
            payload["reply_markup"] = reply_markup
        
        result = self._make_request("sendMessage", payload)
        
        msg_data = result.get("result", {})
        
        return Message(
            message_id=msg_data.get("message_id"),
            chat_id=str(msg_data.get("chat", {}).get("id")),
            text=text,
            date=msg_data.get("date")
        )
    
    def post_photo(
        self,
        caption: str,
        photo: str,
        chat_id: Optional[str] = None,
        parse_mode: Optional[str] = "HTML"
    ) -> Message:
        """
        Post photo with caption
        
        Args:
            caption: Photo caption
            photo: Photo URL or file_id
            chat_id: Target chat ID
            parse_mode: HTML or Markdown
        
        Returns:
            Message object
        """
        if not self.bot_token:
            raise Exception("Telegram bot token not configured")
        
        target_chat = chat_id or self.chat_id
        if not target_chat:
            raise Exception("No chat ID specified")
        
        payload = {
            "chat_id": target_chat,
            "photo": photo,
            "caption": caption
        }
        
        if parse_mode:
            payload["parse_mode"] = parse_mode
        
        result = self._make_request("sendPhoto", payload)
        
        msg_data = result.get("result", {})
        
        return Message(
            message_id=msg_data.get("message_id"),
            chat_id=str(msg_data.get("chat", {}).get("id")),
            text=caption,
            date=msg_data.get("date")
        )
    
    def post_document(
        self,
        caption: str,
        document: str,
        chat_id: Optional[str] = None
    ) -> Message:
        """Post document/file"""
        if not self.bot_token:
            raise Exception("Telegram bot token not configured")
        
        target_chat = chat_id or self.chat_id
        
        payload = {
            "chat_id": target_chat,
            "document": document,
            "caption": caption
        }
        
        result = self._make_request("sendDocument", payload)
        
        msg_data = result.get("result", {})
        
        return Message(
            message_id=msg_data.get("message_id"),
            chat_id=str(msg_data.get("chat", {}).get("id")),
            text=caption,
            date=msg_data.get("date")
        )
    
    def edit_message(
        self,
        message_id: int,
        text: str,
        chat_id: Optional[str] = None,
        parse_mode: Optional[str] = "HTML"
    ) -> Message:
        """Edit an existing message"""
        if not self.bot_token:
            raise Exception("Telegram bot token not configured")
        
        target_chat = chat_id or self.chat_id
        
        payload = {
            "chat_id": target_chat,
            "message_id": message_id,
            "text": text
        }
        
        if parse_mode:
            payload["parse_mode"] = parse_mode
        
        result = self._make_request("editMessageText", payload)
        
        msg_data = result.get("result", {})
        
        return Message(
            message_id=msg_data.get("message_id"),
            chat_id=str(msg_data.get("chat", {}).get("id")),
            text=text,
            edit_date=msg_data.get("edit_date")
        )
    
    def delete_message(self, message_id: int, chat_id: Optional[str] = None) -> bool:
        """Delete a message"""
        if not self.bot_token:
            return False
        
        target_chat = chat_id or self.chat_id
        
        try:
            self._make_request("deleteMessage", {
                "chat_id": target_chat,
                "message_id": message_id
            })
            return True
        except Exception:
            return False
    
    def get_updates(self, offset: Optional[int] = None, limit: int = 100) -> List[Dict]:
        """Get bot updates (for commands/callbacks)"""
        params = {"limit": limit}
        if offset:
            params["offset"] = offset
        
        result = self._make_request("getUpdates", params)
        return result.get("result", [])
    
    def answer_callback(self, callback_query_id: str, text: str = "") -> bool:
        """Answer callback query from inline keyboard"""
        try:
            self._make_request("answerCallbackQuery", {
                "callback_query_id": callback_query_id,
                "text": text
            })
            return True
        except Exception:
            return False


# Quick usage function
def quick_post(text: str) -> Message:
    """Quick post to configured Telegram channel"""
    publisher = TelegramPublisher()
    return publisher.post(text)
