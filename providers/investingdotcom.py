# investingdotcom.py
import cloudscraper
import json
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.fair_value import graham_fair_value, margin_of_safety

# -----------------------------
# Configuration
# -----------------------------
BASE_URL = "https://www.investing.com"
DELAY_MIN = 1
DELAY_MAX = 2
MAX_WORKERS = 5

# Stock dictionary from our mapping
TUNISIAN_STOCKS = {
    "AB": {"symbol": "AB", "name": "AMEN BANK", "url": "/equities/amen-bank"},
    "AL": {"symbol": "AL", "name": "AIR LIQUIDE Tun", "url": "/equities/air-liquide-tunisie"},
    "ARTES": {"symbol": "ARTES", "name": "Automobile Reseau Tunisien Et Service", "url": "/equities/artes-renault"},
    "AST": {"symbol": "AST", "name": "ASTREE SA", "url": "/equities/com.-dassur.et-de-reassur."},
    "ATB": {"symbol": "ATB", "name": "ATB", "url": "/equities/arab-tunisian-bank"},
    "ATL": {"symbol": "ATL", "name": "ATL", "url": "/equities/arab-tunisian-lease"},
    "BH": {"symbol": "BH", "name": "BH Bank", "url": "/equities/banque-de-lhabitat"},
    "BIAT": {"symbol": "BIAT", "name": "BIAT", "url": "/equities/banque-inter.-arabe-de-tunisie"},
    "BNA": {"symbol": "BNA", "name": "BNA", "url": "/equities/banque-nationale-agricole"},
    "BS": {"symbol": "BS", "name": "ATTIJARI BANK", "url": "/equities/banque-attijari-de-tunisie"},
    "BT": {"symbol": "BT", "name": "BT", "url": "/equities/banque-de-tunisie"},
    "BTEI": {"symbol": "BTEI", "name": "BTEI", "url": "/equities/bq-de-tunisie-et-des-emirats"},
    "CC": {"symbol": "CC", "name": "Carthage Cement", "url": "/equities/carthage-cement"},
    "CIL": {"symbol": "CIL", "name": "CIL", "url": "/equities/compagnie-int.-de-leasing"},
    "ICF": {"symbol": "ICF", "name": "ICF", "url": "/equities/soc.-des-ind.-chimiu.-du-fluor"},
    "MGR": {"symbol": "MGR", "name": "Societe Tunisienne des Marches de Gros", "url": "/equities/sotumag"},
    "BHL": {"symbol": "BHL", "name": "BH Leasing", "url": "/equities/modern-leasing"},
    "MNP": {"symbol": "MNP", "name": "Societe Nouvelle Maison de la Ville de Tunis", "url": "/equities/monoprix"},
    "NAKL": {"symbol": "NAKL", "name": "Ennakl Automobiles", "url": "/equities/ennakl-automobiles"},
    "PLTU": {"symbol": "PLTU", "name": "PLACEMENT DE TUNISIE", "url": "/equities/placements-de-tunisie"},
    "POULA": {"symbol": "POULA", "name": "POULINA GROUP HLD", "url": "/equities/poulina-group-holding"},
    "SCB": {"symbol": "SCB", "name": "Les Ciments de Bizerte", "url": "/equities/ciments-de-bizerte"},
    "SFBT": {"symbol": "SFBT", "name": "SFBT", "url": "/equities/sfbt"},
    "SIAM": {"symbol": "SIAM", "name": "STE Ind d'appareillage Et De Materiels Elec", "url": "/equities/siame"},
    "SIMP": {"symbol": "SIMP", "name": "SIMPAR", "url": "/equities/soc.-immob.-et-de-part."},
    "SITS": {"symbol": "SITS", "name": "SITS", "url": "/equities/soc.-immob.-tuniso-seoud."},
    "SMG": {"symbol": "SMG", "name": "MAGASIN GENERAL", "url": "/equities/magazin-gneral"},
    "SOKNA": {"symbol": "SOKNA", "name": "ESSOUKNA", "url": "/equities/societe-essoukna"},
    "SOMOC": {"symbol": "SOMOC", "name": "SOMOCER", "url": "/equities/societe-moderne-de-ceramique"},
    "SOTE": {"symbol": "SOTE", "name": "STE Tunisienne d'entreprises De Telecommunications", "url": "/equities/sotetel"},
    "SPDI": {"symbol": "SPDI", "name": "SPDIT-SICAF", "url": "/equities/spdit"},
    "STAR": {"symbol": "STAR", "name": "STAR", "url": "/equities/star"},
    "STB": {"symbol": "STB", "name": "S.T.B", "url": "/equities/societe-tunisienne-de-banque"},
    "STIP": {"symbol": "STIP", "name": "Societe Tunisienne des Industries de Pneumatiques", "url": "/equities/soc.-tun.-des-ind.-de-pneumatiques"},
    "STPIL": {"symbol": "STPIL", "name": "SOTRAPIL", "url": "/equities/sotrapil"},
    "TINV": {"symbol": "TINV", "name": "TUN INVEST - SICAR", "url": "/equities/tuninvest"},
    "TJL": {"symbol": "TJL", "name": "ATTIJARI LEASING", "url": "/equities/attijari-leasing"},
    "TLNET": {"symbol": "TLNET", "name": "TELNET", "url": "/equities/telnet-holding"},
    "TLS": {"symbol": "TLS", "name": "TUNISIE LEASING", "url": "/equities/tunisie-leasing"},
    "TPR": {"symbol": "TPR", "name": "TPR", "url": "/equities/soc.-tun.-profiles-aluminium"},
    "TRE": {"symbol": "TRE", "name": "Tunis Re", "url": "/equities/soc.-tun.-de-reassurance"},
    "UBCI": {"symbol": "UBCI", "name": "Union Bancaire pour le Commerce et l'Industrie", "url": "/equities/u.b.c.i"},
    "UIB": {"symbol": "UIB", "name": "UIB", "url": "/equities/union-internationale-de-banque"},
    "WIFAK": {"symbol": "WIFAK", "name": "EL WIFACK LEASING", "url": "/equities/el-wifack-leasing"},
    "STVR": {"symbol": "STVR", "name": "Societe Tunisienne De Verreries", "url": "/equities/soc-tunisienne-de-verreries"},
    "BHASS": {"symbol": "BHASS", "name": "BH Assurance", "url": "/equities/salim"},
    "LNDOR": {"symbol": "LNDOR", "name": "Land Or", "url": "/equities/land-or"},
    "NBL": {"symbol": "NBL", "name": "New Body Li", "url": "/equities/new-body-li"},
    "OTH": {"symbol": "OTH", "name": "One Tech Ho", "url": "/equities/one-tech-ho"},
    "STPAP": {"symbol": "STPAP", "name": "Societe Tunisienne Industrielle Du Papier Et Du Ca", "url": "/equities/sotipapier"},
    "SOTEM": {"symbol": "SOTEM", "name": "Sotemail", "url": "/equities/sotemail"},
    "SAH": {"symbol": "SAH", "name": "Sah", "url": "/equities/sah"},
    "HANL": {"symbol": "HANL", "name": "Hannibal Lease", "url": "/equities/hannibal-lease"},
    "CITY": {"symbol": "CITY", "name": "City Cars", "url": "/equities/city-cars"},
    "ECYCL": {"symbol": "ECYCL", "name": "Euro-Cycles", "url": "/equities/euro-cycles"},
    "MPBS": {"symbol": "MPBS", "name": "Manufacture de Panneaux Bois du Sud", "url": "/equities/mpbs"},
    "BL": {"symbol": "BL", "name": "Best Lease", "url": "/equities/best-lease"},
    "DH": {"symbol": "DH", "name": "Societe Delice Holding", "url": "/equities/societe-delice-holding"},
    "PLAST": {"symbol": "PLAST", "name": "OfficePlast", "url": "/equities/officeplast"},
    "UMED": {"symbol": "UMED", "name": "Unite de Fabrication de Medicaments", "url": "/equities/unimed-sa"},
    "SAMAA": {"symbol": "SAMAA", "name": "Atelier Meuble Interieurs", "url": "/equities/atelier-meuble-interieurs"},
    "ASSMA": {"symbol": "ASSMA", "name": "Ste Assurances Magrebia", "url": "/equities/ste-assurances-magrebia"},
    "SMART": {"symbol": "SMART", "name": "Smart Tunisie", "url": "/equities/smart-tunisie"},
    "STAS": {"symbol": "STAS", "name": "Societe Tunisienne D Automobiles", "url": "/equities/societe-tunisienne-d-automobiles"},
    "AMV": {"symbol": "AMV", "name": "Assurances Maghrebia Vie", "url": "/equities/assurances-maghrebia-vie"},
}

