"""Quick import verification after refactor."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

results = []

def check(label, fn):
    try:
        fn()
        results.append(f"  ✅ {label}")
    except Exception as e:
        results.append(f"  ❌ {label}: {e}")

check("ui.styles",           lambda: __import__("ui.styles", fromlist=["apply_custom_css"]))
check("core.models",         lambda: __import__("core.models", fromlist=["BrandSoul"]))
check("core.prompts",        lambda: __import__("core.prompts", fromlist=["REPURPOSE_PROMPT_TEMPLATE"]))
check("core.vector_store",   lambda: __import__("core.vector_store", fromlist=["BrandVectorStore"]))
check("core.brand_profile_engine", lambda: __import__("core.brand_profile_engine", fromlist=["BrandProfileEngine"]))
check("core.content_extractor",    lambda: __import__("core.content_extractor", fromlist=["ContentExtractor"]))
check("core.content_repurposer",   lambda: __import__("core.content_repurposer", fromlist=["ContentRepurposer"]))
check("data_engine.trend_scraper_v2",  lambda: __import__("data_engine.trend_scraper_v2", fromlist=["TrendScraperV2"]))
check("data_engine.brand_collector",   lambda: __import__("data_engine.brand_collector", fromlist=["BrandDataCollector"]))
check("service.twitter",     lambda: __import__("service.twitter", fromlist=["TwitterProfileAnalyzer"]))
check("service.llm_analyzer",lambda: __import__("service.llm_analyzer", fromlist=["ContentLLMAnalyzer"]))

print("\nImport Verification Results:")
for r in results:
    print(r)

failures = [r for r in results if "❌" in r]
print(f"\n{'🎉 All imports passed!' if not failures else f'⚠️  {len(failures)} import(s) failed.'}")
