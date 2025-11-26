import asyncio
import sys
from datetime import datetime

import aiohttp
import pandas as pd

# CONFIGURATION
API_URL = "http://localhost:8000"
MAX_CONCURRENT_REQUESTS = 50


try:
    cows_df = pd.read_parquet("data/input/cows.parquet")
    sensors_df = pd.read_parquet("data/input/sensors.parquet")
    measurements_df = pd.read_parquet("data/input/measurements.parquet")
except Exception as e:
    print(f"Error loading parquet files: {e}")
    sys.exit(1)


async def post_row(session, url, data, semaphore):
    """
    Sends a single POST request with concurrency control.
    """
    async with semaphore:
        try:
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
        url = f"{API_URL}/cows/{row['cow_id']}/measurements"
        tasks.append(post_row(session, url, payload, semaphore))

    await asyncio.gather(*tasks)
    print("--- Measurements Loading Complete ---")


async def main():
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    async with aiohttp.ClientSession() as session:
        await load_cows(session, semaphore)
        await load_sensors(session, semaphore)
        await load_measurements(session, semaphore)


if __name__ == "__main__":
    start = datetime.now()
    asyncio.run(main())
    print(f"Total execution time: {datetime.now() - start}")
