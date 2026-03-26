from concurrent.futures import ThreadPoolExecutor, as_completed

def run_parallel(func, items, max_workers=20):
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(func, item): item for item in items}
        for f in as_completed(futures):
            try:
                results.append(f.result())
            except:
                results.append(None)
    return results