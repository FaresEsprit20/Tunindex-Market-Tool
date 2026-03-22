# providers/bvmt.py

from bs4 import BeautifulSoup
from services.fetcher import fetch


def get_provider_name():
    return "BVMT"


def fetch_market_data():
    html = fetch("https://www.bvmt.com.tn", use_proxy=False)

    if not html:
        return []

    soup = BeautifulSoup(html, "html.parser")

    tables = soup.find_all("table")
    if not tables:
        return []

    table = max(tables, key=lambda t: len(t.find_all("tr")))

    rows = []

    for tr in table.find_all("tr")[1:]:
        cols = [td.get_text(strip=True) for td in tr.find_all("td")]

        if len(cols) < 3:
            continue

        rows.append({
            "symbol": cols[0],
            "company_name": cols[1],
            "price": safe_float(cols[2]),
            "source": "bvmt"
        })

    return rows


def safe_float(x):
    try:
        return float(x.replace(",", "."))
    except:
        return None