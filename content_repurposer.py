import anthropic
import openai
import google.generativeai as genai
import os
import re
import time
from typing import Dict, Any
from collections import deque
from dataclasses import dataclass
import logging
from datetime import datetime


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
    """Enhanced rate limiter with token tracking and daily limits"""
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
        logger.info(f"   Estimated output tokens: {estimated_output_tokens:,}")
        logger.info(f"   Total estimated tokens: {total_estimated_tokens:,}")
        
        self._reset_daily_if_needed()
        
        # Check 1: Daily Request Limit
        logger.info(f"   [CHECK 1/4] Daily request limit...")
        if len(self.daily_requests) >= self.max_requests_per_day:
            time_until_reset = self.daily_reset_time - now
            logger.error("=" * 70)
            logger.error(f"❌ DAILY LIMIT REACHED!")
            logger.error(f"   Current: {len(self.daily_requests)} / {self.max_requests_per_day}")
            logger.error(f"   Reset in: {time_until_reset/3600:.2f} hours")
            logger.error("=" * 70)
            raise Exception(f"Daily rate limit exceeded. Reset in {time_until_reset/3600:.1f}h")
        logger.info(f"   ✓ Daily: {len(self.daily_requests)}/{self.max_requests_per_day} requests")
        
        # Check 2: Per-Minute Request Limit
        logger.info(f"   [CHECK 2/4] Per-minute request limit...")
        while self.requests and self.requests[0] < now - self.time_window:
            self.requests.popleft()
        
        current_rpm = len(self.requests)
        logger.info(f"   Current RPM: {current_rpm}/{self.max_requests_per_minute}")
        
        if current_rpm >= self.max_requests_per_minute:
            wait_time = self.time_window - (now - self.requests[0]) + 1.0
            logger.warning("⏸️  RATE LIMIT: At minute limit!")
            logger.warning(f"Current: {current_rpm}/{self.max_requests_per_minute} requests")
            logger.warning(f"Waiting {wait_time:.1f}s for window to expire...")
            time.sleep(wait_time)
            now = time.time()
            logger.info(f"   ✓ Wait completed, continuing...")
        else:
            logger.info(f"   ✓ RPM: {current_rpm}/{self.max_requests_per_minute} - OK")
        
        # Check 3: Token Per Minute Limit
        logger.info(f"   [CHECK 3/4] Token per minute limit...")
        while self.tokens and self.tokens[0][0] < now - self.time_window:
            self.tokens.popleft()
        
        current_tokens = sum(t[1] for t in self.tokens)
        projected_tokens = current_tokens + total_estimated_tokens
        
        logger.info(f"   Current TPM: {current_tokens:,}/{self.max_tokens_per_minute:,}")
        logger.info(f"   After this call: {projected_tokens:,}/{self.max_tokens_per_minute:,}")
        
        if projected_tokens > self.max_tokens_per_minute:
            if self.tokens:
                oldest_time = self.tokens[0][0]
                token_wait = self.time_window - (now - oldest_time) + 1.0
                logger.warning("⏸️  RATE LIMIT: Token limit would be exceeded!")
                logger.warning(f"   Current: {current_tokens:,} tokens")
                logger.warning(f"   Would be: {projected_tokens:,}/{self.max_tokens_per_minute:,}")
                logger.warning(f"   ⏳ Waiting {token_wait:.1f}s for token window reset...")
                time.sleep(token_wait)
                wait_time += token_wait
                now = time.time()
                logger.info(f"   ✓ Wait completed, continuing...")
        else:
            logger.info(f"   ✓ Tokens: {projected_tokens:,}/{self.max_tokens_per_minute:,} - OK")
        
        # Check 4: Minimum Delay Between Requests
        logger.info(f"   [CHECK 4/4] Minimum delay between requests...")
        time_since_last = now - self.last_request_time
        
        if self.last_request_time > 0:
            logger.info(f"   Time since last request: {time_since_last:.2f}s")
            logger.info(f"   Minimum required: {self.min_delay:.2f}s")
        
        if time_since_last < self.min_delay and self.last_request_time > 0:
            delay = self.min_delay - time_since_last + 0.5
            logger.warning(f"⏸️  RATE LIMIT: Minimum delay not met!")
            logger.warning(f"   ⏳ Enforcing {delay:.1f}s delay...")
            time.sleep(delay)
            wait_time += delay
        else:
            logger.info(f"   ✓ Delay check passed")
        
        # Record this request
        request_time = time.time()
        self.requests.append(request_time)
        self.daily_requests.append(request_time)
        self.tokens.append((request_time, total_estimated_tokens))
        self.last_request_time = request_time
        self.total_requests += 1
        self.total_tokens += total_estimated_tokens
        
        logger.info("✅ RATE LIMIT CHECK PASSED")
        if wait_time > 0:
            logger.info(f"   Total wait time: {wait_time:.2f}s")
        logger.info(f"   Request #{self.total_requests} approved")
        logger.info("-" * 70)
        
        return wait_time
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        now = time.time()
        current_minute_tokens = sum(t[1] for t in self.tokens if t[0] > now - self.time_window)
        
        stats = {
            "total_requests": self.total_requests,
            "total_tokens": self.total_tokens,
            "current_minute_requests": len(self.requests),
            "current_minute_tokens": current_minute_tokens,
            "daily_requests": len(self.daily_requests),
            "max_requests_per_minute": self.max_requests_per_minute,
            "max_requests_per_day": self.max_requests_per_day,
            "max_tokens_per_minute": self.max_tokens_per_minute,
            "time_until_daily_reset": max(0, self.daily_reset_time - now)
        }
        
        logger.info("=" * 70)
        logger.info("📊 RATE LIMITER STATISTICS")
        logger.info(f"   Total requests (session): {stats['total_requests']}")
        logger.info(f"   Total tokens (session): {stats['total_tokens']:,}")
        logger.info(f"   Current minute: {stats['current_minute_requests']}/{stats['max_requests_per_minute']} requests")
        logger.info(f"   Current minute: {stats['current_minute_tokens']:,}/{stats['max_tokens_per_minute']:,} tokens")
        logger.info(f"   Daily usage: {stats['daily_requests']}/{stats['max_requests_per_day']} requests")
        logger.info(f"   Daily reset in: {stats['time_until_daily_reset']/3600:.2f} hours")
        logger.info("=" * 70)
        
        return stats


