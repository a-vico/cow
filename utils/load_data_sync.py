import argparse
import sys
from datetime import datetime

import pandas as pd
import requests

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


def post_row(session, url, data):
    """
    Sends a single POST request synchronously.
    """
    try:
        if session is None:
            print(f"DRY-RUN POST {url} -> {data}")
            return 200

        response = session.post(url, json=data)
        if response.status_code >= 400:
            text = response.text
            print(f"Failed: {response.status_code} - {text} - Data: {data}")
        return response.status_code
    except requests.RequestException as e:
        print(f"Request Error: {e}. Data: {data}")
        return 500


def load_cows(session):
    """
    Load Cows (Dimension)
    """
    print(f"--- Loading {len(cows_df)} Cows ---")

    records = cows_df.to_dict(orient="records")

    for row in records:
        payload = {
            "name": str(row["name"]),
            "birthdate": str(row["birthdate"]),
        }
        url = f"{API_URL}/cows/{row['id']}"
        post_row(session, url, payload)

    print("--- Cows Loading Complete ---")


def load_sensors(session):
    """
    Load Sensors (Dimension)
    """
    print(f"--- Loading {len(sensors_df)} Sensors ---")

    records = sensors_df.to_dict(orient="records")

    for row in records:
        payload = {"unit": str(row["unit"])}
        url = f"{API_URL}/sensors/{row['id']}"
        post_row(session, url, payload)

    print("--- Sensors Loading Complete ---")


def load_measurements(session):
    """
    Load Measurements (Fact)
    """
    total = len(measurements_df)
    print(f"--- Loading {total} Measurements ---")

    count = 0
    for row in measurements_df.to_dict(orient="records"):
        count += 1
        payload = {
            "sensor_id": str(row["sensor_id"]),
            "cow_id": str(row["cow_id"]),
            "timestamp": str(row["timestamp"]),
            "value": None if pd.isna(row["value"]) else row["value"],
        }
        # POST to the measurements collection endpoint (contains cow_id in payload)
        url = f"{API_URL}/measurements"
        post_row(session, url, payload)

        if count % 100 == 0:
            print(f"Uploaded {count} / {total} measurements")

    print("--- Measurements Loading Complete ---")


def main(data_dir: str):
    global cows_df, sensors_df, measurements_df
    cows_df, sensors_df, measurements_df = load_data_frames(data_dir)

    use_dry_run = globals().get("DRY_RUN", False)

    if use_dry_run:
        session = None
        load_cows(session)
        load_sensors(session)
        load_measurements(session)
    else:
        with requests.Session() as session:
            load_cows(session)
            load_sensors(session)
            load_measurements(session)


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
    globals()["DRY_RUN"] = bool(getattr(args, "dry_run", False))
    start = datetime.now()
    main(args.data_dir)
    print(f"Total execution time: {datetime.now() - start}")
