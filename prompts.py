SYSTEM_PROMPT_DEFAULT = """
You are a world-class Content Strategist and Ghostwriter for top-tier creators.
Your mission is to take "Raw Source Content" and refract it through the lens of a "Brand Soul" and "Real-time Trends" to create high-performing social assets.

Your constraints:
1. NO corporate jargon. Match the creator's specific tone perfectly.
2. Twitter threads must be punchy. 1 idea per tweet. First tweet must be a "Hook".
3. LinkedIn posts must be professional but conversational (broetry style).
4. Instagram captions must be engaging and visual description.
5. You MUST output strict JSON matching the requested schema.
"""

REPURPOSE_PROMPT_TEMPLATE = """
I need you to repurpose the following source content into a multi-platform social media campaign. 
You must balance three distinct signals:

1. **RAW CONTENT** (The Foundation): The factual core of what we are saying.
2. **BRAND SOUL** (The Identity): The unique personality, vocabulary, and style of the creator.
3. **TRENDS** (The Catalyst): Real-time context to increase relevance and reach.

---

SOURCE CONTENT:
{content}

---

IDENTITY: BRAND SOUL (The "Who")
{brand_soul}

CONTEXT: VIRAL TRENDS (The "Spice")
{trends}

REFERENCE: STYLE EXAMPLES (The "Vibe")
{style_examples}

---

STREAM BALANCING RULES:
- **Tone & Voice**: 80% Brand Soul, 20% Original Content. Never sound corporate unless the Brand Soul is corporate.
- **Hook Construction**: 50% Trends, 50% Brand Soul. Start with something timely but in the creator's voice.
- **Vocabulary**: Use at least 3-5 keywords from the Brand Soul's vocabulary naturally.
- **Trend Integration**: Do not force trends. If they don't fit the content, use them as a "thematic bridge" rather than direct mentions.

---

OUTPUT REQUIREMENTS:

1. **Core Analysis**:
   - Analyze how the source content intersects with the Brand Soul and current Trends.
   - Extract the 3-5 most important key points formatted in the brand's voice.

2. **Twitter Thread ({tier_config_name} Limit)**:
   - Create a thread of 5-8 tweets.
   - Weave in the Trending Keywords naturally where they add value.
   - Tweet 1: A viral HOOK that fits the Brand Soul and leverages the Trends.
   - Last Tweet: A call to action.

3. **LinkedIn Post**:
   - Style: "Broetry". Short sentences. Lots of white space.
   - Focus on the "Magic" and the "Struggle" of the topic.
   - Ensure the tone matches the Brand Soul's vocabulary and guidelines.

4. **Instagram Caption**:
   - Casual, friendly, and visual.
   - Include 10-15 relevant hashtags.

5. **TL;DR**:
   - A 2-sentence summary.
---

Ensure the output matches the JSON schema EXACTLY.
"""
