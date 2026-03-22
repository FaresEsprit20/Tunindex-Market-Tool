# services/parser.py

from bs4 import BeautifulSoup


def extract_best_table(html):
    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table")

    if not tables:
        return None

    # Choose largest table
    return max(tables, key=lambda t: len(t.find_all("tr")))


def extract_headers(table):
    headers = []
    for th in table.find_all("th"):
        headers.append(th.get_text(strip=True).lower())
    return headers


def extract_rows(table):
    rows = []
    for tr in table.find_all("tr")[1:]:
        cols = [td.get_text(strip=True) for td in tr.find_all("td")]
        if cols:
            rows.append(cols)
    return rows