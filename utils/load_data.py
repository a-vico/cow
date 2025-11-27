import argparse
import asyncio
import json
import sys
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

import aiohttp
import numpy as np
import pandas as pd


def timed_print(*args, **kwargs):
    """Print with an ISO8601 UTC timestamp prefix."""
    ts = datetime.utcnow().isoformat() + "Z"
    print(ts, *args, **kwargs)


# CONFIGURATION
# include API prefix so loader targets routes registered under /api/v1
API_URL = "http://localhost:8000/api/v1"
MAX_CONCURRENT_REQUESTS = 50


def load_data_frames(data_dir: str):
    """Load parquet files from provided data directory."""
    try:
        cows_df = pd.read_parquet(f"{data_dir}/cows.parquet")
        sensors_df = pd.read_parquet(f"{data_dir}/sensors.parquet")
        measurements_df = pd.read_parquet(f"{data_dir}/measurements.parquet")
        return cows_df, sensors_df, measurements_df
    except Exception as e:
        timed_print(f"Error loading parquet files from {data_dir}: {e}")
        sys.exit(1)


async def post_row(session, url, data, semaphore):
    """
    Sends a single POST request with concurrency control.
    """
    async with semaphore:
        # ensure payload only contains JSON-native types
        def _normalize_value(v: Any) -> Any:
            if v is None:
                return None
            if isinstance(v, (str, bool)):
                return v
            if isinstance(v, (int,)):
                return v
            if isinstance(v, float):
                # convert numpy floats to python float implicitly
                return float(v)
            if isinstance(v, Decimal):
                return float(v)
            if isinstance(v, (np.floating,)):
                return float(v)
            if isinstance(v, (np.integer,)):
                return int(v)
            if isinstance(v, (np.ndarray,)):
                return v.tolist()
            if isinstance(v, (UUID,)):
                return str(v)
            # pandas timestamp / numpy datetime -> ISO string
            if isinstance(v, (pd.Timestamp,)):
                if pd.isna(v):
                    return None
                return v.isoformat()
            if isinstance(v, (np.datetime64,)):
                try:
                    return pd.to_datetime(v).isoformat()
                except Exception:
                    return str(v)
            # fall back to attempt JSON-serializable conversion
            try:
                json.dumps(v)
                return v
            except Exception:
                return str(v)

        normalized = {k: _normalize_value(v) for k, v in (data or {}).items()}

        try:
            if session is None:
                timed_print(f"DRY-RUN POST {url} -> {normalized}")
                return 200

            # small retry/backoff logic for transient network errors
            attempts = 3
            for attempt in range(1, attempts + 1):
                try:
                    async with session.post(url, json=normalized) as response:
                        if response.status >= 400:
                            text = await response.text()
                            timed_print(
                                f"Failed: {response.status} - {text} - Data: {normalized}"
                            )
                        return response.status
                except Exception as inner_e:
                    if attempt == attempts:
                        timed_print(f"Request Error: {inner_e}. Data: {normalized}")
                        return 500
                    await asyncio.sleep(0.5 * attempt)
                    continue
        except Exception as e:
            timed_print(f"Request Error: {e}. Data: {normalized}")
            return 500


async def load_cows(session, semaphore):
    """
    Load Cows (Dimension)
    """
    timed_print(f"--- Loading {len(cows_df)} Cows ---")
    tasks = []

    records = cows_df.to_dict(orient="records")

    for row in records:
        payload = {
            "name": str(row["name"]),
            "birthdate": str(row["birthdate"]),
        }
        url = f"{API_URL}/cows/{row['id']}"
        tasks.append(post_row(session, url, payload, semaphore))

    await asyncio.gather(*tasks)
    timed_print("--- Cows Loading Complete ---")


async def load_sensors(session, semaphore):
    """
    Load Sensors (Dimension)
    """
    timed_print(f"--- Loading {len(sensors_df)} Sensors ---")
    tasks = []

    records = sensors_df.to_dict(orient="records")

    for row in records:
        payload = {
            "unit": str(row["unit"]),
        }
        url = f"{API_URL}/sensors/{row['id']}"
        tasks.append(post_row(session, url, payload, semaphore))

    await asyncio.gather(*tasks)
    timed_print("--- Sensors Loading Complete ---")


async def load_measurements(session, semaphore):
    """
    Load Measurements (Fact)
    """
    total = len(measurements_df)
    timed_print(f"--- Loading {total} Measurements ---")

    # build tasks but execute with as_completed to report progress
    tasks = []
    for row in measurements_df.to_dict(orient="records"):
        payload = {
            "sensor_id": str(row["sensor_id"]),
            "cow_id": str(row["cow_id"]),
            "timestamp": row["timestamp"],
            "value": None if pd.isna(row["value"]) else row["value"],
        }
        url = f"{API_URL}/measurements"
        tasks.append(post_row(session, url, payload, semaphore))

    # run and report progress
    completed = 0
    successes = 0
    failures = 0
    report_every = max(1, total // 100)

    for fut in asyncio.as_completed(tasks):
        status = await fut
        completed += 1
        if status and 200 <= status < 300:
            successes += 1
        else:
            failures += 1

        if completed % report_every == 0 or completed == total:
            timed_print(
                f"Measurements progress: {completed}/{total} (success={successes} fail={failures})"
            )
    timed_print(
        f"--- Measurements Loading Complete: {completed}/{total} (success={successes} fail={failures}) ---"
    )


async def main(data_dir: str):
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    # lazy-load dataframes using provided data_dir so --help doesn't fail
    global cows_df, sensors_df, measurements_df
    cows_df, sensors_df, measurements_df = load_data_frames(data_dir)

    # determine if we're in dry-run mode by checking a global flag set by parse_args
    use_dry_run = globals().get("DRY_RUN", False)

    if use_dry_run:
        session = None
        await load_cows(session, semaphore)
        await load_sensors(session, semaphore)
        await load_measurements(session, semaphore)
    else:
        timeout = aiohttp.ClientTimeout(total=60)
        connector = aiohttp.TCPConnector(limit_per_host=MAX_CONCURRENT_REQUESTS)
        async with aiohttp.ClientSession(
            timeout=timeout, connector=connector
        ) as session:
            await load_cows(session, semaphore)
            await load_sensors(session, semaphore)
            await load_measurements(session, semaphore)


def parse_args():
    p = argparse.ArgumentParser(description="Load parquet data into the Cow API")
    p.add_argument(
        "--data-dir",
        default="data/input",
        help="Directory containing cows.parquet, sensors.parquet, measurements.parquet",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print payloads without sending HTTP requests",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    # expose dry-run flag as a global so async code can check without changing signatures
    globals()["DRY_RUN"] = bool(getattr(args, "dry_run", False))
    start = datetime.now()
    asyncio.run(main(args.data_dir))
    timed_print(f"Total execution time: {datetime.now() - start}")
