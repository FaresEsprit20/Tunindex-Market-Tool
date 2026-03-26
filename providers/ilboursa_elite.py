# providers/ilboursa_elite.py

from bs4 import BeautifulSoup
from difflib import get_close_matches
from services.fetcher import fetch
from utils.captcha_detector import has_captcha
from utils.fundamentals import calculate_bvps
from utils.simple_cache import get as cache_get, set as cache_set

BASE_URL = "https://www.ilboursa.com"


def get_provider_name():
    return "Ilboursa"


# -------------------------
# MARKET DATA (ELITE) with CACHE
# -------------------------
def fetch_market_data():
    # Try cache first (15 minutes)
    cached = cache_get("market_data_ilboursa")
    if cached:
        return cached

    html = fetch(f"{BASE_URL}/marches/aaz", use_proxy=False)
    if not html or has_captcha(html):
        return []

    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")
    if not tables:
        return []

    table = max(tables, key=lambda t: len(t.find_all("tr")))
    headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
    col_map = detect_columns(headers)

    rows = []
    for tr in table.find_all("tr")[1:]:
        tds = tr.find_all("td")
        if len(tds) < 3:
            continue

        row = {}
        confidence = 0
        for field, idx in col_map.items():
            if idx is None:
                continue
            try:
                val = tds[idx].get_text(strip=True)
                if field in ["price", "open_price", "high_price", "low_price", "volume"]:
                    val = parse_number(val)
                row[field] = val
                confidence += 1
            except:
                continue

        if confidence >= 2:
            row["source"] = "ilboursa"
            rows.append(row)

    # Cache results for 15 minutes
    cache_set("market_data_ilboursa", rows, ttl=900)
    return rows


# -------------------------
# DETAIL SCRAPER (BVPS) with CACHE
# -------------------------
def scrape_bvps(symbol):
    cached = cache_get(f"bvps_{symbol}")
    if cached:
        return cached

    html = fetch(f"{BASE_URL}/marches/cotation_{symbol}", use_proxy=False)
    if not html or has_captcha(html):
        return None

    soup = BeautifulSoup(html, "html.parser")
    equity = find_value(soup, ["capitaux propres", "fonds propres"])
    shares = find_value(soup, ["nombre d'actions", "actions"])

    result = {
        "total_equity": equity,
        "shares_outstanding": shares,
        "book_value_per_share": calculate_bvps(equity, shares)
    }

    # Cache for 1 hour
    cache_set(f"bvps_{symbol}", result, ttl=3600)
    return result


# -------------------------
# HELPERS
# -------------------------
def detect_columns(headers):
    mapping = {
        "symbol": ["valeur", "symbole"],
        "company_name": ["nom", "désignation"],
        "price": ["dernier", "cours"],
        "open_price": ["ouverture"],
        "high_price": ["haut"],
        "low_price": ["bas"],
        "volume": ["volume"]
    }
    col_map = {}
    for field, keywords in mapping.items():
        col_map[field] = find_column(headers, keywords)
    return col_map


def find_column(headers, keywords):
    for kw in keywords:
        match = get_close_matches(kw, headers, n=1, cutoff=0.5)
        if match:
            return headers.index(match[0])
    return None


def find_value(soup, keywords):
    import re

    for tr in soup.find_all("tr"):
        tds = tr.find_all(["td", "th"])
        if len(tds) < 2:
            continue

        label = tds[0].get_text(strip=True).lower()
        if any(k in label for k in keywords):
            return extract_number(tds[1].get_text())

    text = soup.get_text(" ", strip=True).lower()
    for k in keywords:
        if k in text:
            match = re.search(r"[\d\.,]+", text)
            if match:
                return extract_number(match.group())
    return None


def parse_number(val):
    try:
        return float(val.replace(" ", "").replace(",", "."))
    except:
        return None


def extract_number(val):
    try:
        return float(val.replace(" ", "").replace(",", "."))
    except:
        return None