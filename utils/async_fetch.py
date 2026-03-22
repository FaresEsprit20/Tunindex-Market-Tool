from concurrent.futures import ThreadPoolExecutor

def run_parallel(func, items, max_workers=5):
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(func, item) for item in items]
        for f in futures:
            try:
                results.append(f.result())
            except:
                results.append(None)
    return results