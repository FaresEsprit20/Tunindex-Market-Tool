import time

CACHE = {}

def get(key):
    if key in CACHE:
        value, expiry = CACHE[key]
        if expiry > time.time():
            return value
    return None

def set(key, value, ttl=3600):
    CACHE[key] = (value, time.time() + ttl)