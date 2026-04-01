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

def extract_value_from_indicator(indicator):
    """Extract numeric value from indicator dictionary or return as is if numeric"""
    if indicator is None:
        return None
    if isinstance(indicator, (int, float)):
        return indicator
    if isinstance(indicator, dict):
        # Try to get the 'value' field
        value = indicator.get('value')
        if value is not None and isinstance(value, (int, float)):
            return value
        # Try to get 'raw_value' or other common fields
        value = indicator.get('raw_value')
        if value is not None and isinstance(value, (int, float)):
            return value
    return None

def fetch_financial_ratios(symbol, stock_info):
    """Fetch P/E Ratio, Price/Book, Debt/Equity from the financial-summary page"""
    url = f"{BASE_URL}{stock_info['url']}-financial-summary"
    
    time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
    
    try:
        scraper = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "mobile": False}
        )
        resp = scraper.get(url)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Initialize variables
        pe_ratio = None
        price_to_book = None
        debt_to_equity = None
        
        # Find all cells in the Key Ratios table
        ratio_cells = soup.find_all('div', class_=re.compile(r'border-b border-\[\#e4eaf1\] py-3\.5'))
        
        for cell in ratio_cells:
            # Get the label text
            label_elem = cell.find('span', class_=re.compile(r'text-xs font-semibold'))
            if not label_elem:
                continue
            
            label = label_elem.get_text(strip=True)
            # Get the value - it's in a span with class 'block text-sm'
            value_elem = cell.find('span', class_=re.compile(r'block text-sm'))
            if not value_elem:
                continue
            
            value = value_elem.get_text(strip=True)
            
            # Extract P/E Ratio
            if 'P/E Ratio' in label:
                try:
                    pe_ratio = float(value)
                    print(f"[INFO] P/E Ratio from Financial Summary for {symbol}: {pe_ratio}")
                except (ValueError, TypeError):
                    pass
            
            # Extract Price/Book
            elif 'Price/Book' in label:
                try:
                    price_to_book = float(value)
                    print(f"[INFO] Price/Book from Financial Summary for {symbol}: {price_to_book}")
                except (ValueError, TypeError):
                    pass
            
            # Extract Debt / Equity
            elif 'Debt / Equity' in label:
                try:
                    # Remove % sign if present
                    clean_value = value.replace('%', '').strip()
                    debt_to_equity = float(clean_value)
                    print(f"[INFO] Debt/Equity from Financial Summary for {symbol}: {debt_to_equity}%")
                except (ValueError, TypeError):
                    pass
        
        return {
            'pe_ratio': pe_ratio,
            'price_to_book': price_to_book,
            'debt_to_equity': debt_to_equity
        }
        
    except Exception as e:
        print(f"[ERROR] Failed to fetch financial ratios for {symbol}: {e}")
        return {
            'pe_ratio': None,
            'price_to_book': None,
            'debt_to_equity': None
        }

def fetch_balance_sheet_data(symbol, stock_info):
    """Fetch balance sheet data to get Total Equity"""
    url = f"{BASE_URL}{stock_info['url']}-balance-sheet"
    
    time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
    
    try:
        scraper = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "mobile": False}
        )
        resp = scraper.get(url)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Find the script with the data
        script_tag = soup.find("script", id="__NEXT_DATA__")
        if script_tag:
            data = json.loads(script_tag.string)
            
            # Try to get balance sheet data
            balance_sheet = safe_get(data, "props", "pageProps", "state", "balanceSheetStore", "balanceSheetDataAnnual", default={})
            
            if balance_sheet and balance_sheet.get("reports"):
                reports = balance_sheet.get("reports", [])
                if reports:
                    # Get the most recent report (last in the list)
                    latest_report = reports[-1]
                    year = latest_report.get("year")
                    indicators = latest_report.get("indicators", {})
                    
                    # Get total equity - could be dict or direct value
                    total_equity_raw = indicators.get("total_equity_standard")
                    if total_equity_raw is None:
                        total_equity_raw = indicators.get("total_equity")
                    
                    # Extract the numeric value
                    total_equity = extract_value_from_indicator(total_equity_raw)
                    
                    print(f"[DEBUG] Balance Sheet - Year {year}, Total Equity: {total_equity} million")
                    return total_equity
        
        # If JSON parsing fails, try HTML parsing
        print("[DEBUG] Trying to parse Total Equity from HTML table...")
        
        # Find all table rows
        rows = soup.find_all('tr')
        
        for row in rows:
            # Get all cells in the row
            cells = row.find_all('td')
            if len(cells) > 0:
                first_cell_text = cells[0].get_text(strip=True)
                
                # Look for Total Equity in the first column
                if 'Total Equity' in first_cell_text or 'Total Equity Standard' in first_cell_text:
                    print(f"[DEBUG] Found row with: {first_cell_text}")
                    # Look for numeric values in the following cells
                    for cell in cells[1:]:
                        cell_text = cell.get_text(strip=True)
                        if cell_text and cell_text != '-' and re.match(r'[\d,]+', cell_text):
                            try:
                                total_equity = float(cell_text.replace(',', ''))
                                print(f"[DEBUG] Found Total Equity from HTML: {total_equity} million")
                                return total_equity
                            except (ValueError, TypeError):
                                continue
        
        return None
        
    except Exception as e:
        print(f"[ERROR] Failed to fetch balance sheet data: {e}")
        return None

