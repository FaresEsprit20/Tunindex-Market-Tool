import time

LAST_CALL = 0
DELAY = 1.5

def wait():
    global LAST_CALL
    now = time.time()
    if now - LAST_CALL < DELAY:
        time.sleep(DELAY - (now - LAST_CALL))
    LAST_CALL = time.time()