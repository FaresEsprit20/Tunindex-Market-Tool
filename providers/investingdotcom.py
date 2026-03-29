# investing_tunisia.py
import cloudscraper
import json
from bs4 import BeautifulSoup

# -----------------------------
# Configuration
# -----------------------------
BASE_URL = "https://www.investing.com/equities/tunisia"

def fetch_investing_tunisia():
    """Scrape Tunisia stocks from Investing.com using embedded JSON data"""
    scraper = cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "mobile": False}
    )
    
    resp = scraper.get(BASE_URL)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    
    # Find the __NEXT_DATA__ script tag
    script_tag = soup.find("script", id="__NEXT_DATA__")
    if not script_tag:
        print("[ERROR] Could not find __NEXT_DATA__ script tag")
        return []
    
    # Parse the JSON data
    data = json.loads(script_tag.string)
    
    # Navigate to the assets collection where stock data is stored
    stocks = []
    try:
        assets_collection = data.get("props", {}).get("pageProps", {}).get("state", {}).get("assetsCollectionStore", {}).get("assetsCollection", {}).get("_collection", [])
        
        for asset in assets_collection:
            # Extract basic information
            stock = {
                "symbol": asset.get("symbol"),
                "name": asset.get("title"),
                "country_flag": asset.get("flagCode"),
                "country_name": asset.get("flagName"),
                "exchange_id": asset.get("exchangeId"),
                "is_cfd": asset.get("isCFD"),
                "url": asset.get("url"),
                "last": asset.get("last"),
                "change_pct": asset.get("changeOneDayPercent"),
                "volume": asset.get("volumeOneDay"),
            }
            stocks.append(stock)
        
        print(f"[INFO] Retrieved {len(stocks)} stocks from Investing.com")
        return stocks
        
    except Exception as e:
        print(f"[ERROR] Failed to parse __NEXT_DATA__: {e}")
        import traceback
        traceback.print_exc()
        return []

# -----------------------------
# PROVIDER INTERFACE (Pipeline Compatible)
# -----------------------------
def get_provider_name():
    return "Investing.com"

def fetch_market_data():
    """Fetch all Tunisia stocks data"""
    return fetch_investing_tunisia()

# -----------------------------
# Display ALL symbols with basic information
# -----------------------------
if __name__ == "__main__":
    stocks = fetch_market_data()
    
    if stocks:
        print(f"\n{'='*100}")
        print(f"📊 ALL {len(stocks)} TUNISIAN STOCKS - BASIC INFORMATION")
        print(f"{'='*100}\n")
        
        # Print header
        print(f"{'#':<4} | {'Symbol':<10} | {'Name':<40} | {'Country':<15} | {'Exch':<6} | {'CFD':<5} | URL")
        print(f"{'-'*4}-+-{'-'*10}-+-{'-'*40}-+-{'-'*15}-+-{'-'*6}-+-{'-'*5}-+{'-'*50}")
        
        # Print each stock with index number
        for idx, stock in enumerate(stocks, 1):
            symbol = stock.get('symbol', 'N/A')
            name = stock.get('name', 'N/A')[:40]  # Truncate long names to 40 chars
            country = f"{stock.get('country_flag', 'N/A')} - {stock.get('country_name', 'N/A')}"
            exchange_id = stock.get('exchange_id', 'N/A')
            is_cfd = stock.get('is_cfd', 'N/A')
            url = stock.get('url', 'N/A')
            
            print(f"{idx:<4} | {symbol:<10} | {name:<40} | {country:<15} | {exchange_id:<6} | {is_cfd:<5} | {url}")
        
        print(f"\n{'='*100}")
        print(f"✅ Total stocks displayed: {len(stocks)}")
        print(f"{'='*100}")
        
        # Also show a quick summary of price data for all stocks
        print(f"\n📈 PRICE SUMMARY FOR ALL {len(stocks)} STOCKS:")
        print(f"{'='*80}")
        print(f"{'Symbol':<10} | {'Name':<35} | {'Price':<10} | {'Change %':<10} | {'Volume'}")
        print(f"{'-'*10}-+-{'-'*35}-+-{'-'*10}-+-{'-'*10}-+{'-'*12}")
        
        for stock in stocks:
            symbol = stock.get('symbol', 'N/A')
            name = stock.get('name', 'N/A')[:35]
            last = stock.get('last', 'N/A')
            change = stock.get('change_pct', 'N/A')
            volume = stock.get('volume', 'N/A')
            
            if last is not None:
                print(f"{symbol:<10} | {name:<35} | {last:<10} | {change:<10}% | {volume}")
            else:
                print(f"{symbol:<10} | {name:<35} | {'N/A':<10} | {'N/A':<10} | {volume}")
        
        print(f"\n{'='*80}")
    else:
        print("No stocks retrieved.")