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

def calculate_book_value_per_share(data):
    """Extract Total Equity and Shares Outstanding from financial statements and calculate Book Value Per Share"""
    try:
        total_equity = None
        shares_outstanding = None
        
        # Get shares outstanding from fundamental data
        shares_outstanding = safe_get(data, "props", "pageProps", "state", "equityStore", "instrument", "fundamental", "sharesOutstanding", default=None)
        print(f"[DEBUG] Shares Outstanding from fundamental: {shares_outstanding}")
        
        # If shares not found, try key metrics
        if shares_outstanding is None:
            key_metrics = safe_get(data, "props", "pageProps", "state", "keyMetricsStore", "keyMetrics", "metrics", default=[])
            for metric in key_metrics:
                if isinstance(metric, dict) and metric.get("slug") == "shares_out":
                    value = metric.get("value", "")
                    try:
                        if value:
                            clean_value = str(value).replace(',', '').strip()
                            if 'M' in clean_value:
                                shares_outstanding = float(clean_value.replace('M', '')) * 1000000
                            elif 'B' in clean_value:
                                shares_outstanding = float(clean_value.replace('B', '')) * 1000000000
                            else:
                                shares_outstanding = float(clean_value)
                            print(f"[DEBUG] Shares Outstanding from Key Metrics: {shares_outstanding}")
                    except (ValueError, TypeError):
                        pass
                    break
        
        # Try to get Total Equity from balanceSheetStore (most reliable)
        balance_sheet_annual = safe_get(data, "props", "pageProps", "state", "balanceSheetStore", "balanceSheetDataAnnual", default={})
        
        if balance_sheet_annual and balance_sheet_annual.get("reports"):
            reports = balance_sheet_annual.get("reports", [])
            if reports:
                # Get the most recent report
                latest_report = reports[-1]
                indicators = latest_report.get("indicators", {})
                
                # Look for Total Equity - could be under different keys
                total_equity = indicators.get("total_equity_standard")
                if total_equity is None:
                    total_equity = indicators.get("total_equity")
                if total_equity is None:
                    # Try to find total equity by looking for equity-related fields
                    for key, value in indicators.items():
                        if 'equity' in key.lower() and 'total' in key.lower():
                            total_equity = value
                            break
                
                print(f"[DEBUG] Total Equity from Balance Sheet: {total_equity}")
        
        # If not found in balance sheet, try financialStatementsStore
        if total_equity is None:
            annual_reports = safe_get(data, "props", "pageProps", "state", "financialStatementsStore", "annualReports", default=[])
            
            if annual_reports and len(annual_reports) > 0:
                latest_report = annual_reports[-1]
                total_equity = latest_report.get("indicators", {}).get("total_equity_standard")
                if total_equity is None:
                    total_equity = latest_report.get("indicators", {}).get("total_equity")
                print(f"[DEBUG] Total Equity from financialStatementsStore: {total_equity}")
        
        # If still not found, try to calculate from Price/Book ratio if available
        if total_equity is None and shares_outstanding:
            # Get current price and price_to_book from fundamental or key metrics
            current_price = safe_get(data, "props", "pageProps", "state", "equityStore", "instrument", "price", "last", default=None)
            price_to_book = None
            
            # Try to get price_to_book from key metrics
            key_metrics = safe_get(data, "props", "pageProps", "state", "keyMetricsStore", "keyMetrics", "metrics", default=[])
            for metric in key_metrics:
                if isinstance(metric, dict) and metric.get("slug") == "price_to_book":
                    value = metric.get("value", "")
                    try:
                        if value and value not in ("-", "NA", "N/A", ""):
                            clean_value = str(value).replace(',', '').replace('x', '').strip()
                            price_to_book = float(clean_value)
                            print(f"[DEBUG] Price/Book from Key Metrics: {price_to_book}")
                    except (ValueError, TypeError):
                        pass
                    break
            
            # If we have price_to_book and current price, we can calculate BVPS
            if price_to_book and current_price and price_to_book > 0:
                bvps = current_price / price_to_book
                print(f"[INFO] Book Value calculated from Price/Book ratio: {bvps} (Price: {current_price}, P/B: {price_to_book})")
                return round(bvps, 2)
        
        # Calculate BVPS if we have both values
        if total_equity and shares_outstanding and shares_outstanding > 0:
            bvps = total_equity / shares_outstanding
            print(f"[INFO] Calculated Book Value Per Share: {bvps} (Total Equity: {total_equity}, Shares: {shares_outstanding})")
            return round(bvps, 2)
        
        # If we have shares but no total equity, try to get book value from key metrics
        if shares_outstanding and total_equity is None:
            key_metrics = safe_get(data, "props", "pageProps", "state", "keyMetricsStore", "keyMetrics", "metrics", default=[])
            for metric in key_metrics:
                if isinstance(metric, dict) and metric.get("slug") == "bv_share":
                    value = metric.get("value", "")
                    try:
                        if value and value not in ("-", "NA", "N/A", ""):
                            bvps = float(str(value).replace(',', '').strip())
                            print(f"[INFO] Book Value from Key Metrics: {bvps}")
                            return bvps
                    except (ValueError, TypeError):
                        pass
        
        return None
        
    except Exception as e:
        print(f"[ERROR] Failed to calculate Book Value Per Share: {e}")
        return None