def fetch_income_statement_data(symbol, stock_info):
    """Fetch income statement data to get Net Income and Revenue"""
    url = f"{BASE_URL}{stock_info['url']}-income-statement"
    
    time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
    
    try:
        scraper = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "mobile": False}
        )
        resp = scraper.get(url)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Find the script with the data
        script_tag = soup.find("script", id="__NEXT_DATA__")
        if script_tag:
            data = json.loads(script_tag.string)
            
            # Try to get income statement data
            income_statement = safe_get(data, "props", "pageProps", "state", "incomeStatementStore", "incomeStatementDataAnnual", default={})
            
            if income_statement and income_statement.get("reports"):
                reports = income_statement.get("reports", [])
                if reports:
                    # Get the most recent report (last in the list)
                    latest_report = reports[-1]
                    year = latest_report.get("year")
                    indicators = latest_report.get("indicators", {})
                    
                    # Get net income and total revenue (could be dict or direct value)
                    net_income_raw = indicators.get("net_income")
                    total_revenue_raw = indicators.get("total_revenues_standard")
                    
                    # Extract numeric values
                    net_income = extract_value_from_indicator(net_income_raw)
                    total_revenue = extract_value_from_indicator(total_revenue_raw)
                    
                    print(f"[DEBUG] Income Statement - Year {year}, Net Income: {net_income} million, Revenue: {total_revenue} million")
                    
                    if net_income and total_revenue and total_revenue > 0:
                        profit_margin = (net_income / total_revenue) * 100
                        print(f"[INFO] Profit Margin from Income Statement: {profit_margin}%")
                        return profit_margin
        
        return None
        
    except Exception as e:
        print(f"[ERROR] Failed to fetch income statement data: {e}")
        return None

