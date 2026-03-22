# services/enricher.py

from utils.fundamentals import calculate_bvps
from utils.fair_value import graham_fair_value, margin_of_safety


def enrich(stock):
    eps = stock.get("eps")
    bvps = stock.get("book_value_per_share")

    # Calculate BVPS if missing
    if not bvps:
        bvps = calculate_bvps(
            stock.get("total_equity"),
            stock.get("shares_outstanding")
        )
        stock["book_value_per_share"] = bvps

    # Fair value
    fair_value = graham_fair_value(eps, bvps)
    stock["fair_value"] = fair_value

    # Margin of safety
    mos = margin_of_safety(stock.get("price"), fair_value)
    stock["margin_of_safety"] = mos

    return stock