"""
Multi-provider API Gateway with key rotation and usage tracking

Supports:
- Google AI Studio (Gemini 2.5 Flash)
- Groq (Llama 3.3 70B)
- Mistral (Mistral Small)

Features:
- Automatic key rotation on rate limits
- Usage tracking per key
- Fallback between providers
- Request logging
"""

import json
import time
import random
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)


@dataclass
class APIKey:
    """Represents an API key with usage tracking"""
    name: str
    key: str
    provider: str
    requests_today: int = 0
    tokens_today: int = 0
    last_reset: str = ""
    total_requests: int = 0
    total_tokens: int = 0
    is_active: bool = True
    last_error: Optional[str] = None
    last_error_time: Optional[str] = None


@dataclass
class APIResponse:
    """Standardized API response"""
    success: bool
    content: str
    model: str
    provider: str
    key_name: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0
    error: Optional[str] = None


class APIGateway:
    """
    Multi-provider API gateway with intelligent routing
    
    Usage:
        gateway = APIGateway()
        response = gateway.generate("Say hello in 3 words")
        print(response.content)
    """
    
    def __init__(self, secrets_path: Optional[str] = None):
        self.secrets_path = secrets_path or self._find_secrets()
        self.keys: Dict[str, List[APIKey]] = {
            "google": [],
            "groq": [],
            "mistral": []
        }
        self._load_keys()
        
        # Provider priority (order matters for fallback)
        self.provider_priority = ["google", "groq", "mistral"]
        
        # Track current key index per provider
        self.current_key_index: Dict[str, int] = {p: 0 for p in self.provider_priority}
        
        logger.info(f"API Gateway initialized with keys: {self._key_counts()}")
    
    def _find_secrets(self) -> str:
        """Find secrets.json in standard locations"""
        candidates = [
            Path(__file__).parent.parent / "config" / "secrets.json",
            Path.home() / ".hermes" / "credentials" / "api_keys.json",
        ]
        for path in candidates:
            if path.exists():
                return str(path)
        raise FileNotFoundError("No secrets.json found. Copy secrets.example.json and add your keys.")
    
    def _load_keys(self):
        """Load API keys from secrets file"""
        try:
            with open(self.secrets_path) as f:
                data = json.load(f)
        except FileNotFoundError:
            logger.warning(f"Secrets file not found: {self.secrets_path}")
            return
        
        # Google AI Studio (multiple keys)
        google_config = data.get("google_ai_studio", {})
        for key_info in google_config.get("keys", []):
            if key_info.get("key") and key_info["key"] != "YOUR_KEY_HERE":
                self.keys["google"].append(APIKey(
                    name=key_info["name"],
                    key=key_info["key"],
                    provider="google"
                ))
        
        # Groq
        groq_config = data.get("groq", {})
        if groq_config.get("key") and groq_config["key"] != "YOUR_KEY_HERE":
            self.keys["groq"].append(APIKey(
                name="groq_main",
                key=groq_config["key"],
                provider="groq"
            ))
        
        # Mistral
        mistral_config = data.get("mistral", {})
        if mistral_config.get("key") and mistral_config["key"] != "YOUR_KEY_HERE":
            self.keys["mistral"].append(APIKey(
                name="mistral_main",
                key=mistral_config["key"],
                provider="mistral"
            ))
    
    def _key_counts(self) -> str:
        """Return count of keys per provider"""
        return ", ".join(f"{p}: {len(keys)}" for p, keys in self.keys.items() if keys)
    
    def _get_next_key(self, provider: str) -> Optional[APIKey]:
        """Get next available key for a provider (round-robin)"""
        keys = self.keys.get(provider, [])
        active_keys = [k for k in keys if k.is_active]
        
        if not active_keys:
            return None
        
        # Round-robin selection
        idx = self.current_key_index[provider] % len(active_keys)
        key = active_keys[idx]
        self.current_key_index[provider] = (idx + 1) % len(active_keys)
        
        return key
    
    def _call_google(self, prompt: str, key: APIKey, **kwargs) -> APIResponse:
        """Call Google AI Studio API"""
        model = kwargs.get("model", "gemini-2.5-flash")
        max_tokens = kwargs.get("max_tokens", 1000)
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key.key}"
        
        payload = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"maxOutputTokens": max_tokens}
        }).encode()
        
        req = urllib.request.Request(url, data=payload, headers={
            "Content-Type": "application/json"
        })
        
        start_time = time.time()
        try:
            resp = urllib.request.urlopen(req, timeout=30)
            result = json.loads(resp.read())
            
            content = result["candidates"][0]["content"]["parts"][0]["text"]
            usage = result.get("usageMetadata", {})
            
            latency = (time.time() - start_time) * 1000
            
            # Update usage
            key.requests_today += 1
            key.tokens_today += usage.get("totalTokenCount", 0)
            key.total_requests += 1
            key.total_tokens += usage.get("totalTokenCount", 0)
            
            return APIResponse(
                success=True,
                content=content,
                model=model,
                provider="google",
                key_name=key.name,
                input_tokens=usage.get("promptTokenCount", 0),
                output_tokens=usage.get("candidatesTokenCount", 0),
                total_tokens=usage.get("totalTokenCount", 0),
                latency_ms=latency
            )
            
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()[:200]
            key.last_error = f"{e.code}: {error_body}"
            key.last_error_time = datetime.now().isoformat()
            
            if e.code == 429:
                key.is_active = False  # Temporarily disable on rate limit
            
            return APIResponse(
                success=False,
                content="",
                model=model,
                provider="google",
                key_name=key.name,
                error=f"HTTP {e.code}: {error_body}"
            )
    
    def _call_groq(self, prompt: str, key: APIKey, **kwargs) -> APIResponse:
        """Call Groq API (OpenAI-compatible)"""
        model = kwargs.get("model", "llama-3.3-70b-versatile")
        max_tokens = kwargs.get("max_tokens", 1000)
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        
        payload = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens
        }).encode()
        
        req = urllib.request.Request(url, data=payload, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key.key}",
            "User-Agent": "ai-lab/1.0"  # Required for Cloudflare
        })
        
        start_time = time.time()
        try:
            resp = urllib.request.urlopen(req, timeout=30)
            result = json.loads(resp.read())
            
            content = result["choices"][0]["message"]["content"]
            usage = result.get("usage", {})
            
            latency = (time.time() - start_time) * 1000
            
            # Update usage
            key.requests_today += 1
            key.tokens_today += usage.get("total_tokens", 0)
            key.total_requests += 1
            key.total_tokens += usage.get("total_tokens", 0)
            
            return APIResponse(
                success=True,
                content=content,
                model=model,
                provider="groq",
                key_name=key.name,
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
                latency_ms=latency
            )
            
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()[:200]
            key.last_error = f"{e.code}: {error_body}"
            key.last_error_time = datetime.now().isoformat()
            
            if e.code == 429:
                key.is_active = False
            
            return APIResponse(
                success=False,
                content="",
                model=model,
                provider="groq",
                key_name=key.name,
                error=f"HTTP {e.code}: {error_body}"
            )
    
    def _call_mistral(self, prompt: str, key: APIKey, **kwargs) -> APIResponse:
        """Call Mistral API (OpenAI-compatible)"""
        model = kwargs.get("model", "mistral-small-latest")
        max_tokens = kwargs.get("max_tokens", 1000)
        
        url = "https://api.mistral.ai/v1/chat/completions"
        
        payload = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens
        }).encode()
        
        req = urllib.request.Request(url, data=payload, headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key.key}"
        })
        
        start_time = time.time()
        try:
            resp = urllib.request.urlopen(req, timeout=30)
            result = json.loads(resp.read())
            
            content = result["choices"][0]["message"]["content"]
            usage = result.get("usage", {})
            
            latency = (time.time() - start_time) * 1000
            
            # Update usage
            key.requests_today += 1
            key.tokens_today += usage.get("total_tokens", 0)
            key.total_requests += 1
            key.total_tokens += usage.get("total_tokens", 0)
            
            return APIResponse(
                success=True,
                content=content,
                model=model,
                provider="mistral",
                key_name=key.name,
                input_tokens=usage.get("prompt_tokens", 0),
                output_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
                latency_ms=latency
            )
            
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()[:200]
            key.last_error = f"{e.code}: {error_body}"
            key.last_error_time = datetime.now().isoformat()
            
            if e.code == 429:
                key.is_active = False
            
            return APIResponse(
                success=False,
                content="",
                model=model,
                provider="mistral",
                key_name=key.name,
                error=f"HTTP {e.code}: {error_body}"
            )
    
    def generate(self, prompt: str, provider: Optional[str] = None, **kwargs) -> APIResponse:
        """
        Generate content using available API providers
        
        Args:
            prompt: The prompt to send
            provider: Force a specific provider (google/groq/mistral)
            **kwargs: Additional parameters (model, max_tokens, etc.)
        
        Returns:
            APIResponse with the generated content
        """
        providers_to_try = [provider] if provider else self.provider_priority
        
        for prov in providers_to_try:
            key = self._get_next_key(prov)
            if not key:
                logger.warning(f"No available keys for {prov}")
                continue
            
            # Call the appropriate provider
            if prov == "google":
                response = self._call_google(prompt, key, **kwargs)
            elif prov == "groq":
                response = self._call_groq(prompt, key, **kwargs)
            elif prov == "mistral":
                response = self._call_mistral(prompt, key, **kwargs)
            else:
                continue
            
            if response.success:
                logger.info(f"Success via {prov}/{key.name}: {response.total_tokens} tokens, {response.latency_ms:.0f}ms")
                return response
            else:
                logger.warning(f"Failed via {prov}/{key.name}: {response.error}")
                continue
        
        return APIResponse(
            success=False,
            content="",
            model="",
            provider="",
            key_name="",
            error="All providers failed"
        )
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics for all keys"""
        stats = {}
        for provider, keys in self.keys.items():
            stats[provider] = {
                "total_keys": len(keys),
                "active_keys": sum(1 for k in keys if k.is_active),
                "total_requests": sum(k.total_requests for k in keys),
                "total_tokens": sum(k.total_tokens for k in keys),
                "keys": [
                    {
                        "name": k.name,
                        "active": k.is_active,
                        "requests": k.total_requests,
                        "tokens": k.total_tokens,
                        "last_error": k.last_error
                    }
                    for k in keys
                ]
            }
        return stats
    
    def reset_daily_usage(self):
        """Reset daily usage counters (call at midnight)"""
        for keys in self.keys.values():
            for key in keys:
                key.requests_today = 0
                key.tokens_today = 0
                key.last_reset = datetime.now().isoformat()
                key.is_active = True  # Re-enable keys


# Convenience function
_gateway: Optional[APIGateway] = None

def get_gateway() -> APIGateway:
    """Get or create the global API gateway instance"""
    global _gateway
    if _gateway is None:
        _gateway = APIGateway()
    return _gateway

def generate(prompt: str, **kwargs) -> str:
    """Quick generate function - returns content string"""
    gateway = get_gateway()
    response = gateway.generate(prompt, **kwargs)
    if response.success:
        return response.content
    raise Exception(f"API generation failed: {response.error}")
