# investingdotcom.py
import cloudscraper
import json
import time
import random
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TUNISIAN_STOCKS
from utils.fair_value import graham_fair_value, margin_of_safety, close_to_52weekslow_percentage

# -----------------------------
# Configuration
# -----------------------------
BASE_URL = "https://www.investing.com"
DELAY_MIN = 1
DELAY_MAX = 2
MAX_WORKERS = 5


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

def fetch_debt_equity(symbol, stock_info):
    """Fetch ONLY Debt/Equity from the financial-summary page"""
    url = f"{BASE_URL}{stock_info['url']}-financial-summary"
    
    time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
    
    try:
        scraper = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "mobile": False}
        )
        resp = scraper.get(url)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        debt_equity = None
        
        # Look for Debt / Equity in Key Ratios
        key_ratios_divs = soup.find_all('div', class_=re.compile(r'border-b.*py-3\.5'))
        
        for div in key_ratios_divs:
            text = div.get_text(strip=True)
            if 'Debt / Equity' in text:
                match = re.search(r'Debt / Equity\s*([\d.]+)%', text)
                if match:
                    try:
                        debt_equity = float(match.group(1))
                    except:
                        pass
                break
        
        print(f"[INFO] Debt/Equity for {symbol}: {debt_equity}%")
        return debt_equity
        
    except Exception as e:
        print(f"[ERROR] Failed to fetch Debt/Equity for {symbol}: {e}")
        return None

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

        # Get current price and 52-week range for calculation
        current_price = price.get("last")
        week_52_low = price.get("fiftyTwoWeekLow")
        week_52_high = price.get("fiftyTwoWeekHigh")
        
        # Calculate distance from 52-week low (inverse of position in range)
        # Formula: ((current - low) / (high - low)) * 100 = position in range (0-100%)
        # Then distance from low = 100% - position in range
        close_to_low_pct = None
        if current_price and week_52_low and week_52_high and week_52_high > week_52_low:
            # Position in range (0% = at low, 100% = at high)
            position_in_range = ((current_price - week_52_low) / (week_52_high - week_52_low)) * 100
            # Distance from low = how much room from low to current price (inverted)
            # If at high (100%), distance from low = 0% (meaning not close to low at all)
            # If at low (0%), distance from low = 100% (meaning very close to low)
            close_to_low_pct = round(100 - position_in_range, 2)
            print(f"[INFO] Position in 52-week range for {symbol}: {position_in_range}%")
            print(f"[INFO] Distance from 52-week low for {symbol}: {close_to_low_pct}%")
        
        # Get Key Metrics from keyMetricsStore
        km_items = safe_get(data, "props", "pageProps", "state", "keyMetricsStore", "keyMetrics", "metrics", default=[])
        
        # Extract Book Value per Share from Key Metrics
        bvps = None
        for item in km_items:
            if isinstance(item, dict) and item.get("slug") == "bv_share":
                try:
                    raw = str(item.get("value", "")).replace(",", "").strip()
                    if raw and raw not in ("-", "NA", "N/A", ""):
                        bvps = float(raw)
                        print(f"[INFO] Book Value from Key Metrics: {bvps}")
                except (ValueError, TypeError):
                    pass
                break
        
        # Extract P/E Ratio from Key Metrics
        pe_ratio = None
        for item in km_items:
            if isinstance(item, dict) and item.get("slug") == "pe_ltm":
                try:
                    raw = str(item.get("value", "")).replace(",", "").strip()
                    raw = raw.replace('x', '').strip()
                    if raw and raw not in ("-", "NA", "N/A", ""):
                        pe_ratio = float(raw)
                        print(f"[INFO] P/E Ratio from Key Metrics: {pe_ratio}")
                except (ValueError, TypeError):
                    pass
                break
        
        # Extract Price to Book from Key Metrics
        price_to_book = None
        for item in km_items:
            if isinstance(item, dict) and item.get("slug") == "price_to_book":
                try:
                    raw = str(item.get("value", "")).replace(",", "").strip()
                    raw = raw.replace('x', '').strip()
                    if raw and raw not in ("-", "NA", "N/A", ""):
                        price_to_book = float(raw)
                        print(f"[INFO] Price/Book from Key Metrics: {price_to_book}")
                except (ValueError, TypeError):
                    pass
                break
        
        # Get EPS from fundamental data
        eps = fundamental.get("eps")
        
        # Get Net Income and Revenue to calculate Profit Margin
        net_income = fundamental.get("netIncome") or fundamental.get("ni_avail_excl")
        revenue = fundamental.get("revenue") or fundamental.get("revenueRaw")
        
        profit_margin = None
        if net_income and revenue and revenue != 0:
            profit_margin = round((net_income / revenue) * 100, 2)
            print(f"[INFO] Calculated Profit Margin for {symbol}: {profit_margin}%")
        
        # Fetch ONLY Debt/Equity from financial summary page
        debt_to_equity = fetch_debt_equity(symbol, stock_info)
        
        # Calculate Graham Fair Value using BVPS from Key Metrics
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

            "last_price": current_price,
            "prev_close": price.get("lastClose"),
            "open": price.get("open"),
            "day_high": price.get("high"),
            "day_low": price.get("low"),
            "change": price.get("change"),
            "change_pct": price.get("changePcr"),
            "week_52_high": week_52_high,
            "week_52_low": week_52_low,
            "week_52_range": f"{week_52_low} - {week_52_high}" if week_52_low and week_52_high else None,
            "close_to_52weekslow_pct": close_to_low_pct,

            "volume": volume.get("_turnover"),
            "avg_volume_3m": volume.get("average"),

            "bid": bidding.get("bid"),
            "ask": bidding.get("ask"),

            "market_cap": fundamental.get("marketCapRaw"),
            "shares_outstanding": fundamental.get("sharesOutstanding"),
            "eps": eps,
            "pe_ratio": pe_ratio,
            "dividend_yield": fundamental.get("yield"),
            "revenue": revenue,
            "net_income": net_income,
            "profit_margin": profit_margin,
            "one_year_return": fundamental.get("oneYearReturn"),

            "price_to_book": price_to_book,
            "debt_to_equity": debt_to_equity,

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
        
        # Save to JSON file
        with open(f"{result['symbol']}_data.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Data saved to {result['symbol']}_data.json")
    else:
        print("Failed to fetch data")