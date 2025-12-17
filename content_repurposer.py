"""
Content Repurposer with Optimization
- Free tier support with intelligent truncation
- Better error handling and retry logic
- Improved parsing and validation
- Performance optimizations
"""

import anthropic
import openai
import google.generativeai as genai
import os
import re
import time
from typing import Dict, List, Any, Optional, Tuple
from collections import deque
import random
from dataclasses import dataclass


@dataclass
class TierConfig:
    """Configuration for different API tiers"""
    max_input_chars: int
    max_output_tokens: int
    requests_per_minute: int
    min_delay_seconds: float
    name: str


class RateLimiter:
    """Rate limiter for API calls with improved tracking"""
    
    def __init__(self, max_requests: int = 15, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
        self.last_request_time = 0
        self.min_delay = time_window / max_requests
        self.total_requests = 0
    
    def wait_if_needed(self) -> float:
        """
        Wait if rate limit would be exceeded.
        Returns: Time waited in seconds
        """
        now = time.time()
        wait_time = 0
        
        # Remove old requests outside the time window
        while self.requests and self.requests[0] < now - self.time_window:
            self.requests.popleft()
        
        # Check if at limit
        if len(self.requests) >= self.max_requests:
            wait_time = self.time_window - (now - self.requests[0]) + 0.5
            if wait_time > 0:
                print(f"[RATE LIMITER] At limit ({len(self.requests)}/{self.max_requests}), waiting {wait_time:.1f}s...")
                time.sleep(wait_time)
                now = time.time()
        
        # Ensure minimum delay between requests
        time_since_last = now - self.last_request_time
        if time_since_last < self.min_delay and self.last_request_time > 0:
            delay = self.min_delay - time_since_last
            time.sleep(delay)
            wait_time += delay
        
        # Record this request
        self.requests.append(time.time())
        self.last_request_time = time.time()
        self.total_requests += 1
        
        return wait_time
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        return {
            "total_requests": self.total_requests,
            "current_window_requests": len(self.requests),
            "max_requests": self.max_requests,
            "time_window": self.time_window
        }


class ContentRepurposer:
    """
    Content repurposer with multi-tier support and optimization.
    Supports free and paid tiers with intelligent content handling.
    """
    
    # Configuration for different tiers
    TIER_CONFIGS = {
        "gemini_free": TierConfig(
            max_input_chars=2500,
            max_output_tokens=1500,
            requests_per_minute=15,
            min_delay_seconds=4.5,
            name="Gemini Free"
        ),
        "gemini": TierConfig(
            max_input_chars=30000,
            max_output_tokens=2048,
            requests_per_minute=60,
            min_delay_seconds=1.0,
            name="Gemini Pro"
        ),
        "claude": TierConfig(
            max_input_chars=100000,
            max_output_tokens=4096,
            requests_per_minute=50,
            min_delay_seconds=1.2,
            name="Claude"
        ),
        "openai": TierConfig(
            max_input_chars=50000,
            max_output_tokens=4096,
            requests_per_minute=60,
            min_delay_seconds=1.0,
            name="OpenAI"
        )
    }
    
    def __init__(self, provider: str = "claude", api_key: str = None):
        self.provider = provider.lower().strip()
        self.api_key = api_key
        self.is_free_tier = "free" in self.provider.lower()
        
        # Get tier configuration
        self.tier_config = self.TIER_CONFIGS.get(
            self.provider,
            self.TIER_CONFIGS["gemini_free"]
        )
        
        # Setup rate limiter
        self.rate_limiter = RateLimiter(
            max_requests=self.tier_config.requests_per_minute,
            time_window=60
        )
        
        print(f"✅ Initialized {self.tier_config.name}")
        print(f"   Max input: {self.tier_config.max_input_chars:,} chars")
        print(f"   Rate limit: {self.tier_config.requests_per_minute} req/min")
        
        # Validate and initialize API client
        self._validate_and_init_client()
    
    def _validate_and_init_client(self):
        """Validate API key and initialize the appropriate client"""
        
        # Validation rules
        validation_rules = {
            "openai": ("sk-", "OpenAI"),
            "claude": ("sk-ant-", "Claude"),
            "gemini": ("AIza", "Gemini"),
            "gemini_free": ("AIza", "Gemini")
        }
        
        if self.provider not in validation_rules:
            raise ValueError(f"❌ Unsupported provider: {self.provider}")
        
        prefix, name = validation_rules[self.provider]
        
        if not self.api_key or not isinstance(self.api_key, str):
            raise ValueError(f"❌ Invalid {name} API key: Key must be a non-empty string")
        
        if not self.api_key.startswith(prefix):
            raise ValueError(f"❌ Invalid {name} API key: Must start with '{prefix}'")
        
        # Initialize client based on provider
        try:
            if self.provider == "claude":
                self.model_name = "claude-3-5-sonnet-latest"
                self.client = anthropic.Anthropic(api_key=self.api_key)
                
            elif self.provider == "openai":
                self.model_name = "gpt-4o"
                openai.api_key = self.api_key
                
            elif "gemini" in self.provider:
                genai.configure(api_key=self.api_key)
                # Use cheaper model for free tier
                model_name = "gemini-1.5-flash" if self.is_free_tier else "gemini-2.0-flash"
                self.model = genai.GenerativeModel(model_name)
                print(f"   Using model: {model_name}")
                
        except Exception as e:
            raise ValueError(f"❌ Failed to initialize {name} client: {str(e)}")
    
    def _truncate_content_intelligently(self, content: str) -> str:
        """
        Intelligently truncate content to fit tier limits.
        Preserves beginning (context) and end (conclusion).
        """
        max_chars = self.tier_config.max_input_chars
        
        if len(content) <= max_chars:
            return content
        
        print(f"⚠️  Content: {len(content):,} chars → Truncating to {max_chars:,} chars")
        
        # Strategy: Keep first 65% and last 35% to preserve context and conclusion
        first_ratio = 0.65
        last_ratio = 0.35
        
        first_part_size = int(max_chars * first_ratio)
        last_part_size = int(max_chars * last_ratio)
        
        first_part = content[:first_part_size]
        last_part = content[-last_part_size:]
        
        # Add truncation marker
        truncated = (
            f"{first_part}\n\n"
            f"[... {len(content) - first_part_size - last_part_size:,} characters truncated ...]\n\n"
            f"{last_part}"
        )
        
        # Ensure we don't exceed limit with the marker
        if len(truncated) > max_chars:
            truncated = truncated[:max_chars]
        
        print(f"✅ Truncated to {len(truncated):,} chars")
        return truncated
    
    def _estimate_token_count(self, text: str) -> int:
        """Rough estimate of token count (4 chars ≈ 1 token)"""
        return max(1, int(len(text) / 4))
    
    def _call_llm(
        self, 
        prompt: str, 
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> str:
        """
        Unified LLM caller with rate limiting and retry logic.
        """
        max_attempts = 3
        attempt = 0
        
        # Apply rate limiting
        wait_time = self.rate_limiter.wait_if_needed()
        if wait_time > 0:
            print(f"⏱️  Waited {wait_time:.1f}s for rate limit")
        
        # Truncate prompt if needed
        max_prompt_chars = self.tier_config.max_input_chars
        if len(prompt) > max_prompt_chars:
            prompt = prompt[:max_prompt_chars]
            print(f"⚠️  Prompt truncated to {max_prompt_chars:,} chars")
        
        while attempt < max_attempts:
            try:
                if self.provider == "claude":
                    completion = self.client.messages.create(
                        model=self.model_name,
                        max_tokens=max_tokens,
                        messages=[{"role": "user", "content": prompt}],
                    )
                    return completion.content[0].text

                elif self.provider == "openai":
                    completion = openai.chat.completions.create(
                        model=self.model_name,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=max_tokens,
                        temperature=temperature
                    )
                    return completion.choices[0].message.content

                elif "gemini" in self.provider:
                    result = self.model.generate_content(
                        contents=prompt,
                        generation_config={
                            "max_output_tokens": max_tokens,
                            "temperature": temperature,
                        },
                    )
                    
                    # Handle different response types
                    if hasattr(result, 'text'):
                        return result.text
                    elif hasattr(result, 'parts'):
                        return ''.join(part.text for part in result.parts if hasattr(part, 'text'))
                    else:
                        return ""

            except Exception as e:
                error_msg = str(e).lower()
                
                # Check if it's a rate limit error
                is_rate_limit = any(
                    keyword in error_msg 
                    for keyword in ["quota", "rate limit", "429", "too many requests", "resource exhausted"]
                )
                
                if is_rate_limit and attempt < max_attempts - 1:
                    # Extract retry time if available
                    retry_match = re.search(r"retry in (\d+(?:\.\d+)?)s", str(e), re.IGNORECASE)
                    
                    if retry_match:
                        delay = float(retry_match.group(1)) + 1.0
                    else:
                        # Exponential backoff with jitter
                        base_delay = 2 ** attempt
                        jitter = random.uniform(0.5, 1.5)
                        delay = min(60, base_delay + jitter)
                    
                    print(f"⚠️  Rate limit hit (attempt {attempt + 1}/{max_attempts})")
                    print(f"   Waiting {delay:.1f}s before retry...")
                    time.sleep(delay)
                    attempt += 1
                    continue
                else:
                    # Non-rate-limit error or final attempt
                    error_summary = str(e)[:200]
                    return f"❌ Error calling {self.provider.upper()} API: {error_summary}"
        
        return f"❌ Error: Rate limit retries exhausted after {max_attempts} attempts"
    
    def _parse_structured_response(self, response: str) -> Dict[str, Any]:
        """
        Parse structured response with section markers.
        Handles various formatting variations.
        """
        results = {
            "core_analysis": "",
            "twitter_thread": [],
            "linkedin_post": "",
            "instagram_caption": "",
            "tldr": ""
        }
        
        try:
            # Define section markers (with variations)
            sections = {
                "core_analysis": [
                    "===CORE_ANALYSIS===",
                    "===CORE ANALYSIS===",
                    "CORE_ANALYSIS:",
                    "CORE ANALYSIS:"
                ],
                "twitter": [
                    "===TWITTER===",
                    "===TWITTER THREAD===",
                    "TWITTER_THREAD:",
                    "TWITTER:"
                ],
                "linkedin": [
                    "===LINKEDIN===",
                    "===LINKEDIN POST===",
                    "LINKEDIN_POST:",
                    "LINKEDIN:"
                ],
                "instagram": [
                    "===INSTAGRAM===",
                    "===INSTAGRAM CAPTION===",
                    "INSTAGRAM_CAPTION:",
                    "INSTAGRAM:"
                ],
                "tldr": [
                    "===TLDR===",
                    "===TL;DR===",
                    "TLDR:",
                    "TL;DR:"
                ]
            }
            
            # Parse Core Analysis
            for marker in sections["core_analysis"]:
                if marker in response:
                    parts = response.split(marker)
                    if len(parts) > 1:
                        next_section = parts[1].split("===")[0]
                        results["core_analysis"] = next_section.strip()
                        break
            
            # Parse Twitter Thread
            for marker in sections["twitter"]:
                if marker in response:
                    parts = response.split(marker)
                    if len(parts) > 1:
                        twitter_section = parts[1].split("===")[0]
                        
                        # Extract numbered tweets
                        for line in twitter_section.split("\n"):
                            line = line.strip()
                            # Match: "1. tweet" or "1) tweet" or "1: tweet"
                            match = re.match(r"^\d+[\.):\s]+(.+)$", line)
                            if match:
                                tweet = match.group(1).strip()
                                # Filter out very short or empty tweets
                                if tweet and len(tweet) > 15:
                                    results["twitter_thread"].append(tweet)
                        break
            
            # Parse LinkedIn
            for marker in sections["linkedin"]:
                if marker in response:
                    parts = response.split(marker)
                    if len(parts) > 1:
                        linkedin_section = parts[1].split("===")[0]
                        results["linkedin_post"] = linkedin_section.strip()
                        break
            
            # Parse Instagram
            for marker in sections["instagram"]:
                if marker in response:
                    parts = response.split(marker)
                    if len(parts) > 1:
                        instagram_section = parts[1].split("===")[0]
                        results["instagram_caption"] = instagram_section.strip()
                        break
            
            # Parse TLDR
            for marker in sections["tldr"]:
                if marker in response:
                    parts = response.split(marker)
                    if len(parts) > 1:
                        tldr_section = parts[1].split("===")[0]
                        results["tldr"] = tldr_section.strip()
                        break
            
            # Validation: Check if we got meaningful results
            has_content = any([
                results["core_analysis"],
                results["twitter_thread"],
                results["linkedin_post"],
                results["instagram_caption"],
                results["tldr"]
            ])
            
            if not has_content:
                print("⚠️  Warning: No structured sections found, using fallback")
                results["core_analysis"] = response[:1000]  # Fallback to raw response
            else:
                print(f"✅ Parsed: {len(results['twitter_thread'])} tweets, "
                      f"{len(results['linkedin_post'])} chars LinkedIn, "
                      f"{len(results['instagram_caption'])} chars Instagram")
            
            return results
            
        except Exception as e:
            print(f"❌ Error parsing response: {e}")
            # Fallback: return raw response in core_analysis
            return {
                "core_analysis": response,
                "twitter_thread": [],
                "linkedin_post": "",
                "instagram_caption": "",
                "tldr": ""
            }
    
    def _generate_all_outputs_single_call(self, content: str) -> Dict[str, Any]:
        """
        FREE TIER OPTIMIZED: Generate ALL outputs in a SINGLE API call.
        """
        max_tokens = self.tier_config.max_output_tokens
        
        prompt = f"""You are a content repurposing expert. Generate ALL of the following from this content in ONE response.

CONTENT TO REPURPOSE:
{content}

Generate these outputs:

1. CORE ANALYSIS: Extract main thesis, 3-5 key points, tone, target audience, and key data/stats.

2. TWITTER THREAD: Create 8-12 tweets, each under 280 characters. Number them (1., 2., 3., etc.). Make them engaging and actionable.

3. LINKEDIN POST: Write 1000-1500 characters, professional yet conversational. Start with a hook. Include line breaks for readability.

4. INSTAGRAM CAPTION: Write 150-200 character main caption, then add 10-15 relevant hashtags on new lines.

5. TL;DR: Provide a 2-3 sentence summary capturing the core message.

Format your response EXACTLY like this:

===CORE_ANALYSIS===
[Your analysis here]

===TWITTER===
1. [tweet 1]
2. [tweet 2]
3. [tweet 3]
...

===LINKEDIN===
[LinkedIn post here]

===INSTAGRAM===
[Caption here]

#hashtag1 #hashtag2 #hashtag3 ...

===TLDR===
[Summary here]

Remember: Use these exact section headers with === markers."""
        
        print(f"🔄 Making single API call ({self.tier_config.name})...")
        response = self._call_llm(prompt, max_tokens=max_tokens)
        
        # Parse and return results
        results = self._parse_structured_response(response)
        return results
    
    def _generate_outputs_separate_calls(self, content: str) -> Dict[str, Any]:
        """
        PAID TIER: Generate outputs using optimized separate calls.
        """
        print(f"💰 Using multi-call strategy ({self.tier_config.name})")
        
        # Step 1: Core analysis
        core_prompt = f"""Analyze this content and extract:
1. MAIN THESIS (1 sentence)
2. KEY POINTS (3-5 bullets)
3. TONE (professional, casual, technical, etc.)
4. TARGET AUDIENCE
5. KEY DATA/STATS (numbers, facts)

Content:
{content}

Provide a structured analysis."""
        
        core = self._call_llm(core_prompt, max_tokens=800)
        
        # Step 2: Batch generate platform outputs
        batch_prompt = f"""Based on this analysis:

{core}

Generate:
1. TWITTER THREAD (8-12 tweets, max 280 chars each, numbered)
2. LINKEDIN POST (1000-1500 chars, professional, conversational)
3. INSTAGRAM CAPTION (150-200 chars + 10-15 hashtags)
4. TL;DR (2-3 sentence summary)

Use this exact format:

===TWITTER===
1. [tweet]
...

===LINKEDIN===
[post]

===INSTAGRAM===
[caption]
#hashtags

===TLDR===
[summary]"""
        
        batch_response = self._call_llm(batch_prompt, max_tokens=2000)
        
        # Parse and combine results
        results = self._parse_structured_response(batch_response)
        results["core_analysis"] = core
        
        return results
    
    def repurpose_content(self, content: str) -> Dict[str, Any]:
        """
        Main repurposing pipeline.
        Automatically chooses strategy based on tier.
        """
        print(f"\n{'='*60}")
        print(f"REPURPOSING CONTENT ({self.tier_config.name})")
        print(f"{'='*60}")
        print(f"Input: {len(content):,} characters")
        
        # Step 1: Truncate content if needed
        content = self._truncate_content_intelligently(content)
        
        # Step 2: Choose strategy based on tier
        start_time = time.time()
        
        if self.is_free_tier:
            print("\n🆓 Strategy: Single API call (Free Tier)")
            results = self._generate_all_outputs_single_call(content)
        else:
            print("\n💰 Strategy: Multi-call optimization (Paid Tier)")
            results = self._generate_outputs_separate_calls(content)
        
        elapsed = time.time() - start_time
        
        # Step 3: Log statistics
        stats = self.rate_limiter.get_stats()
        print(f"\n{'='*60}")
        print(f"✅ COMPLETED IN {elapsed:.1f}s")
        print(f"   API calls: {stats['current_window_requests']}")
        print(f"   Total requests: {stats['total_requests']}")
        print(f"{'='*60}\n")
        
        return results