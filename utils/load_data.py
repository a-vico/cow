import argparse
import asyncio
import sys
from datetime import datetime

import aiohttp
import pandas as pd

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
        print(f"Error loading parquet files from {data_dir}: {e}")
        sys.exit(1)


async def post_row(session, url, data, semaphore):
    """
    Sends a single POST request with concurrency control.
    """
    async with semaphore:
        try:
            if session is None:
                print(f"DRY-RUN POST {url} -> {data}")
                return 200

            async with session.post(url, json=data) as response:
                if response.status >= 400:
                    text = await response.text()
                    print(f"Failed: {response.status} - {text} - Data: {data}")
                return response.status
        except Exception as e:
            print(f"Request Error: {e}")
            return 500


async def load_cows(session, semaphore):
    """
    Load Cows (Dimension)
    """
    print(f"--- Loading {len(cows_df)} Cows ---")
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
    print("--- Cows Loading Complete ---")


async def load_sensors(session, semaphore):
    """
    Load Sensors (Dimension)
    """
    print(f"--- Loading {len(sensors_df)} Sensors ---")
    tasks = []

    records = sensors_df.to_dict(orient="records")

    for row in records:
        payload = {
            "unit": str(row["unit"]),
        }
        url = f"{API_URL}/sensors/{row['id']}"
        tasks.append(post_row(session, url, payload, semaphore))

    await asyncio.gather(*tasks)
    print("--- Sensors Loading Complete ---")


async def load_measurements(session, semaphore):
    """
    Load Measurements (Fact)
    """
    print(f"--- Loading {len(measurements_df)} Measurements ---")
    tasks = []

    for row in measurements_df.to_dict(orient="records"):
        payload = {
            "sensor_id": str(row["sensor_id"]),
            "cow_id": str(row["cow_id"]),
            "timestamp": row["timestamp"],
            "value": row["value"],
        }
        # POST to the measurements collection endpoint (contains cow_id in payload)
        url = f"{API_URL}/measurements"
        tasks.append(post_row(session, url, payload, semaphore))

    await asyncio.gather(*tasks)
    print("--- Measurements Loading Complete ---")


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
        async with aiohttp.ClientSession() as session:
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
    print(f"Total execution time: {datetime.now() - start}")
