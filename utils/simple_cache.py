# utils/simple_cache.py

import time

CACHE = {}

def get(key):
    """
    Retrieve a value from cache if not expired.
    """
    if key in CACHE:
        value, expiry = CACHE[key]
        if expiry > time.time():
            return value
    return None

def set(key, value, ttl=3600):
    """
    Save a value in cache for ttl seconds (default 1 hour).
    """
    CACHE[key] = (value, time.time() + ttl)