class ContentRepurposer:

    TIER_CONFIGS = {
        "gemini_free": TierConfig(
            max_input_chars=2500, max_output_tokens=1500, requests_per_minute=14,
            requests_per_day=1400, tokens_per_minute=900_000, min_delay_seconds=5.0,
            name="Gemini Free"
        ),
        "gemini": TierConfig(
            max_input_chars=30000, max_output_tokens=2048, requests_per_minute=360,
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
        self.tier_config = self.TIER_CONFIGS.get(self.provider, self.TIER_CONFIGS["gemini_free"])
        self.rate_limiter = RateLimiter(
            max_requests_per_minute=self.tier_config.requests_per_minute,
            max_requests_per_day=self.tier_config.requests_per_day,
            max_tokens_per_minute=self.tier_config.tokens_per_minute,
            time_window=60
        )
        
        self._validate_and_init_client()
        logger.info("✅ Initialization complete!\n")
    
    def _validate_and_init_client(self):
        """Validate API key and initialize the appropriate client"""
        logger.info("\n🔐 VALIDATING API KEY")
        
        validation_rules = {
            "openai": ("sk-", "OpenAI"), "claude": ("sk-ant-", "Claude"),
            "gemini": ("AIza", "Gemini"), "gemini_free": ("AIza", "Gemini")
        }
        
        if self.provider not in validation_rules:
            logger.error(f"❌ Unsupported provider: {self.provider}")
            raise ValueError(f"❌ Unsupported provider: {self.provider}")
        
        prefix, name = validation_rules[self.provider]
        
        if not self.api_key or not isinstance(self.api_key, str):
            logger.error(f"❌ Invalid {name} API key")
            raise ValueError(f"❌ Invalid {name} API key: Key must be a non-empty string")
        
        if not self.api_key.startswith(prefix):
            logger.error(f"❌ Invalid {name} API key: Must start with '{prefix}'")
            raise ValueError(f"❌ Invalid {name} API key: Must start with '{prefix}'")
        
        logger.info(f"   ✓ API key format valid for {name}")
        logger.info(f"   Key prefix: {self.api_key[:10]}...")
        
        try:
            if self.provider == "claude":
                self.model_name = "claude-3-5-sonnet-latest"
                self.client = anthropic.Anthropic(api_key=self.api_key)
                logger.info(f"   ✓ Claude client initialized - Model: {self.model_name}")
            elif self.provider == "openai":
                self.model_name = "gpt-4o"
                openai.api_key = self.api_key
                logger.info(f"   ✓ OpenAI client initialized - Model: {self.model_name}")
            elif "gemini" in self.provider:
                genai.configure(api_key=self.api_key)
                model_name = "gemini-1.5-flash" if self.is_free_tier else "gemini-2.0-flash"
                self.model = genai.GenerativeModel(model_name)
                logger.info(f"   ✓ Gemini client initialized - Model: {model_name}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize {name} client: {str(e)}")
            raise ValueError(f"❌ Failed to initialize {name} client: {str(e)}")
    
    def _truncate_content_intelligently(self, content: str) -> str:
        """Intelligently truncate content to fit tier limits"""
        max_chars = self.tier_config.max_input_chars
        
        if len(content) <= max_chars:
            logger.info(f"   Content size OK: {len(content):,} chars (max: {max_chars:,})")
            return content
        
        logger.warning("⚠️  CONTENT TRUNCATION NEEDED")
        logger.warning(f"   Original: {len(content):,} chars | Max: {max_chars:,} chars")
        
        first_ratio, last_ratio = 0.65, 0.35
        first_part_size = int(max_chars * first_ratio)
        last_part_size = int(max_chars * last_ratio)
        
        truncated = f"{content[:first_part_size]}\n\n[... {len(content) - first_part_size - last_part_size:,} characters truncated ...]\n\n{content[-last_part_size:]}"
        
        if len(truncated) > max_chars:
            truncated = truncated[:max_chars]
        
        logger.info(f"   ✓ Truncated to: {len(truncated):,} chars")
        return truncated
    
    def _estimate_token_count(self, text: str) -> int:
        """Rough estimate of token count (4 chars ≈ 1 token)"""
        return max(1, len(text) // 4)
    
    def _call_llm(self, prompt: str, max_tokens: int = 2000, temperature: float = 0.7) -> str:
        """Unified LLM caller with enhanced rate limiting."""
        logger.info("\n" + "=" * 70)
        logger.info("🤖 API CALL INITIATED")
        logger.info("=" * 70)
        logger.info(f"Provider: {self.provider.upper()} | Max tokens: {max_tokens} | Temp: {temperature}")
        logger.info(f"Prompt length: {len(prompt):,} chars")
        
        max_attempts = 2
        attempt = 0
        
        max_prompt_chars = self.tier_config.max_input_chars
        if len(prompt) > max_prompt_chars:
            logger.warning(f"⚠️  Prompt truncated from {len(prompt):,} to {max_prompt_chars:,} chars")
            prompt = prompt[:max_prompt_chars]
        
        estimated_input = self._estimate_token_count(prompt)
        estimated_output = max_tokens
        
        logger.info(f"📊 TOKEN ESTIMATION: Input ~{estimated_input:,} | Output ~{estimated_output:,} | Total ~{estimated_input + estimated_output:,}")
        
        try:
            wait_time = self.rate_limiter.wait_if_needed(estimated_input, estimated_output)
            if wait_time > 0:
                logger.info(f"⏱️  Total wait time: {wait_time:.2f}s")
        except Exception as e:
            logger.error(f"❌ Rate limit check failed: {str(e)}")
            return f"❌ Rate limit error: {str(e)}"
        
        while attempt < max_attempts:
            try:
                logger.info(f"\n🔄 ATTEMPT {attempt + 1}/{max_attempts} - {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
                call_start = time.time()
                
                if self.provider == "claude":
                    logger.info("   Calling Claude API...")
                    completion = self.client.messages.create(
                        model=self.model_name, max_tokens=max_tokens,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    response = completion.content[0].text
                elif self.provider == "openai":
                    logger.info("   Calling OpenAI API...")
                    completion = openai.chat.completions.create(
                        model=self.model_name,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=max_tokens, temperature=temperature
                    )
                    response = completion.choices[0].message.content
                elif "gemini" in self.provider:
                    logger.info("   Calling Gemini API...")
                    result = self.model.generate_content(
                        contents=prompt,
                        generation_config={"max_output_tokens": max_tokens, "temperature": temperature}
                    )
                    response = result.text if hasattr(result, 'text') else ''.join(
                        part.text for part in result.parts if hasattr(part, 'text')
                    ) if hasattr(result, 'parts') else ""
                
                call_duration = time.time() - call_start
                logger.info(f"✅ API SUCCESS - Duration: {call_duration:.2f}s | Response: {len(response):,} chars (~{self._estimate_token_count(response):,} tokens)")
                logger.info("=" * 70)
                return response

            except Exception as e:
                error_msg = str(e).lower()
                call_duration = time.time() - call_start
                logger.error(f"❌ API FAILED - Duration: {call_duration:.2f}s | Error: {str(e)[:200]}")
                
                is_rate_limit = any(kw in error_msg for kw in ["quota", "rate limit", "429", "too many requests", "resource exhausted"])
                
                if is_rate_limit and attempt < max_attempts - 1:
                    delay = 10.0 + (attempt * 5.0)
                    logger.warning(f"⚠️  RATE LIMIT - Retry {attempt + 1}/{max_attempts} after {delay:.1f}s...")
                    time.sleep(delay)
                    attempt += 1
                    continue
                else:
                    logger.error(f"   {'Max retries reached' if is_rate_limit else 'Non-rate-limit error'}")
                    return f"❌ {'Rate limit exceeded' if is_rate_limit else 'API Error'}: {str(e)[:200]}"
        
        return f"❌ Failed after {max_attempts} attempts"
    
    def _parse_structured_response(self, response: str) -> Dict[str, Any]:
        """Parse structured response with section markers"""
        logger.info(f"\n📝 PARSING RESPONSE ({len(response):,} chars)")
        
        results = {"core_analysis": "", "twitter_thread": [], "linkedin_post": "", "instagram_caption": "", "tldr": ""}
        
        try:
            sections = {
                "core_analysis": ["===CORE_ANALYSIS===", "===CORE ANALYSIS==="],
                "twitter": ["===TWITTER===", "===TWITTER THREAD==="],
                "linkedin": ["===LINKEDIN===", "===LINKEDIN POST==="],
                "instagram": ["===INSTAGRAM===", "===INSTAGRAM CAPTION==="],
                "tldr": ["===TLDR===", "===TL;DR==="]
            }
            
            for marker in sections["core_analysis"]:
                if marker in response:
                    results["core_analysis"] = response.split(marker)[1].split("===")[0].strip()
                    logger.info(f"   ✓ CORE_ANALYSIS: {len(results['core_analysis'])} chars")
                    break
            
            for marker in sections["twitter"]:
                if marker in response:
                    twitter_section = response.split(marker)[1].split("===")[0]
                    for line in twitter_section.split("\n"):
                        match = re.match(r"^\d+[\.):\s]+(.+)$", line.strip())
                        if match:
                            tweet = match.group(1).strip()
                            if len(tweet) > 15:
                                results["twitter_thread"].append(tweet)
                    logger.info(f"   ✓ TWITTER: {len(results['twitter_thread'])} tweets")
                    break
            
            for marker in sections["linkedin"]:
                if marker in response:
                    results["linkedin_post"] = response.split(marker)[1].split("===")[0].strip()
                    logger.info(f"   ✓ LINKEDIN: {len(results['linkedin_post'])} chars")
                    break
            
            for marker in sections["instagram"]:
                if marker in response:
                    results["instagram_caption"] = response.split(marker)[1].split("===")[0].strip()
                    logger.info(f"   ✓ INSTAGRAM: {len(results['instagram_caption'])} chars")
                    break
            
            for marker in sections["tldr"]:
                if marker in response:
                    results["tldr"] = response.split(marker)[1].split("===")[0].strip()
                    logger.info(f"   ✓ TLDR: {len(results['tldr'])} chars")
                    break
            
            if not any(results.values()):
                logger.warning("⚠️  No sections found, using fallback")
                results["core_analysis"] = response[:1000]
            else:
                logger.info("✅ Parsing completed")
            
            return results
        except Exception as e:
            logger.error(f"❌ Parsing error: {e}")
            return {"core_analysis": response, "twitter_thread": [], "linkedin_post": "", "instagram_caption": "", "tldr": ""}
    
    def _generate_all_outputs_single_call(self, content: str) -> Dict[str, Any]:
        """FREE TIER: Generate ALL outputs in SINGLE API call"""
        logger.info("\n🆓 SINGLE CALL STRATEGY")
        
        prompt = f"""You are a content repurposing expert. Generate ALL outputs in ONE response.
        CONTENT: {content}
        Format EXACTLY as:
        ===CORE_ANALYSIS===
        [analysis]
        ===TWITTER===
        1. [tweet 1]
        2. [tweet 2]
        ===LINKEDIN===
        [post]
        ===INSTAGRAM===
        [caption]
        #hashtags
        # ===TLDR===
        # [summary]"""
        
        response = self._call_llm(prompt, max_tokens=self.tier_config.max_output_tokens)
        return self._parse_structured_response(response)
    
    def _generate_outputs_separate_calls(self, content: str) -> Dict[str, Any]:
        """PAID TIER: Generate outputs using separate calls"""
        logger.info("\n💰 MULTI-CALL STRATEGY")
        
        core = self._call_llm(f"Analyze: {content}\n\nExtract: thesis, key points, tone, audience, data.", max_tokens=800)
        
        batch = self._call_llm(f"Based on: {core}\n\nGenerate formatted outputs.", max_tokens=2000)
        
        results = self._parse_structured_response(batch)
        results["core_analysis"] = core
        return results
    
    def repurpose_content(self, content: str) -> Dict[str, Any]:
        """Main repurposing pipeline"""
        logger.info("\n" + "=" * 70)
        logger.info(f"🎯 REPURPOSING CONTENT ({self.tier_config.name})")
        logger.info(f"   Input: {len(content):,} characters")
        logger.info("=" * 70)
        
        content = self._truncate_content_intelligently(content)
        start_time = time.time()
        
        results = self._generate_all_outputs_single_call(content) if self.is_free_tier else self._generate_outputs_separate_calls(content)
        
        elapsed = time.time() - start_time
        stats = self.rate_limiter.get_stats()
        
        logger.info("\n" + "=" * 70)
        logger.info(f"✅ COMPLETED IN {elapsed:.1f}s")
        logger.info(f"   API calls (minute): {stats['current_minute_requests']}/{stats['max_requests_per_minute']}")
        logger.info(f"   Tokens (minute): {stats['current_minute_tokens']:,}/{stats['max_tokens_per_minute']:,}")
        logger.info(f"   Daily usage: {stats['daily_requests']}/{stats['max_requests_per_day']}")
        logger.info(f"   Total requests: {stats['total_requests']}")
        logger.info("=" * 70 + "\n")
        
        return results