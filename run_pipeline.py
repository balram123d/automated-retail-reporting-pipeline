# run_pipeline.py
from __future__ import annotations

import argparse
import os
from glob import glob

import pandas as pd

from src.ingest import load_data
from src.clean import clean_data, save_processed
from src.analyze import compute_metrics, save_analysis_outputs
from src.report import generate_report


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Automated Business Insights Pipeline")
    p.add_argument("--input", required=True, help="Path to raw file OR directory containing raw files")
    p.add_argument("--processed-dir", default="data/processed", help="Where to save cleaned data")
    p.add_argument("--output-dir", default="output", help="Where to save reports/metrics")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    if os.path.isdir(args.input):
        files = glob(os.path.join(args.input, "*.csv"))
        if not files:
            raise ValueError(f"No CSV files found in directory: {args.input}")
    else:
        files = [args.input]

    dfs = []
    for path in files:
        print(f"Loading: {path}")
        df = load_data(path)
        dfs.append(df)

    df_raw = pd.concat(dfs, ignore_index=True)

    df_clean = clean_data(df_raw)
    processed_path = save_processed(df_clean, args.processed_dir)

    metrics, tables = compute_metrics(df_clean)
    output_paths = save_analysis_outputs(metrics, tables, args.output_dir)
    report_path = generate_report(metrics, tables, args.output_dir)

    print("✅ Pipeline completed.")
    print(f"Processed data: {processed_path}")
    for k, v in output_paths.items():
        print(f"{k}: {v}")
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()
