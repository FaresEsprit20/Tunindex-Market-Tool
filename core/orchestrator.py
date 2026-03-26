# core/orchestrator.py

from config import ACTIVE_PROVIDER
from data.repository import MarketRepository

from services.normalizer import normalize_stock
from services.enricher import enrich
from utils.async_fetch import run_parallel

# Providers
from providers import ilboursa_elite
from providers import bvmt
from providers import tunisie_valeurs


def get_provider():
    providers = {
        "ilboursa": ilboursa_elite,
        "bvmt": bvmt,
        "tunisie_valeurs": tunisie_valeurs
    }
    return providers.get(ACTIVE_PROVIDER.lower())


def run_pipeline():
    provider = get_provider()
    if not provider:
        print("❌ No provider selected")
        return

    print(f"🚀 Running pipeline with provider: {provider.get_provider_name()}")

    repo = MarketRepository()

    # -------------------------
    # STEP 1: MARKET DATA (cached in provider)
    # -------------------------
    market_data = provider.fetch_market_data()
    if not market_data:
        print("❌ No market data fetched")
        return

    print(f"✅ Fetched {len(market_data)} stocks")

    # -------------------------
    # STEP 2: DETAILS (BVPS etc.) — PARALLEL
    # -------------------------
    if hasattr(provider, "scrape_bvps"):
        symbols = [s["symbol"] for s in market_data if s.get("symbol")]

        # Run scrape_bvps in parallel with higher max_workers
        details = run_parallel(provider.scrape_bvps, symbols, max_workers=20)

        # Update market_data with results
        for i, d in enumerate(details):
            if d:
                market_data[i].update(d)

    # -------------------------
    # STEP 3: NORMALIZE + ENRICH
    # -------------------------
    final_data = []
    for stock in market_data:
        normalized = normalize_stock(stock)
        enriched = enrich(normalized)
        final_data.append(enriched)

    # -------------------------
    # STEP 4: SAVE TO DB
    # -------------------------
    for stock in final_data:
        try:
            repo.upsert_stock(stock)
        except Exception as e:
            print("DB error:", e)

    print("✅ Pipeline completed successfully")
    repo.close()