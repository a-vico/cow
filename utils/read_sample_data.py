import argparse
from pathlib import Path

import pandas as pd


def read_parquet_files(directory_path: str = ".") -> dict[str, pd.DataFrame]:
    """
    Read all parquet files from the specified directory.

    Args:
        directory_path: Path to directory containing parquet files (default: current directory)

    Returns:
        Dictionary with filename (without extension) as key and DataFrame as value
    """
    directory = Path(directory_path)
    parquet_files = list(directory.rglob("*.parquet"))

    if not parquet_files:
        print(f"No parquet files found in {directory.absolute()}")
        return {}

    dataframes = {}
    for parquet_file in parquet_files:
        try:
            df = pd.read_parquet(parquet_file)
            try:
                key = parquet_file.relative_to(directory).with_suffix("").as_posix()
            except Exception:
                key = parquet_file.with_suffix("").name
            dataframes[key] = df
            print(
                f"✓ Loaded {parquet_file.relative_to(directory)}: {df.shape[0]} rows, {df.shape[1]} columns"
            )
        except Exception as e:
            print(f"✗ Error reading {parquet_file.name}: {e}")

    return dataframes


def read_single_parquet(file_path: str) -> pd.DataFrame:
    """
    Read a single parquet file.

    Args:
        file_path: Path to the parquet file

    Returns:
        DataFrame with the parquet file contents
    """
    df = pd.read_parquet(file_path)
    print(f"Loaded {Path(file_path).name}: {df.shape[0]} rows, {df.shape[1]} columns")
    print(f"Columns: {', '.join(df.columns)}")
    return df


def _cli():
    parser = argparse.ArgumentParser(
        description="Read parquet files recursively from a directory"
    )
    parser.add_argument(
        "dir",
        nargs="?",
        default=".",
        help="Directory to scan for parquet files (default: current directory)",
    )
    args = parser.parse_args()

    directory = Path(args.dir)
    print(f"Reading parquet files from: {directory.absolute()}\n")

    dfs = read_parquet_files(directory)

    # Display info about each DataFrame
    for name, df in dfs.items():
        print(f"\n--- {name} ---")
        print(df.head())
        print(f"\nData types:\n{df.dtypes}")
        print(f"\nSummary:\n{df.describe()}")


if __name__ == "__main__":
    _cli()
