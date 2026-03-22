def calculate_bvps(total_equity, shares_outstanding):
    if not total_equity or not shares_outstanding:
        return None
    try:
        return total_equity / shares_outstanding
    except:
        return None