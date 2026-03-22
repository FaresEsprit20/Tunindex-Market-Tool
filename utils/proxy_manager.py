import requests
import random

PROXY_LIST = []

def load_proxies():
    global PROXY_LIST
    try:
        res = requests.get("https://www.proxy-list.download/api/v1/get?type=http")
        PROXY_LIST = res.text.splitlines()
    except:
        PROXY_LIST = []

def get_random_proxy():
    if not PROXY_LIST:
        load_proxies()
    return random.choice(PROXY_LIST) if PROXY_LIST else None