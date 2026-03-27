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
    """Parse percentage values including + and - signs and HTML entities"""
    if not text:
        return None
    cleaned = str(text).strip()
    # Handle HTML entities
    cleaned = cleaned.replace("&nbsp;", "").replace("&thinsp;", "")
    cleaned = cleaned.replace(" ", "").replace("\xa0", "")
    # Remove % sign
    cleaned = cleaned.replace("%", "")
    # Remove + sign for float conversion (keep -)
    cleaned = cleaned.replace("+", "")
    try:
        return float(cleaned)
    except:
        # Try to extract number from text like "+0,86%"
        match = re.search(r'([+-]?\d+[.,]?\d*)', text)
        if match:
            num_str = match.group(1).replace(",", ".")
            try:
                return float(num_str)
            except:
                return None
        return None

def extract_symbol(td):
    """Extract symbol from td containing <a href="/marches/cotation_SYMBOL">"""
    link = td.find("a")
    if link and "href" in link.attrs:
        href = link["href"]
        return href.split("cotation_")[-1]
    return td.get_text(strip=True)

def extract_sector(symbol):
    """Extract sector information from the secteur page"""
    url = f"{BASE_URL}/marches/secteur/{symbol}"
    time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))  # polite delay
    
    try:
        resp = scraper.get(url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Find the h1 tag that contains the sector information
        h1_tag = soup.find("h1", class_="h1a")
        if h1_tag:
            text = h1_tag.get_text(strip=True)
            # Extract the sector after "secteur"
            match = re.search(r'secteur\s+([A-Z\s&]+)', text, re.IGNORECASE)
            if match:
                sector = match.group(1).strip()
                return sector
    except Exception as e:
        print(f"[WARN] Could not extract sector for {symbol}: {e}")
    
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
# Fetch Stock Details - COMPLETE WITH ALL FIELDS
# -----------------------------
def fetch_stock_detail(symbol):
    """Fetch detailed price data for a specific stock including historical ranges and sector"""
    
    # First, get the sector information
    sector = extract_sector(symbol)
    
    # Then get the main stock details
    url = f"{BASE_URL}/marches/cotation_{symbol}"
    time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))  # polite delay
    
    resp = scraper.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    data = {
        "symbol": symbol,
        "sector": sector,
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
        "market_cap_mtn": None,
        # Historical fields - will be added dynamically
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
    
    # Extract change percentage
    change_elem = soup.find("div", class_="quote_up4") or soup.find("div", class_="quote_down4")
    if change_elem:
        change_text = change_elem.get_text(strip=True)
        data["change_pct"] = parse_percentage(change_text)
    
    # Extract open, high, low, prev close
    cot_v21 = soup.find("div", class_="cot_v21")
    if cot_v21:
        divs = cot_v21.find_all("div")
        if len(divs) >= 2:
            data["open"] = parse_number(divs[1].get_text(strip=True))
        if len(divs) >= 4:
            data["high"] = parse_number(divs[3].get_text(strip=True))
    
    cot_v22 = soup.find("div", class_="cot_v22")
    if cot_v22:
        divs = cot_v22.find_all("div")
        if len(divs) >= 2:
            data["prev_close"] = parse_number(divs[1].get_text(strip=True))
        if len(divs) >= 4:
            data["low"] = parse_number(divs[3].get_text(strip=True))
    
    # Extract volume, volatility, capital exchange, market cap
    cot_v3 = soup.find("div", class_="cot_v3")
    if cot_v3:
        v21_in_v3 = cot_v3.find("div", class_="cot_v21")
        if v21_in_v3:
            inner_divs = v21_in_v3.find_all("div")
            if len(inner_divs) >= 2:
                data["volume"] = parse_number(inner_divs[1].get_text(strip=True))
            if len(inner_divs) >= 4:
                data["volatility_pct"] = parse_percentage(inner_divs[3].get_text(strip=True))
        
        v22_in_v3 = cot_v3.find("div", class_="cot_v22")
        if v22_in_v3:
            inner_divs = v22_in_v3.find_all("div")
            if len(inner_divs) >= 2:
                data["capital_exchange_pct"] = parse_percentage(inner_divs[1].get_text(strip=True))
            if len(inner_divs) >= 4:
                data["market_cap_mtn"] = parse_number(inner_divs[3].get_text(strip=True))
    
    # Alternative volume extraction
    if data["volume"] is None:
        vol_elem = soup.find(id="vol")
        if vol_elem:
            data["volume"] = parse_number(vol_elem.get_text(strip=True))
    
    # Extract historical data and flatten
    period_mapping = {
        "1 semaine": "week",
        "1 mois": "month",
        "1er janvier": "ytd",
        "1 an": "year",
        "3 ans": "three_years",
        "5 ans": "five_years",
        "10 ans": "ten_years"
    }
    
    hist_table = soup.find("table", class_="tableVar")
    if hist_table:
        rows = hist_table.find_all("tr")[1:]  # Skip header
        for row in rows:
            cells = row.find_all("td")
            if len(cells) >= 4:
                period = cells[0].get_text(strip=True)
                high = parse_number(cells[1].get_text(strip=True))
                low = parse_number(cells[2].get_text(strip=True))
                change = parse_percentage(cells[3].get_text(strip=True))
                
                field_prefix = period_mapping.get(period)
                if field_prefix:
                    data[f"{field_prefix}_high"] = high
                    data[f"{field_prefix}_low"] = low
                    data[f"{field_prefix}_change"] = change
    
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
    for key, value in sorted(result.items()):
        if value is not None:
            print(f"  {key}: {value}")