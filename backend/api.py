import os
import re
import sys
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from core.brand_profile_engine import BrandProfileEngine
from core.content_extractor import ContentExtractor
from core.content_repurposer import ContentRepurposer
from core.models import BrandSoul, TrendContext
from data_engine.trend_scraper_v2 import TrendScraperV2
from service.twitter.profile_analyzer import TwitterProfileAnalyzer
from service.twitter.scraper import TwitterScraperAdvanced


app = FastAPI(title="Content Repurposer API", version="1.0.0")

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "FRONTEND_ORIGINS",
        "http://localhost:8080,http://127.0.0.1:8080,http://localhost:8081,http://127.0.0.1:8081,http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ExtractRequest(BaseModel):
    source: str = Field(..., min_length=1)
    input_type: Literal["text", "blog", "youtube"] = "text"


class RepurposeRequest(BaseModel):
    content: str = Field(..., min_length=1)
    provider: str = "gemini_free"
    api_key: str | None = None
    brand_soul: BrandSoul | None = None
    trends: TrendContext | None = None


class DistillSoulRequest(BaseModel):
    posts: list[str] = Field(default_factory=list)
    user_id: str | None = None


class ProfileAnalyzeRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=51)
    limit: int = Field(default=50, ge=20, le=100)


class ManualTrendsRequest(BaseModel):
    trends: list[str] = Field(default_factory=list)
    source: str = "manual"


class XCookiesRequest(BaseModel):
    cookies_json: str = Field(..., min_length=2)


def _clean_username(raw: str) -> str:
    username = raw.strip().lstrip("@")
    if not re.fullmatch(r"[A-Za-z0-9_]{1,50}", username):
        raise HTTPException(
            status_code=422,
            detail="Invalid username. Use only letters, numbers, and underscores.",
        )
    return username


def _profile_analysis_to_summary(analysis: dict) -> dict:
    top_tweets = analysis.get("top_tweets", [])
    bottom_tweets = analysis.get("bottom_tweets", [])
    viral = analysis.get("viral_insights", {})
    content_types = analysis.get("content_type_breakdown", {})

    tone_vectors = [
        {"k": "Engagement", "v": min(100, int(analysis.get("avg_likes", 0) + analysis.get("avg_retweets", 0)))},
        {"k": "Consistency", "v": min(100, int(analysis.get("tweet_count", 0)))},
        {"k": "Brevity", "v": max(0, min(100, 100 - int(analysis.get("avg_text_length", 0) / 3)))},
        {"k": "Media Bias", "v": min(100, int(content_types.get("media", {}).get("count", 0) * 10))},
        {"k": "Link Density", "v": min(100, int(content_types.get("link", {}).get("count", 0) * 10))},
        {"k": "Text Native", "v": min(100, int(content_types.get("text_only", {}).get("count", 0) * 10))},
    ]

    highlights = [
        f"Best content type: {viral.get('best_content_type', 'unknown')}.",
        f"Best posting window: {viral.get('best_posting_day', 'unknown')} at {viral.get('best_posting_hour', 0)}:00.",
        f"Average high-performing length: {viral.get('avg_viral_length', 0)} characters.",
        f"Analyzed {analysis.get('tweet_count', 0)} posts with {analysis.get('total_engagement', 0)} total engagement.",
    ]

    return {
        "posts": analysis.get("tweet_count", 0),
        "comments": 0,
        "collected_tweets": analysis.get("tweet_count", 0),
        "analysis": {
            "tone_vectors": tone_vectors,
            "highlights": highlights,
            "top_tweets": top_tweets,
            "bottom_tweets": bottom_tweets,
            "raw": analysis,
        },
    }


@app.get("/health")
def health() -> dict:
    return {"ok": True, "service": "content-repurposer-api"}


@app.get("/auth/x/status")
def get_x_auth_status() -> dict:
    scraper = TwitterScraperAdvanced()
    return {
        "cookies_present": Path(scraper.cookies_path).exists(),
        "cookies_path": scraper.cookies_path,
    }


@app.post("/auth/x/cookies")
def import_x_cookies(request: XCookiesRequest) -> dict:
    scraper = TwitterScraperAdvanced()
    success, message = scraper.login_with_manual_cookies(request.cookies_json)
    if not success:
        raise HTTPException(status_code=400, detail=message)
    return {
        "ok": True,
        "message": message,
        "cookies_path": scraper.cookies_path,
    }


@app.post("/extract")
def extract_content(request: ExtractRequest) -> dict:
    content, error = ContentExtractor.extract_content(request.source, request.input_type)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"content": content or "", "characters": len(content or "")}


@app.post("/repurpose")
def repurpose_content(request: RepurposeRequest) -> dict:
    api_key = request.api_key or os.getenv(f"{request.provider.upper()}_API_KEY") or os.getenv("LLM_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="API key is required for the selected provider.")

    try:
        repurposer = ContentRepurposer(provider=request.provider, api_key=api_key)
        return repurposer.repurpose_content(
            request.content,
            brand_soul=request.brand_soul,
            trends=request.trends,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/brand-soul")
def distill_brand_soul(request: DistillSoulRequest) -> dict:
    posts = [post.strip() for post in request.posts if len(post.strip()) > 10]
    if not posts:
        raise HTTPException(status_code=400, detail="Provide at least one post with more than 10 characters.")

    soul = BrandProfileEngine().distill_soul(posts)
    if request.user_id:
        BrandProfileEngine().save_soul(request.user_id, soul)
    return soul.model_dump()


@app.get("/trends")
def get_trends() -> dict:
    return {"trends": TrendScraperV2().get_all_trends()}


@app.post("/trends")
def add_trends(request: ManualTrendsRequest) -> dict:
    clean_trends = [trend.strip() for trend in request.trends if trend.strip()]
    if not clean_trends:
        raise HTTPException(status_code=400, detail="Provide at least one trend.")
    scraper = TrendScraperV2()
    scraper.add_manual_trends(clean_trends, source=request.source)
    return {"trends": scraper.get_all_trends()}


@app.post("/profile/x/analyze")
def analyze_x_profile(request: ProfileAnalyzeRequest) -> dict:
    username = _clean_username(request.username)
    analysis, error = TwitterProfileAnalyzer().analyze_user_patterns(username, tweet_limit=request.limit)
    if error or not analysis:
        raise HTTPException(status_code=400, detail=error or "No analysis returned.")
    return _profile_analysis_to_summary(analysis)