# -----------------------------
# Helper Functions
# -----------------------------
def safe_get(data, *keys, default=None):
    """Safely navigate nested dictionary"""
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key, default)
        else:
            return default
    return data

def fetch_stock_detail(symbol, stock_info):
    """Fetch data for a single stock from Investing.com"""
    url = f"{BASE_URL}{stock_info['url']}"

    time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

    try:
        scraper = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "mobile": False}
        )
        resp = scraper.get(url)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        script_tag = soup.find("script", id="__NEXT_DATA__")
        if not script_tag:
            print(f"[WARN] Could not find __NEXT_DATA__ for {symbol}")
            return None

        data = json.loads(script_tag.string)

        # Extract instrument data from the state
        instrument = safe_get(data, "props", "pageProps", "state", "equityStore", "instrument", default={})
        price = instrument.get("price", {})
        exchange = instrument.get("exchange", {})
        fundamental = instrument.get("fundamental", {})
        volume = instrument.get("volume", {})
        bidding = instrument.get("bidding", {})
        performance = instrument.get("performance", {})
        technical = instrument.get("technical", {})
        technical_summary = technical.get("summary", {})
        underlying = instrument.get("underlying", {})

        # Extract company profile (for sector/industry)
        company_profile = safe_get(data, "props", "pageProps", "state", "companyProfileStore", "profile", default={})

        # Extract analyst/forecast data
        forecast = safe_get(data, "props", "pageProps", "state", "forecastStore", "forecast", default={})

        # Calculate Graham Fair Value and Margin of Safety
        eps = fundamental.get("eps")
        current_price = price.get("last")
        pe_ratio = fundamental.get("ratio")

        # Derive bvps from peerBenchmarksStore → peerBenchmarksData → value
        bvps = None
        pb_items = safe_get(data, "props", "pageProps", "state", "peerBenchmarksStore", "peerBenchmarksData", "value", default=[])
        for item in pb_items:
            if isinstance(item, dict) and item.get("key") == "price_to_book":
                try:
                    pb = float(item["company"])
                    if pb and pb != 0 and current_price:
                        bvps = round(float(current_price) / pb, 4)
                except (ValueError, KeyError, TypeError):
                    pass
                break

        # Fallback: keyMetricsStore → keyMetrics → metrics (live page path)
        if bvps is None:
            km_items = safe_get(data, "props", "pageProps", "state", "keyMetricsStore", "keyMetrics", "metrics", default=[])
            for item in km_items:
                if isinstance(item, dict) and item.get("slug") == "bv_share":
                    try:
                        raw = str(item.get("value", "")).replace(",", "").strip()
                        if raw and raw not in ("-", "NA", "N/A", ""):
                            bvps = float(raw)
                    except (ValueError, TypeError):
                        pass
                    break

        # Fallback: keyMetricsStore → keyMetricsCategoriesData → metrics (static HTML path)
        if bvps is None:
            km_items2 = safe_get(data, "props", "pageProps", "state", "keyMetricsStore", "keyMetricsCategoriesData", "metrics", default=[])
            for item in km_items2:
                if isinstance(item, dict) and item.get("slug") == "bv_share":
                    try:
                        raw = str(item.get("value", "")).replace(",", "").strip()
                        if raw and raw not in ("-", "NA", "N/A", ""):
                            bvps = float(raw)
                    except (ValueError, TypeError):
                        pass
                    break

        graham_value = graham_fair_value(eps, bvps)
        margin = margin_of_safety(current_price, graham_value)

        stock_data = {
            "symbol": symbol,
            "name": stock_info["name"],
            "url": stock_info["url"],
            "isin": underlying.get("isin"),
            "exchange": exchange.get("exchange"),
            "exchange_full_name": exchange.get("exchangeFullName"),
            "market": exchange.get("marketName"),
            "currency": price.get("currency"),
            "sector": company_profile.get("sector", {}).get("name"),
            "industry": company_profile.get("industry", {}).get("name"),

            "last_price": price.get("last"),
            "prev_close": price.get("lastClose"),
            "open": price.get("open"),
            "day_high": price.get("high"),
            "day_low": price.get("low"),
            "change": price.get("change"),
            "change_pct": price.get("changePcr"),
            "last_update": price.get("lastUpdateTime"),

            "week_52_high": price.get("fiftyTwoWeekHigh"),
            "week_52_low": price.get("fiftyTwoWeekLow"),
            "week_52_range": (
                f"{price.get('fiftyTwoWeekLow')} - {price.get('fiftyTwoWeekHigh')}"
                if price.get("fiftyTwoWeekLow") and price.get("fiftyTwoWeekHigh")
                else None
            ),

            "volume": volume.get("_turnover"),
            "avg_volume_3m": volume.get("average"),

            "bid": bidding.get("bid"),
            "ask": bidding.get("ask"),

            "market_cap": fundamental.get("marketCapRaw"),
            "shares_outstanding": fundamental.get("sharesOutstanding"),
            "eps": fundamental.get("eps"),
            "pe_ratio": fundamental.get("ratio"),
            "dividend": fundamental.get("dividend"),
            "dividend_yield": fundamental.get("yield"),
            "revenue": fundamental.get("revenueRaw"),
            "one_year_return": fundamental.get("oneYearReturn"),

            "beta": performance.get("beta"),

            "technical_summary_1d": technical_summary.get("P1D"),
            "technical_summary_1w": technical_summary.get("P1W"),
            "technical_summary_1m": technical_summary.get("P1M"),

            "analyst_consensus": forecast.get("consensus_recommendation"),
            "analyst_buy_count": forecast.get("number_of_analysts_buy"),
            "analyst_sell_count": forecast.get("number_of_analysts_sell"),
            "analyst_hold_count": forecast.get("number_of_analysts_hold"),

            "graham_fair_value": graham_value,
            "margin_of_safety": margin,
            "book_value_per_share": bvps,
        }

        print(f"[INFO] Fetched data for {symbol}")
        return stock_data

    except Exception as e:
        print(f"[ERROR] Failed to fetch {symbol}: {e}")
        return None

