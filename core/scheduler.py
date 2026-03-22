# core/scheduler.py

import time
from core.orchestrator import run_pipeline


def start(interval_minutes=30):
    print(f"⏱️ Scheduler started (every {interval_minutes} min)")

    while True:
        run_pipeline()
        time.sleep(interval_minutes * 60)