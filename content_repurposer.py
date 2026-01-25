import anthropic
import openai
import google.generativeai as genai
import os
import re
import time
import json
from typing import Dict, Any
from collections import deque
from dataclasses import dataclass
import logging
from datetime import datetime

# New imports for architecture refactor
from models import RepurposedContent
from prompts import REPURPOSE_PROMPT_TEMPLATE, SYSTEM_PROMPT_DEFAULT

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


@dataclass
class TierConfig:
    #tier config 
    max_input_chars: int
    max_output_tokens: int
    requests_per_minute: int
    requests_per_day: int
    tokens_per_minute: int
    min_delay_seconds: float
    name: str


class RateLimiter:
    """Enhanced rate limiter with token tracking"""
    def __init__(
        self, 
        max_requests_per_minute: int = 15,
        max_requests_per_day: int = 1500,
        max_tokens_per_minute: int = 1_000_000,
        time_window: int = 60
    ):
        self.max_requests_per_minute = max_requests_per_minute
        self.max_requests_per_day = max_requests_per_day
        self.max_tokens_per_minute = max_tokens_per_minute
        self.time_window = time_window
        
        # Per-minute tracking
        self.requests = deque()
        self.tokens = deque()
        
        # Per-day tracking
        self.daily_requests = deque()
        self.daily_reset_time = time.time() + 86400  # 24 hours
        
        self.last_request_time = 0
        self.min_delay = time_window / max_requests_per_minute
        self.total_requests = 0
        self.total_tokens = 0

    
    def _reset_daily_if_needed(self):
        """Reset daily counter if 24 hours have passed"""
        now = time.time()
        if now >= self.daily_reset_time:
            old_count = len(self.daily_requests)
            self.daily_requests.clear()
            self.daily_reset_time = now + 86400
            logger.info("=" * 70)
            logger.info(f"🔄 DAILY COUNTER RESET")
            logger.info(f"   Previous 24h requests: {old_count}")
            logger.info(f"   Next reset: {datetime.fromtimestamp(self.daily_reset_time).strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info("=" * 70)
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough estimate: 4 chars ≈ 1 token"""
        return max(1, len(text) // 4)
    
    def wait_if_needed(self, estimated_input_tokens: int = 0, estimated_output_tokens: int = 0) -> float:
        """Wait if any rate limit would be exceeded. Returns: Time waited in seconds"""
        now = time.time()
        wait_time = 0
        total_estimated_tokens = estimated_input_tokens + estimated_output_tokens
        
        logger.info("-" * 70)
        logger.info("🔍 RATE LIMIT CHECK STARTED")
        logger.info(f"   Estimated input tokens: {estimated_input_tokens:,}")
        
        self._reset_daily_if_needed()
        
        if len(self.daily_requests) >= self.max_requests_per_day:
            time_until_reset = self.daily_reset_time - now
            logger.error(f"❌ DAILY LIMIT REACHED! Reset in {time_until_reset/3600:.1f}h")
            raise Exception(f"Daily rate limit exceeded. Reset in {time_until_reset/3600:.1f}h")
        
        while self.requests and self.requests[0] < now - self.time_window:
            self.requests.popleft()
        
        current_rpm = len(self.requests)
        
        if current_rpm >= self.max_requests_per_minute:
            wait_time = self.time_window - (now - self.requests[0]) + 1.0
            logger.warning(f"⏸️  RATE LIMIT: At minute limit! Waiting {wait_time:.1f}s...")
            time.sleep(wait_time)
            now = time.time()
        
        while self.tokens and self.tokens[0][0] < now - self.time_window:
            self.tokens.popleft()
        
        current_tokens = sum(t[1] for t in self.tokens)
        projected_tokens = current_tokens + total_estimated_tokens
        
        if projected_tokens > self.max_tokens_per_minute:
            if self.tokens:
                oldest_time = self.tokens[0][0]
                token_wait = self.time_window - (now - oldest_time) + 1.0
                logger.warning(f"⏸️  RATE LIMIT: Token limit! Waiting {token_wait:.1f}s...")
                time.sleep(token_wait)
                wait_time += token_wait
                now = time.time()
        
        time_since_last = now - self.last_request_time
        if time_since_last < self.min_delay and self.last_request_time > 0:
            delay = self.min_delay - time_since_last + 0.5
            logger.warning(f"⏸️  RATE LIMIT: Min delay! Waiting {delay:.1f}s...")
            time.sleep(delay)
            wait_time += delay
        
        # Record this request
        request_time = time.time()
        self.requests.append(request_time)
        self.daily_requests.append(request_time)
        self.tokens.append((request_time, total_estimated_tokens))
        self.last_request_time = request_time
        self.total_requests += 1
        self.total_tokens += total_estimated_tokens
        
        logger.info("✅ RATE LIMIT CHECK PASSED")
        return wait_time
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        now = time.time()
        current_minute_tokens = sum(t[1] for t in self.tokens if t[0] > now - self.time_window)
        return {
            "total_requests": self.total_requests,
            "current_minute_requests": len(self.requests),
            "current_minute_tokens": current_minute_tokens,
            "daily_requests": len(self.daily_requests),
            "max_requests_per_minute": self.max_requests_per_minute,
            "max_tokens_per_minute": self.max_tokens_per_minute
        }


class ContentRepurposer:

    TIER_CONFIGS = {
        "gemini_free": TierConfig(
            max_input_chars=2500, max_output_tokens=3000, requests_per_minute=14,
            requests_per_day=1400, tokens_per_minute=900_000, min_delay_seconds=5.0,
            name="Gemini Free"
        ),
        "gemini": TierConfig(
            max_input_chars=30000, max_output_tokens=8192, requests_per_minute=360,
            requests_per_day=10_000, tokens_per_minute=4_000_000, min_delay_seconds=0.2,
            name="Gemini Pro"
        ),
        "claude": TierConfig(
            max_input_chars=100000, max_output_tokens=4096, requests_per_minute=50,
            requests_per_day=10_000, tokens_per_minute=100_000, min_delay_seconds=1.2,
            name="Claude"
        ),
        "openai": TierConfig(
            max_input_chars=50000, max_output_tokens=4096, requests_per_minute=60,
            requests_per_day=10_000, tokens_per_minute=150_000, min_delay_seconds=1.0,
            name="OpenAI"
        )
    }
    
    def __init__(self, provider: str = "claude", api_key: str = None):
        self.provider = provider.lower().strip()
        self.api_key = api_key
        self.is_free_tier = "free" in self.provider.lower()
        # Map gemini_free to gemini_free config, but use generic gemini logic
        config_key = "gemini_free" if self.is_free_tier and "gemini" in self.provider else self.provider
        if "gemini" in config_key and not self.is_free_tier:
             config_key = "gemini"
             
        self.tier_config = self.TIER_CONFIGS.get(config_key, self.TIER_CONFIGS["gemini_free"])
        
        self.rate_limiter = RateLimiter(
            max_requests_per_minute=self.tier_config.requests_per_minute,
            max_requests_per_day=self.tier_config.requests_per_day,
            max_tokens_per_minute=self.tier_config.tokens_per_minute
        )
        
        self._validate_and_init_client()
    
    def _validate_and_init_client(self):
        """Validate API key and initialize the appropriate client"""
        if not self.api_key:
             raise ValueError("API Key is missing")

        try:
            if self.provider == "claude":
                self.model_name = "claude-3-5-sonnet-latest"
                self.client = anthropic.Anthropic(api_key=self.api_key)
            elif self.provider == "openai":
                self.model_name = "gpt-4o"
                openai.api_key = self.api_key
            elif "gemini" in self.provider:
                genai.configure(api_key=self.api_key)
                # Use Flash 2.0 for best performance/cost ratio
                self.model_name = "gemini-2.0-flash" 
                self.model = genai.GenerativeModel(self.model_name)
        except Exception as e:
            logger.error(f"❌ Failed to initialize {self.provider} client: {str(e)}")
            raise ValueError(f"Failed to initialize client: {str(e)}")
    
    def _truncate_content_intelligently(self, content: str) -> str:
        max_chars = self.tier_config.max_input_chars
        if len(content) <= max_chars:
            return content
        
        logger.warning(f"⚠️  Truncating content from {len(content):,} to {max_chars:,} chars")
        mid_point = max_chars // 2
        return content[:mid_point] + "\n...[TRUNCATED]...\n" + content[-mid_point:]
    
    def _call_llm_structured(self, content: str) -> Dict[str, Any]:
        """Generate structured content using robust prompting and JSON validation"""
        
        # 1. Prepare Prompt
        prompt = REPURPOSE_PROMPT_TEMPLATE.format(
            content=content, 
            tier_config_name=self.tier_config.name
        )
        
        # 2. Append JSON Schema enforcement
        # For simplicity across providers, we inject the schema into the prompt key
        schema_instruction = f"\n\nIMPORTANT: You must response with valid JSON that matches this schema:\n{RepurposedContent.model_json_schema()}"
        full_prompt = SYSTEM_PROMPT_DEFAULT + "\n\n" + prompt + schema_instruction
        
        max_tokens = self.tier_config.max_output_tokens
        
        # Rate Limiting
        self.rate_limiter.wait_if_needed(estimated_input_tokens=len(full_prompt)//4, estimated_output_tokens=max_tokens)
        
        response_text = ""
        
        # 3. Call Provider
        try:
            if self.provider == "claude":
                completion = self.client.messages.create(
                    model=self.model_name, max_tokens=max_tokens,
                    messages=[{"role": "user", "content": full_prompt}]
                )
                response_text = completion.content[0].text
                
            elif self.provider == "openai":
                completion = openai.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": full_prompt}],
                    max_tokens=max_tokens, response_format={"type": "json_object"} 
                )
                response_text = completion.choices[0].message.content
                
            elif "gemini" in self.provider:
                # Gemini supports JSON mode natively, but let's stick to prompt engineering for maximum compatibility with Free tier
                result = self.model.generate_content(
                    contents=full_prompt,
                    generation_config={"max_output_tokens": max_tokens, "temperature": 0.5, "response_mime_type": "application/json"}
                )
                response_text = result.text
                
        except Exception as e:
            logger.error(f"API Call Failed: {e}")
            raise e
            
        # 4. Clean and Validate JSON
        try:
            # Remove markdown code blocks if present
            cleaned_json = response_text.replace("```json", "").replace("```", "").strip()
            
            # Validate with Pydantic
            repurposed_content = RepurposedContent.model_validate_json(cleaned_json)
            
            # Convert back to dict for the frontend
            return repurposed_content.model_dump()
            
        except Exception as e:
            logger.error(f"JSON Validation Failed: {e}")
            logger.error(f"Raw Response: {response_text[:500]}...")
            # Fallback (return raw text in core analysis)
            return {
                "core_analysis": {"summary": "Error parsing JSON", "key_points": [], "tone": "Error", "audience": "Error"}, 
                "twitter_thread": {"tweets": []},
                "linkedin_post": {"content": response_text}, # Dump raw text here so user sees something
                "instagram_caption": {"content": "", "hashtags": []},
                "tldr": "Error parsing response."
            }

    def repurpose_content(self, content: str) -> Dict[str, Any]:
        """Main pipeline"""
        content = self._truncate_content_intelligently(content)
        
        # Generate Structured Output
        results = self._call_llm_structured(content)
        
        # Transform for frontend compatibility (Frontend expects flat keys mostly)
        # Our model: {twitter_thread: {tweets: [...]}} -> Frontend wants: {twitter_thread: [...]}
        
        flat_results = {
            "core_analysis": f"**Summary:** {results['core_analysis']['summary']}\n\n**Tone:** {results['core_analysis']['tone']}\n**Audience:** {results['core_analysis']['audience']}",
            "twitter_thread": [t['content'] for t in results['twitter_thread']['tweets']],
            "linkedin_post": results['linkedin_post']['content'],
            "instagram_caption": f"{results['instagram_caption']['content']}\n\n{' '.join(results['instagram_caption']['hashtags'])}",
            "tldr": results['tldr']
        }
        
        return flat_results