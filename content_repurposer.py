import anthropic
import openai
import google.generativeai as genai
import os
import re
import time
from typing import Dict, List, Any


class ContentRepurposer:
    def __init__(self, provider: str = "claude", api_key: str = None):
        self.provider = provider.lower().strip()
        self.api_key = api_key

        if self.provider == "openai":
            if not api_key or not isinstance(api_key, str) or not api_key.startswith("sk-"):
                raise ValueError("❌ Invalid OpenAI key.")

        if self.provider == "claude":
            if not api_key or not isinstance(api_key, str) or not api_key.startswith("sk-ant-"):
                raise ValueError("❌ Invalid Claude key.")

        if self.provider == "gemini":
            if not api_key or not isinstance(api_key, str) or not api_key.startswith("AIza"):
                raise ValueError("❌ Invalid Gemini key.")


        if self.provider == "claude":
            self.model_name = "claude-3-5-sonnet-latest"
            self.client = anthropic.Anthropic(api_key=self.api_key)

        elif self.provider == "openai":
            self.model_name = "gpt-4o"
            openai.api_key = self.api_key

        elif self.provider == "gemini":
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel("gemini-2.0-flash")
        else:
            raise ValueError(f"❌ Unsupported provider: {provider}")


    def _estimate_token_count(self, text: str) -> int:
        # rough token estimate: chars/4
        return max(1, int(len(text) / 4))

    def _chunk_text(self, text: str, max_chars: int = 4000) -> List[str]:
        """
        Simple paragraph‑aware chunking.
        """
        paragraphs = [p for p in text.split("\n\n") if p.strip()]
        chunks = []
        cur = []
        cur_len = 0
        for p in paragraphs:
            if cur_len + len(p) + 2 > max_chars and cur:
                chunks.append("\n\n".join(cur))
                cur = [p]
                cur_len = len(p) + 2
            else:
                cur.append(p)
                cur_len += len(p) + 2
        if cur:
            chunks.append("\n\n".join(cur))
        return chunks

    # ------------ GEMINI‑SAFE SUMMARIZATION ------------

    def _summarize_chunk(self, chunk: str) -> str:
        """
        Summarize a text chunk to reduce size.
        For Gemini, this keeps prompts well under per‑request limits. [web:25][web:30]
        """
        prompt = (
            "You are a concise summarizer.\n"
            "Summarize the following content in a short paragraph, preserving key ideas.\n\n"
            f"Content:\n{chunk}"
        )
        return self._call_llm(prompt, max_tokens=300)

    def _compress_via_hierarchical_summaries(
        self,
        content: str,
        target_tokens: int = 1500,
        max_chunk_chars: int = 4000,
    ) -> str:
        """
        Map‑reduce style compression:
        1. Split into chunks (map)
        2. Summarize each
        3. Summarize combined summaries until under target. [web:30][web:36]
        """
        paras = [p.strip() for p in content.split("\n\n") if len(p.strip()) > 30]
        content_trimmed = "\n\n".join(paras)

        chunks = self._chunk_text(content_trimmed, max_chars=max_chunk_chars)
        chunk_summaries = []

        for ch in chunks:
            s = self._summarize_chunk(ch)
            if not s:
                s = ch[:1000]
            chunk_summaries.append(s)

        combined = "\n\n".join(chunk_summaries)

        if self._estimate_token_count(combined) <= target_tokens:
            return combined

        max_iters = 6
        it = 0
        while self._estimate_token_count(combined) > target_tokens and it < max_iters:
            combined = self._summarize_chunk(combined)
            it += 1

        # Fallback hard cap
        if self._estimate_token_count(combined) > target_tokens:
            approx_chars = max(100, target_tokens * 4)
            combined = combined[:approx_chars]

        return combined

    # ------------ UNIFIED LLM CALLER (RATE‑LIMIT AWARE) ------------

    def _call_llm(self, prompt: str, max_tokens: int = 2000) -> str:
        """
        Central place to:
        - Keep prompts smaller for Gemini
        - Handle 429 / quota errors with backoff
        - Avoid infinite loops
        """
        max_attempts = 3
        attempt = 0

        # Extra safety for Gemini: hard cap prompt length (e.g. 6k chars ≈ 1.5k tokens)
        if self.provider == "gemini":
            max_prompt_chars = 6000
            if len(prompt) > max_prompt_chars:
                prompt = prompt[:max_prompt_chars]

        while attempt < max_attempts:
            try:
                # ---------- CLAUDE ----------
                if self.provider == "claude":
                    completion = self.client.messages.create(
                        model=self.model_name,
                        max_tokens=max_tokens,
                        messages=[{"role": "user", "content": prompt}],
                    )
                    return completion.content[0].text

                # ---------- OPENAI ----------
                elif self.provider == "openai":
                    completion = openai.chat.completions.create(
                        model=self.model_name,
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=max_tokens,
                    )
                    return completion.choices[0].message.content

                # ---------- GEMINI ----------
                elif self.provider == "gemini":
                    result = self.model.generate_content(
                        contents=prompt,
                        generation_config={
                            "max_output_tokens": max_tokens,
                            "temperature": 0.7,
                        },
                    )
                    return getattr(result, "text", "") or ""

                else:
                    return f"❌ Unsupported provider configured: {self.provider}"

            except Exception as e:
                msg = str(e)
                low = msg.lower()

                is_rate_limit = (
                    "quota" in low
                    or "rate limit" in low
                    or "429" in low
                    or "too many requests" in low
                    or "retry in" in low
                )

                if is_rate_limit:
                    # Parse 'retry in <n>s' from provider messages if present
                    m = re.search(r"retry in (\d+(?:\.\d+)?)s", msg, flags=re.IGNORECASE)
                    if m:
                        retry_seconds = float(m.group(1))
                        # If provider asks to retry after a long delay, return immediately with info
                        # This prevents blocking the Streamlit main thread for 30-60s.
                        if retry_seconds > 10:
                            return f"❌ Quota/rate limit: retry after {retry_seconds:.0f}s"
                        delay = retry_seconds + 1.0
                    else:
                        # Exponential backoff with a small cap to keep UI responsive
                        delay = min(10, (2 ** attempt) + (0.5 * attempt))

                    # Sleep only for small delays (<=10s) to allow quick retry attempts
                    if delay <= 10:
                        time.sleep(delay)
                        attempt += 1
                        continue
                    else:
                        return f"❌ Quota/rate limit: retry after {delay:.0f}s"

                return f"❌ Error calling {self.provider.upper()} API: {msg}"

        return f"❌ Error calling {self.provider.upper()} API: rate limit retries exhausted"

    # ============================================================
    # ANALYSIS + GENERATION
    # ============================================================

    def extract_core_message(self, content: str) -> str:
        # For Gemini, pass already‑compressed content (done in pipeline below)
        prompt = f"""
Analyze this content and extract:

1. MAIN THESIS (1 sentence)
2. KEY POINTS (3–5 bullets)
3. TONE
4. TARGET AUDIENCE
5. KEY DATA (numbers, stats, facts)

Content:
{content}

Return in the exact structure above.
"""
        return self._call_llm(prompt, max_tokens=800)

    def generate_twitter_thread(self, content: str, core_analysis: str) -> List[str]:
        prompt = f"""
Using this analysis:

{core_analysis}

Write an 8–12 tweet Twitter thread.

Rules:
- Tweet 1 = hook
- Each tweet max 280 chars
- No hashtags
- Short, punchy
- Number tweets: 1., 2., 3., etc.

Return only the tweets.
"""
        resp = self._call_llm(prompt, max_tokens=800)

        tweets = []
        for line in resp.split("\n"):
            line = line.strip()
            if re.match(r"^\d+[\.)]\s*", line):
                tweet = re.sub(r"^\d+[\.)]\s*", "", line)
                if tweet:
                    tweets.append(tweet)

        return tweets or [resp]

    def generate_linkedin_post(self, content: str, core_analysis: str) -> str:
        prompt = f"""
Using this content analysis:

{core_analysis}

Write a LinkedIn post:
- Professional, conversational
- 1000–1500 chars
- Hook in first line
- Short paragraphs
- No emojis (unless original had)
- End with question or CTA

Return full post.
"""
        return self._call_llm(prompt, max_tokens=700)

    def generate_instagram_caption(self, content: str, core_analysis: str) -> str:
        prompt = f"""
Using this analysis:

{core_analysis}

Write an Instagram caption:

- 150–200 char main caption
- Use visual language
- Then a newline
- 10–15 hashtags

Format:
[caption]

[hashtags]
"""
        return self._call_llm(prompt, max_tokens=300)

    def generate_tldr(self, content: str, core_analysis: str) -> str:
        prompt = f"""
Using this analysis:

{core_analysis}

Write a TL;DR:
- 2–3 sentences
- Preserve main message
"""
        return self._call_llm(prompt, max_tokens=200)

    # ============================================================
    # MAIN PIPELINE
    # ============================================================

    def repurpose_content(self, content: str) -> Dict[str, Any]:
        """
        1. Compress original content aggressively with hierarchical summaries
           (this is where we chunk; Gemini gets many small calls instead of one huge one). [web:30]
        2. Run all generation from the compressed version.
        """
        provider_budgets = {"openai": 3000, "claude": 5000, "gemini": 2000}
        target_tokens = provider_budgets.get(self.provider, 3000)

        # For Gemini, also slightly smaller chunks so each call is cheap
        max_chunk_chars = 4000 if self.provider != "gemini" else 2500

        compressed = self._compress_via_hierarchical_summaries(
            content,
            target_tokens=target_tokens,
            max_chunk_chars=max_chunk_chars,
        )

        core = self.extract_core_message(compressed)

        return {
            "core_analysis": core,
            "twitter_thread": self.generate_twitter_thread(compressed, core),
            "linkedin_post": self.generate_linkedin_post(compressed, core),
            "instagram_caption": self.generate_instagram_caption(compressed, core),
            "tldr": self.generate_tldr(compressed, core),
        }
