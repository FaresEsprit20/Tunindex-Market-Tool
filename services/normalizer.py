# services/normalizer.py

def clean_number(val):
    if val is None:
        return None
    try:
        val = val.replace(" ", "").replace(",", ".")
        return float(val)
    except:
        return None


def normalize_stock(raw):
    return {
        "symbol": raw.get("symbol"),
        "company_name": raw.get("company_name"),

        "ownership_type": raw.get("ownership_type"),
        "activity_type": raw.get("activity_type"),

        "price": clean_number(raw.get("price")),
        "open_price": clean_number(raw.get("open_price")),
        "high_price": clean_number(raw.get("high_price")),
        "low_price": clean_number(raw.get("low_price")),
        "volume": clean_number(raw.get("volume")),
        "market_cap": clean_number(raw.get("market_cap")),

        "eps": clean_number(raw.get("eps")),
        "book_value_per_share": clean_number(raw.get("book_value_per_share")),
        "total_equity": clean_number(raw.get("total_equity")),
        "shares_outstanding": clean_number(raw.get("shares_outstanding")),

        "pe_ratio": clean_number(raw.get("pe_ratio")),
        "roe": clean_number(raw.get("roe")),
        "roa": clean_number(raw.get("roa")),
        "debt_equity": clean_number(raw.get("debt_equity")),
        "profit_margin": clean_number(raw.get("profit_margin")),

        "fair_value": raw.get("fair_value"),
        "margin_of_safety": raw.get("margin_of_safety"),

        "source": raw.get("source")
    }