def fetch_all_stocks():
    """Fetch details for all Tunisian stocks using ThreadPoolExecutor"""
    stocks_data = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_symbol = {
            executor.submit(fetch_stock_detail, symbol, info): symbol
            for symbol, info in TUNISIAN_STOCKS.items()
        }

        for future in as_completed(future_to_symbol):
            symbol = future_to_symbol[future]
            try:
                result = future.result()
                if result:
                    stocks_data.append(result)
                    print(f"[SUCCESS] Completed: {symbol}")
                else:
                    print(f"[FAILED] Failed: {symbol}")
            except Exception as e:
                print(f"[ERROR] Exception for {symbol}: {e}")

    print(f"\n[INFO] Retrieved {len(stocks_data)} out of {len(TUNISIAN_STOCKS)} stocks")
    return stocks_data

def fetch_single_stock(symbol):
    """Fetch details for a single stock"""
    if symbol not in TUNISIAN_STOCKS:
        print(f"[ERROR] Symbol {symbol} not found in dictionary")
        return None
    return fetch_stock_detail(symbol, TUNISIAN_STOCKS[symbol])

# -----------------------------
# PROVIDER INTERFACE (Pipeline Compatible)
# -----------------------------
def get_provider_name():
    return "Investing.com Details"

def fetch_market_data():
    """Fetch all stocks data"""
    return fetch_all_stocks()

# -----------------------------
# Example Usage
# -----------------------------
if __name__ == "__main__":
    print("Testing with AB (Amen Bank)...")
    result = fetch_single_stock("AB")

    if result:
        print("\n" + "=" * 80)
        print(f"COMPLETE DATA FOR {result['symbol']} - {result['name']}")
        print("=" * 80)

        for key, value in result.items():
            print(f"{key:35}: {value}")
    else:
        print("Failed to fetch data")