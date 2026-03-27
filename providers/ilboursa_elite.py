# ilboursa_elite.py
import cloudscraper
from bs4 import BeautifulSoup
import time
import random
import re

# -----------------------------
# Configuration
# -----------------------------
BASE_URL = "https://www.ilboursa.com"
DELAY_MIN = 2        # polite scraping delay (seconds)
DELAY_MAX = 4

# -----------------------------
# Scraper Initialization
# -----------------------------
scraper = cloudscraper.create_scraper(
    browser={"browser": "chrome", "platform": "windows", "mobile": False}
)

# -----------------------------
# Helper Functions
# -----------------------------
def parse_number(text):
    """Convert string to float, clean spaces, commas, 'M' suffix, and thousand separators"""
    if not text:
        return None
    # Clean the text
    cleaned = str(text).strip()
    # Remove HTML entities
    cleaned = cleaned.replace("&nbsp;", "").replace("&thinsp;", "")
    # Remove spaces
    cleaned = cleaned.replace(" ", "").replace("\xa0", "")
    # Handle thousand separators (French format uses space)
    cleaned = cleaned.replace(",", ".")  # Replace comma with dot for decimal
    # Remove TND, MTND, etc
    cleaned = re.sub(r'[A-Za-z]+$', '', cleaned).strip()
    # Remove % sign
    cleaned = cleaned.replace("%", "")
    try:
        return float(cleaned)
    except:
        return None

def parse_percentage(text):
    """Parse percentage values including + and - signs"""
    if not text:
        return None
    cleaned = str(text).strip()
    cleaned = cleaned.replace("&nbsp;", "").replace(" ", "").replace("%", "")
    try:
        return float(cleaned)
    except:
        return None

def extract_symbol(td):
    """Extract symbol from 67 containing <a href="/marches/cotation_SYMBOL">"""
    link = td.find("a")
    if link and "href" in link.attrs:
        href = link["href"]
        return href.split("cotation_")[-1]
    return td.get_text(strip=True)

def find_text_by_label(soup, label_text):
    """Find the next sibling or parent text after a label"""
    # Try to find the label text in various structures
    # Look for div containing the label
    for elem in soup.find_all(['div', 'td']):
        if label_text in elem.get_text():
            # Get the next element or sibling
            next_elem = elem.find_next_sibling()
            if next_elem:
                return next_elem.get_text(strip=True)
            # Or get the parent's next sibling
            parent = elem.parent
            if parent:
                next_parent = parent.find_next_sibling()
                if next_parent:
                    return next_parent.get_text(strip=True)
    return None

# -----------------------------
# Fetch A-Z Stock List
# -----------------------------
def fetch_stock_list():
    url = f"{BASE_URL}/marches/aaz"
    resp = scraper.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    table = next(t for t in soup.find_all("table") if "nom" in t.text.lower())
    stocks = []
    for tr in table.find_all("tr")[1:]:
        tds = tr.find_all("td")
        if len(tds) < 4:
            continue
        symbol = extract_symbol(tds[0])
        stocks.append({
            "symbol": symbol,
            "detail_url": BASE_URL + tds[0].find("a")["href"]
        })
    return stocks

# -----------------------------
# Fetch Stock Prices (Intraday)
# -----------------------------
def fetch_stock_prices():
    url = f"{BASE_URL}/marches/aaz"
    resp = scraper.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    table = next(t for t in soup.find_all("table") if "nom" in t.text.lower())
    stocks = []

    for tr in table.find_all("tr")[1:]:
        tds = tr.find_all("td")
        if len(tds) < 8:
            continue

        symbol = extract_symbol(tds[0])
        try:
            # Extract price from the 7th column (index 6)
            price_text = tds[6].get_text(strip=True)
            # Extract change from the 8th column (index 7)
            change_text = tds[7].get_text(strip=True)
            
            stock = {
                "symbol": symbol,
                "price": parse_number(price_text),
                "open": parse_number(tds[1].get_text(strip=True)),
                "high": parse_number(tds[2].get_text(strip=True)),
                "low": parse_number(tds[3].get_text(strip=True)),
                "volume": parse_number(tds[4].get_text(strip=True)),
                "change_pct": parse_percentage(change_text)
            }
            stocks.append(stock)
        except Exception as e:
            print(f"[WARN] Error parsing row {symbol}: {e}")
    
    if stocks:
        print(f"[INFO] Sample first symbol data: {stocks[0]}")
    return stocks

