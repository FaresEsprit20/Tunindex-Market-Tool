# services/fetcher.py

import requests
from utils.user_agent import random_user_agent
from utils.proxy_manager import get_random_proxy
from utils.retry_manager import retry
from utils.rate_limiter import wait


@retry(max_retries=3, delay=2)
def fetch(url, use_proxy=False, timeout=10):
    wait()

    headers = {
        "User-Agent": random_user_agent()
    }

    proxies = None
    if use_proxy:
        proxy = get_random_proxy()
        if proxy:
            proxies = {"http": proxy, "https": proxy}

    response = requests.get(url, headers=headers, proxies=proxies, timeout=timeout)

    if response.status_code != 200:
        raise Exception("Request failed")

    return response.text