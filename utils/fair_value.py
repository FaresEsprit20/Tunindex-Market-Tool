import math

def graham_fair_value(eps, bvps):
    if not eps or not bvps:
        return None
    try:
        return math.sqrt(22.5 * eps * bvps)
    except:
        return None


def margin_of_safety(price, fair_value):
    if not price or not fair_value:
        return None
    try:
        return (fair_value - price) / fair_value
    except:
        return None