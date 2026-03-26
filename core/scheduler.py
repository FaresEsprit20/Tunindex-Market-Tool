# core/scheduler.py

import time
from core.orchestrator import run_pipeline

def start(interval_minutes=30):
    """
    Run the orchestrator pipeline at regular intervals.
    """
    print(f"⏱️ Scheduler started (every {interval_minutes} min)")

    try:
        while True:
            run_pipeline()
            # Sleep in smaller increments to allow quicker exit if needed
            total_sleep = interval_minutes * 60
            sleep_step = 5  # 5 seconds per step
            for _ in range(0, total_sleep, sleep_step):
                time.sleep(sleep_step)
    except KeyboardInterrupt:
        print("⏹️ Scheduler stopped by user")