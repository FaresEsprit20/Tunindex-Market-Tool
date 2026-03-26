# ilboursa_elite.py
import cloudscraper
from bs4 import BeautifulSoup
import time, random

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
    """Convert string to float, clean spaces, commas, 'M' suffix"""
    if not text:
        return None
    cleaned = text.replace(" ", "").replace(",", ".").replace("M", "")
    try:
        return float(cleaned)
    except:
        return None

def extract_symbol(td):
    """Extract symbol from <td> containing <a href="/marches/cotation_SYMBOL">"""
    link = td.find("a")
    if link and "href" in link.attrs:
        href = link["href"]
        return href.split("cotation_")[-1]
    return td.get_text(strip=True)

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
            stock = {
                "symbol": symbol,
                "price": parse_number(tds[6].text),
                "open": parse_number(tds[1].text),
                "high": parse_number(tds[2].text),
                "low": parse_number(tds[3].text),
                "volume": parse_number(tds[4].text),
                "change_pct": tds[7].text.strip()
            }
            stocks.append(stock)
        except Exception as e:
            print(f"[WARN] Error parsing row {symbol}: {e}")
    if stocks:
        print(f"[INFO] Sample first symbol data: {stocks[0]}")
    return stocks

# -----------------------------
# Fetch Stock Details (Société Tab)
# -----------------------------
def fetch_stock_detail(url):
    time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))  # polite delay
    resp = scraper.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    data = {}
    for label, field in [
        ("VALORISATION", "market_cap_mtn"),
        ("Nombre de titres", "shares_outstanding"),
        ("BNPA", "eps"),
        ("PER", "pe_ratio"),
        ("Flottant", "float_pct"),
        ("Capitaux propres", "total_equity_mtn")
    ]:
        td = soup.find("td", string=label)
        if td:
            value = td.find_next_sibling("td").text.strip()
            data[field] = parse_number(value)
    print(f"[INFO] Sample stock details fetched: {data}")
    return data

# -----------------------------
# -----------------------------
# PROVIDER INTERFACE (Pipeline Compatible)
# -----------------------------
def get_provider_name():
    return "Ilboursa"

def fetch_market_data():
    return fetch_stock_prices()

def scrape_bvps(symbol):
    url = f"{BASE_URL}/marches/cotation_{symbol}"
    return fetch_stock_detail(url)

# -----------------------------
# Quick Test if run standalone
# -----------------------------
if __name__ == "__main__":
    print("🚀 Fetching stock list...")
    stock_list = fetch_stock_list()
    print(f"✅ Found {len(stock_list)} stocks")
    print("🚀 Fetching first 5 stock prices...")
    prices = fetch_stock_prices()
    for p in prices[:5]:
        print(p)
    print("🚀 Fetching first stock details...")
    details = fetch_stock_detail(stock_list[0]["detail_url"])
    print(details)