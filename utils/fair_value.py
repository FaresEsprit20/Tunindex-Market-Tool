import math

def graham_fair_value(eps, bvps):
    if not eps or not bvps or eps < 0 or bvps < 0:
        return None
    try:
        # Graham's formula: sqrt(22.5 * EPS * BVPS)
        return math.sqrt(22.5 * eps * bvps)
    except:
        return None

def margin_of_safety(price, fair_value):
    if not price or not fair_value or fair_value <= 0:
        return None
    try:
        # returns as a percentage (e.g., 37.3)
        return round(((fair_value - price) / fair_value) * 100, 2)
    except:
        return None