# -----------------------------
# Fetch Stock Details - FIXED SELECTORS
# -----------------------------
def fetch_stock_detail(symbol):
    """Fetch detailed price data for a specific stock"""
    url = f"{BASE_URL}/marches/cotation_{symbol}"
    time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))  # polite delay
    
    resp = scraper.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    data = {
        "symbol": symbol,
        "isin": None,
        "ticker": None,
        "price": None,
        "change_pct": None,
        "open": None,
        "high": None,
        "low": None,
        "prev_close": None,
        "volume": None,
        "volatility_pct": None,
        "capital_exchange_pct": None,
        "market_cap_mtn": None
    }
    
    # Extract ISIN and Ticker from the header section
    isin_elem = soup.find("div", class_="coth1")
    if isin_elem:
        isin_text = isin_elem.get_text(strip=True)
        isin_match = re.search(r'ISIN\s*:\s*([A-Z0-9]+)', isin_text)
        if isin_match:
            data["isin"] = isin_match.group(1)
        ticker_match = re.search(r'Ticker\s*:\s*([A-Z0-9]+)', isin_text)
        if ticker_match:
            data["ticker"] = ticker_match.group(1)
    
    # Extract current price - from cot_v1b div
    price_elem = soup.find("div", class_="cot_v1b")
    if price_elem:
        price_text = price_elem.get_text(strip=True)
        data["price"] = parse_number(price_text)
        print(f"[DEBUG] {symbol} - Price: {price_text} -> {data['price']}")
    
    # Extract change percentage - from quote_up4 or quote_down4
    change_elem = soup.find("div", class_="quote_up4") or soup.find("div", class_="quote_down4")
    if change_elem:
        change_text = change_elem.get_text(strip=True)
        data["change_pct"] = parse_percentage(change_text)
        print(f"[DEBUG] {symbol} - Change: {change_text} -> {data['change_pct']}")
    
    # Extract open, high, low, prev close from the cot_v21 and cot_v22 structures
    # For Open and High (in cot_v21)
    cot_v21 = soup.find("div", class_="cot_v21")
    if cot_v21:
        divs = cot_v21.find_all("div")
        if len(divs) >= 4:
            # Structure: first div is "OUVERTURE", second is value, third is "+ HAUT", fourth is value
            if len(divs) >= 2:
                data["open"] = parse_number(divs[1].get_text(strip=True))
            if len(divs) >= 4:
                data["high"] = parse_number(divs[3].get_text(strip=True))
    
    # For Prev Close and Low (in cot_v22)
    cot_v22 = soup.find("div", class_="cot_v22")
    if cot_v22:
        divs = cot_v22.find_all("div")
        if len(divs) >= 4:
            # Structure: first div is "CLOTURE VEILLE", second is value, third is "+ BAS", fourth is value
            if len(divs) >= 2:
                data["prev_close"] = parse_number(divs[1].get_text(strip=True))
            if len(divs) >= 4:
                data["low"] = parse_number(divs[3].get_text(strip=True))
    
    # Extract volume and volatility from cot_v21 (second part)
    cot_v3 = soup.find("div", class_="cot_v3")
    if cot_v3:
        # Find all divs within cot_v3
        v3_divs = cot_v3.find_all("div")
        # Volume is in the second div of cot_v21 within cot_v3
        v21_in_v3 = cot_v3.find("div", class_="cot_v21")
        if v21_in_v3:
            inner_divs = v21_in_v3.find_all("div")
            if len(inner_divs) >= 2:
                # Volume value
                volume_text = inner_divs[1].get_text(strip=True)
                data["volume"] = parse_number(volume_text)
            if len(inner_divs) >= 4:
                # Volatility value
                vol_text = inner_divs[3].get_text(strip=True)
                data["volatility_pct"] = parse_percentage(vol_text)
        
        # Extract capital exchange and market cap from cot_v22 within cot_v3
        v22_in_v3 = cot_v3.find("div", class_="cot_v22")
        if v22_in_v3:
            inner_divs = v22_in_v3.find_all("div")
            if len(inner_divs) >= 2:
                # Capital exchange
                cap_ex_text = inner_divs[1].get_text(strip=True)
                data["capital_exchange_pct"] = parse_percentage(cap_ex_text)
            if len(inner_divs) >= 4:
                # Market cap
                market_cap_text = inner_divs[3].get_text(strip=True)
                data["market_cap_mtn"] = parse_number(market_cap_text)
    
    # Alternative: Extract volume from id="vol" if not found
    if data["volume"] is None:
        vol_elem = soup.find(id="vol")
        if vol_elem:
            data["volume"] = parse_number(vol_elem.get_text(strip=True))
    
    print(f"[DEBUG] {symbol} - Final data: price={data['price']}, open={data['open']}, high={data['high']}, low={data['low']}, volume={data['volume']}")
    return data

# -----------------------------
# PROVIDER INTERFACE (Pipeline Compatible)
# -----------------------------
def get_provider_name():
    return "Ilboursa"

def fetch_market_data():
    """Fetch all stocks data from the A-Z page"""
    return fetch_stock_prices()

def scrape_bvps(symbol):
    """Fetch detailed data for a specific stock"""
    return fetch_stock_detail(symbol)

# -----------------------------
# Example Usage
# -----------------------------
if __name__ == "__main__":
    # Test with AB (Amen Bank)
    print("Testing with AB (Amen Bank)...")
    result = scrape_bvps("AB")
    print("\nFinal extracted data:")
    for key, value in result.items():
        if value is not None:
            print(f"  {key}: {value}")