def fetch_stock_detail(symbol, stock_info):
    """Fetch data for a single stock from Investing.com"""
    # Fetch main page
    url = f"{BASE_URL}{stock_info['url']}"
    
    time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))
    
    try:
        scraper = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "mobile": False}
        )
        resp = scraper.get(url)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Extract instrument data from the state
        script_tag = soup.find("script", id="__NEXT_DATA__")
        if not script_tag:
            print(f"[WARN] Could not find __NEXT_DATA__ for {symbol}")
            return None
            
        data = json.loads(script_tag.string)
        
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
        
        # Extract company profile
        company_profile = safe_get(data, "props", "pageProps", "state", "companyProfileStore", "profile", default={})
        
        # Extract analyst/forecast data
        forecast = safe_get(data, "props", "pageProps", "state", "forecastStore", "forecast", default={})
        
        # Get current price and 52-week range
        current_price = price.get("last")
        week_52_low = price.get("fiftyTwoWeekLow")
        week_52_high = price.get("fiftyTwoWeekHigh")
        
        # Calculate distance from 52-week low
        close_to_low_pct = None
        if current_price and week_52_low and week_52_high and week_52_high > week_52_low:
            position_in_range = ((current_price - week_52_low) / (week_52_high - week_52_low)) * 100
            close_to_low_pct = round(100 - position_in_range, 2)
            print(f"[INFO] Distance from 52-week low for {symbol}: {close_to_low_pct}%")
        
        # Get shares outstanding
        shares_outstanding = fundamental.get("sharesOutstanding")
        print(f"[DEBUG] Shares Outstanding: {shares_outstanding}")
        
        # Try to get Book Value from multiple sources
        bvps = None
        
        # Method 1: Try to get from Key Metrics
        key_metrics_list = safe_get(data, "props", "pageProps", "state", "keyMetricsStore", "keyMetrics", "metrics", default=[])
        if isinstance(key_metrics_list, dict):
            key_metrics_list = key_metrics_list.get("metrics", [])
        
        if key_metrics_list:
            for item in key_metrics_list:
                if isinstance(item, dict) and item.get("slug") == "bv_share":
                    value = item.get("value", "")
                    try:
                        if value and value not in ("-", "NA", "N/A", ""):
                            clean_value = str(value).replace(',', '').strip()
                            if 'M' in clean_value:
                                bvps = float(clean_value.replace('M', ''))
                            elif 'B' in clean_value:
                                bvps = float(clean_value.replace('B', ''))
                            else:
                                bvps = float(clean_value)
                            print(f"[INFO] Book Value from Key Metrics: {bvps}")
                            break
                    except (ValueError, TypeError):
                        pass
        
        # Method 2: Fetch balance sheet data directly
        if bvps is None:
            print("[DEBUG] Fetching balance sheet data to calculate Book Value...")
            total_equity = fetch_balance_sheet_data(symbol, stock_info)
            
            if total_equity and shares_outstanding and shares_outstanding > 0:
                total_equity_value = total_equity * 1000000
                bvps = total_equity_value / shares_outstanding
                print(f"[INFO] Book Value calculated from balance sheet: {bvps} (Total Equity: {total_equity}M, Shares: {shares_outstanding})")
        
        # Get EPS from fundamental data
        eps = fundamental.get("eps")
        
        # Get P/E and other ratios
        pe_ratio = None
        price_to_book = None
        key_metrics_list = safe_get(data, "props", "pageProps", "state", "keyMetricsStore", "keyMetrics", "metrics", default=[])
        if isinstance(key_metrics_list, dict):
            key_metrics_list = key_metrics_list.get("metrics", [])
        
        if key_metrics_list:
            for item in key_metrics_list:
                if isinstance(item, dict):
                    slug = item.get("slug", "")
                    value = item.get("value", "")
                    
                    if slug == "pe_ltm":
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
        
        # Fetch financial ratios from summary page
        financial_ratios = fetch_financial_ratios(symbol, stock_info)
        
        # Use fetched values, falling back to previously extracted values
        final_pe_ratio = financial_ratios.get('pe_ratio') if financial_ratios.get('pe_ratio') is not None else pe_ratio
        final_price_to_book = financial_ratios.get('price_to_book') if financial_ratios.get('price_to_book') is not None else price_to_book
        final_debt_to_equity = financial_ratios.get('debt_to_equity')
        
        # Get profit margin from income statement
        profit_margin = fetch_income_statement_data(symbol, stock_info)
        
        # Calculate Graham Fair Value
        graham_value = None
        margin = None
        if bvps is not None and eps is not None:
            graham_value = graham_fair_value(eps, bvps)
            if current_price and graham_value:
                margin = margin_of_safety(current_price, graham_value)
            print(f"[INFO] Graham Fair Value: {graham_value}, Margin: {margin}")
        else:
            print(f"[WARN] Cannot calculate Graham Fair Value - BVPS: {bvps}, EPS: {eps}")

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
            "shares_outstanding": shares_outstanding,
            "eps": eps,
            "pe_ratio": final_pe_ratio,
            "dividend_yield": fundamental.get("yield"),
            "revenue": fundamental.get("revenueRaw"),
            "one_year_return": fundamental.get("oneYearReturn"),

            "price_to_book": final_price_to_book,
            "debt_to_equity": final_debt_to_equity,
            "profit_margin": profit_margin,

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
        import traceback
        traceback.print_exc()
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
    print("Testing with BS Attijari Bank...")
    result = fetch_single_stock("BS")

    if result:
        print("\n" + "=" * 80)
        print(f"COMPLETE DATA FOR {result['symbol']} - {result['name']}")
        print("=" * 80)

        for key, value in result.items():
            print(f"{key:35}: {value}")
    else:
        print("Failed to fetch data")