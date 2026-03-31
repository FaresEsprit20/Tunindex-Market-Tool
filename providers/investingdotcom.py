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
        
        # Calculate distance from 52-week low
        close_to_low_pct = None
        if current_price and week_52_low and week_52_high and week_52_high > week_52_low:
            position_in_range = ((current_price - week_52_low) / (week_52_high - week_52_low)) * 100
            close_to_low_pct = round(100 - position_in_range, 2)
            print(f"[INFO] Distance from 52-week low for {symbol}: {close_to_low_pct}%")
        
        # Extract Key Metrics from the keyMetricsStore in JSON
        bvps = None
        pe_ratio = None
        price_to_book = None
        
        # Get the keyMetrics array from the correct path
        key_metrics_list = safe_get(data, "props", "pageProps", "state", "keyMetricsStore", "keyMetrics", "metrics", default=[])
        
        # If that didn't work, try alternative path
        if not key_metrics_list:
            key_metrics_list = safe_get(data, "props", "pageProps", "state", "keyMetricsStore", "keyMetrics", default=[])
        
        # If it's a dict, try to extract the metrics array
        if isinstance(key_metrics_list, dict):
            # Look for metrics array in the dict
            key_metrics_list = key_metrics_list.get("metrics", [])
        
        print(f"[DEBUG] Found {len(key_metrics_list) if key_metrics_list else 0} metrics")
        
        # Iterate through the metrics
        if key_metrics_list:
            for item in key_metrics_list:
                if isinstance(item, dict):
                    slug = item.get("slug", "")
                    value = item.get("value", "")
                    
                    if slug == "bv_share":
                        try:
                            # Clean the value (remove commas, etc.)
                            clean_value = str(value).replace(',', '').strip()
                            if clean_value and clean_value not in ("-", "NA", "N/A", ""):
                                bvps = float(clean_value)
                                print(f"[INFO] Book Value from Key Metrics: {bvps}")
                        except (ValueError, TypeError):
                            pass
                    
                    elif slug == "pe_ltm":
                        try:
                            clean_value = str(value).replace(',', '').replace('x', '').strip()
                            if clean_value and clean_value not in ("-", "NA", "N/A", ""):
                                pe_ratio = float(clean_value)
                                print(f"[INFO] P/E Ratio from Key Metrics: {pe_ratio}")
                        except (ValueError, TypeError):
                            pass
                    
                    elif slug == "price_to_book":
                        try:
                            clean_value = str(value).replace(',', '').replace('x', '').strip()
                            if clean_value and clean_value not in ("-", "NA", "N/A", ""):
                                price_to_book = float(clean_value)
                                print(f"[INFO] Price/Book from Key Metrics: {price_to_book}")
                        except (ValueError, TypeError):
                            pass
        
        # Fallback: Try to find in the HTML key metrics section
        if bvps is None:
            # Look for the specific div containing Book Value
            bv_elements = soup.find_all('div', class_=re.compile(r'flex flex-wrap items-center justify-between'))
            for elem in bv_elements:
                text = elem.get_text()
                if 'Book Value / Share' in text:
                    # Find the number in the dd element
                    dd = elem.find('dd')
                    if dd:
                        try:
                            bvps = float(dd.get_text(strip=True))
                            print(f"[INFO] Book Value from HTML div: {bvps}")
                        except:
                            pass
        
        # Get EPS from fundamental data
        eps = fundamental.get("eps")
        
        # Fetch ONLY Debt/Equity from financial summary page
        debt_to_equity = fetch_debt_equity(symbol, stock_info)
        
        # Calculate Graham Fair Value using BVPS
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
            "last_update": price.get("lastUpdateTime"),

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
            "revenue": fundamental.get("revenueRaw"),
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
    else:
        print("Failed to fetch data")