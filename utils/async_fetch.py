# utils/async_fetch.py

from concurrent.futures import ThreadPoolExecutor, as_completed

def run_parallel(func, items, max_workers=20):
    """
    Run a function over a list of items in parallel threads.
    Returns a list of results in the same order as items.
    """
    results = [None] * len(items)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(func, item): i for i, item in enumerate(items)}
        for f in as_completed(futures):
            idx = futures[f]
            try:
                results[idx] = f.result()
            except:
                results[idx] = None
    return results