def calculate_profit_margin_from_financials(data):
    """Extract Net Income and Total Revenue from financial statements and calculate profit margin"""
    try:
        # Try to get annual reports from financialStatementsStore
        annual_reports = safe_get(data, "props", "pageProps", "state", "financialStatementsStore", "annualReports", default=[])
        
        if annual_reports and len(annual_reports) > 0:
            # Get the most recent annual report (last in the list)
            latest_report = annual_reports[-1]
            
            # Extract Net Income and Total Revenue
            net_income = latest_report.get("indicators", {}).get("net_income")
            total_revenue = latest_report.get("indicators", {}).get("total_revenues_standard")
            
            print(f"[DEBUG] Net Income from financialStatementsStore: {net_income}")
            print(f"[DEBUG] Total Revenue from financialStatementsStore: {total_revenue}")
            
            if net_income and total_revenue and total_revenue > 0:
                profit_margin = (net_income / total_revenue) * 100
                return round(profit_margin, 2)
        
        # Try to get from incomeStatementStore
        income_statement = safe_get(data, "props", "pageProps", "state", "incomeStatementStore", "incomeStatementDataAnnual", default={})
        
        if income_statement and income_statement.get("reports"):
            reports = income_statement.get("reports", [])
            if reports:
                # Get the most recent report
                latest_report = reports[-1]
                indicators = latest_report.get("indicators", {})
                
                net_income = indicators.get("net_income")
                total_revenue = indicators.get("total_revenues_standard")
                
                print(f"[DEBUG] Net Income from Income Statement: {net_income}")
                print(f"[DEBUG] Total Revenue from Income Statement: {total_revenue}")
                
                if net_income and total_revenue and total_revenue > 0:
                    profit_margin = (net_income / total_revenue) * 100
                    return round(profit_margin, 2)
        
        # Try to get from key metrics (as fallback)
        key_metrics = safe_get(data, "props", "pageProps", "state", "keyMetricsStore", "keyMetrics", "metrics", default=[])
        
        if key_metrics:
            net_income = None
            total_revenue = None
            
            for metric in key_metrics:
                if isinstance(metric, dict):
                    slug = metric.get("slug", "")
                    value = metric.get("value", "")
                    
                    if slug == "ni_avail_excl" and value:
                        try:
                            # Clean value (remove commas, K/M/B suffixes)
                            clean_value = str(value).replace(',', '').strip()
                            if 'B' in clean_value:
                                net_income = float(clean_value.replace('B', '')) * 1000000000
                            elif 'M' in clean_value:
                                net_income = float(clean_value.replace('M', '')) * 1000000
                            else:
                                net_income = float(clean_value)
                            print(f"[DEBUG] Net Income from Key Metrics: {net_income}")
                        except (ValueError, TypeError):
                            pass
                    
                    elif slug == "total_rev" and value:
                        try:
                            clean_value = str(value).replace(',', '').strip()
                            if 'B' in clean_value:
                                total_revenue = float(clean_value.replace('B', '')) * 1000000000
                            elif 'M' in clean_value:
                                total_revenue = float(clean_value.replace('M', '')) * 1000000
                            else:
                                total_revenue = float(clean_value)
                            print(f"[DEBUG] Total Revenue from Key Metrics: {total_revenue}")
                        except (ValueError, TypeError):
                            pass
            
            if net_income and total_revenue and total_revenue > 0:
                profit_margin = (net_income / total_revenue) * 100
                return round(profit_margin, 2)
        
        # Try to get from fundamental data (as last resort)
        fundamental = safe_get(data, "props", "pageProps", "state", "equityStore", "instrument", "fundamental", default={})
        
        if fundamental:
            revenue_raw = fundamental.get("revenueRaw")
            eps = fundamental.get("eps")
            shares_outstanding = fundamental.get("sharesOutstanding")
            
            # If we have EPS and shares outstanding, we can estimate net income
            if eps and shares_outstanding:
                net_income_est = eps * shares_outstanding
                if revenue_raw:
                    profit_margin = (net_income_est / revenue_raw) * 100
                    print(f"[DEBUG] Profit Margin from EPS * Shares (estimated): {profit_margin}%")
                    return round(profit_margin, 2)
        
        return None
        
    except Exception as e:
        print(f"[ERROR] Failed to calculate profit margin from financials: {e}")
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
        
        # If BVPS is still None, calculate it manually from financial data
        if bvps is None:
            bvps = calculate_book_value_per_share(data)
            if bvps:
                print(f"[INFO] Book Value manually calculated: {bvps}")
            else:
                print(f"[WARN] Could not calculate Book Value for {symbol}")
        
        # Get EPS from fundamental data
        eps = fundamental.get("eps")
        
        # Fetch financial ratios (P/E, P/B, Debt/Equity) from financial summary page
        financial_ratios = fetch_financial_ratios(symbol, stock_info)
        
        # Use the fetched values, falling back to previously extracted values if needed
        final_pe_ratio = financial_ratios.get('pe_ratio') if financial_ratios.get('pe_ratio') is not None else pe_ratio
        final_price_to_book = financial_ratios.get('price_to_book') if financial_ratios.get('price_to_book') is not None else price_to_book
        final_debt_to_equity = financial_ratios.get('debt_to_equity')
        
        # Calculate profit margin from financial data
        profit_margin = calculate_profit_margin_from_financials(data)
        
        # Calculate Graham Fair Value using BVPS (only if bvps is available)
        graham_value = None
        margin = None
        if bvps is not None and eps is not None:
            graham_value = graham_fair_value(eps, bvps)
            if current_price and graham_value:
                margin = margin_of_safety(current_price, graham_value)
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
            "shares_outstanding": fundamental.get("sharesOutstanding"),
            "eps": eps,
            "pe_ratio": final_pe_ratio,
            "dividend_yield": fundamental.get("yield"),
            "revenue": fundamental.get("revenueRaw"),
            "one_year_return": fundamental.get("oneYearReturn"),

            "price_to_book": final_price_to_book,
            "debt_to_equity": final_debt_to_equity,
            "profit_margin": profit_margin,  # Calculated from financial statements

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