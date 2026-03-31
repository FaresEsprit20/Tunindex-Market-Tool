# fair_value.py
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

def close_to_52weekslow_percentage(current_price, week_52_low, week_52_high=None):
    """
    Calculate the current price's position within the 52-week range.
    Returns a percentage where:
    - 0% means price is at the 52-week low
    - 100% means price is at the 52-week high
    - Values between 0-100% show position between low and high
    
    Example: If low=37.03, high=61.79, current=60.49
    Result = ((60.49 - 37.03) / (61.79 - 37.03)) * 100 = 95.7% (close to high)
    """
    if not current_price or not week_52_low:
        return None
    
    try:
        if week_52_high and week_52_high > week_52_low:
            # Calculate position between low and high (0-100% scale)
            position_pct = ((current_price - week_52_low) / (week_52_high - week_52_low)) * 100
            return round(position_pct, 2)
        else:
            # Fallback: calculate percentage above low
            percentage_above_low = ((current_price - week_52_low) / week_52_low) * 100
            return round(percentage_above_low, 2)
    except:
        return None