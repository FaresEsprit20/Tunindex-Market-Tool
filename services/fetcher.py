# services/fetcher.py

import requests
from utils.user_agent import random_user_agent
from utils.proxy_manager import get_random_proxy
from utils.rate_limiter import wait
import time


def fetch(url, use_proxy=False, timeout=10, retries=3, backoff=2):
    """
    Robust fetch with retries, backoff, random User-Agent, optional proxy, and rate-limit wait.
    """
    for attempt in range(1, retries + 1):
        try:
            wait()  # global rate limiter

            headers = {"User-Agent": random_user_agent()}
            proxies = None
            if use_proxy:
                proxy = get_random_proxy()
                if proxy:
                    proxies = {"http": proxy, "https": proxy}

            response = requests.get(url, headers=headers, proxies=proxies, timeout=timeout)

            if response.status_code == 200 and response.text:
                return response.text
            else:
                raise Exception(f"Request failed: {url} (status {response.status_code})")

        except Exception as e:
            print(f"Retry {attempt}/{retries} failed: {e}")
            time.sleep(backoff * attempt)  # exponential backoff

    print(f"❌ All retries failed for: {url}")
    return None