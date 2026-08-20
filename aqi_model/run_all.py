

import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

AQI_MODEL_DIR = Path(__file__).resolve().parent
BACKEND_DIR = AQI_MODEL_DIR.parent / "urbanair_backend"
PYTHON = sys.executable  # use the same interpreter this script was launched with

# (script, loop_minutes) -- intervals match each collector's own recommended usage
COLLECTORS = [
    ("air_pollution_collector.py", 30),
    ("traffic_collector.py", 30),
    ("weather_collector.py", 60),
    ("waqi_aqi_collector.py", 30),
]

# Files the backend reads (from urbanair_backend/README + main.py / source_attribution.py)
FILES_TO_SYNC = [
    "traffic_log.csv",
    "weather_current_log.csv",
    "live_pollutants_log.csv",
    "live_ground_aqi_log.csv",
]

SYNC_INTERVAL_SECONDS = 300  


def log(msg: str) -> None:
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)


def start_collectors() -> list[subprocess.Popen]:
    if not BACKEND_DIR.exists():
        log(f"ERROR: {BACKEND_DIR} not found. Run this from inside aqi_model/.")
        sys.exit(1)

    procs = []
    for script, minutes in COLLECTORS:
        script_path = AQI_MODEL_DIR / script
        if not script_path.exists():
            log(f"WARNING: {script} not found in {AQI_MODEL_DIR}, skipping.")
            continue
        p = subprocess.Popen(
            [PYTHON, str(script_path), "--loop", str(minutes)],
            cwd=AQI_MODEL_DIR,
        )
        log(f"started {script} (--loop {minutes}), pid={p.pid}")
        procs.append(p)
    return procs


def sync_once() -> None:
    synced = []
    for fname in FILES_TO_SYNC:
        src = AQI_MODEL_DIR / fname
        if src.exists():
            shutil.copy2(src, BACKEND_DIR / fname)
            synced.append(fname)
    if synced:
        log(f"synced -> urbanair_backend/: {', '.join(synced)}")
    else:
        log("WARNING: no source CSVs found yet, skipping this sync round")


def main() -> None:
    procs = start_collectors()
    log(f"sync loop running every {SYNC_INTERVAL_SECONDS // 60} min. Ctrl+C to stop everything.")
    try:
        while True:
            sync_once()
            time.sleep(SYNC_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        log("stopping -- terminating all collectors...")
    finally:
        for p in procs:
            p.terminate()
        for p in procs:
            try:
                p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                p.kill()
        log("all collectors stopped.")


if __name__ == "__main__":
    main()
