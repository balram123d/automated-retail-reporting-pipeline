# src/analyze.py
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class AnalyzeConfig:
    metrics_filename: str = "summary_metrics.csv"
    daily_trend_filename: str = "daily_revenue_trend.csv"
    top_products_filename: str = "top_products_by_revenue.csv"
    anomalies_filename: str = "revenue_anomalies.csv"
    top_n_products: int = 10


def compute_metrics(df: pd.DataFrame, cfg: Optional[AnalyzeConfig] = None) -> Tuple[Dict[str, float], Dict[str, pd.DataFrame]]:
    if cfg is None:
        cfg = AnalyzeConfig()

    # Core summary
    date_min = df["invoicedate"].min()
    date_max = df["invoicedate"].max()

    total_revenue = float(df["revenue"].sum())
    total_orders = float(df["invoiceno"].nunique())
    total_customers = float(df["customerid"].nunique(dropna=True))
    avg_order_value = float(total_revenue / total_orders) if total_orders else 0.0

    returns_revenue = float(df.loc[df["is_return"], "revenue"].sum())  # negative number typically
    returns_count = float(df.loc[df["is_return"], "invoiceno"].nunique())

    metrics = {
        "total_revenue": total_revenue,
        "total_orders": total_orders,
        "total_customers": total_customers,
        "avg_order_value": avg_order_value,
        "returns_revenue": returns_revenue,
        "returns_orders_count": returns_count,
        "date_start": date_min.isoformat() if pd.notna(date_min) else "",
        "date_end": date_max.isoformat() if pd.notna(date_max) else "",
    }

    # Daily trend
    daily = (
        df.groupby("invoice_date", as_index=False)["revenue"]
        .sum()
        .rename(columns={"invoice_date": "date", "revenue": "daily_revenue"})
    )
    daily["date"] = pd.to_datetime(daily["date"])
    daily = daily.sort_values("date")

    # Top products by revenue (stockcode+description)
    top_products = (
        df.groupby(["stockcode", "description"], as_index=False)["revenue"]
        .sum()
        .sort_values("revenue", ascending=False)
        .head(cfg.top_n_products)
        .rename(columns={"revenue": "total_revenue"})
    )

    # Simple anomaly detection on daily revenue: > mean + 2*std (basic, explainable)
    mu = daily["daily_revenue"].mean()
    sigma = daily["daily_revenue"].std(ddof=0) if len(daily) > 1 else 0.0
    threshold = mu + 2 * sigma
    anomalies = daily[daily["daily_revenue"] > threshold].copy()
    anomalies["threshold"] = threshold

    tables = {
        "daily_trend": daily,
        "top_products": top_products,
        "anomalies": anomalies,
    }

    return metrics, tables


def save_analysis_outputs(
    metrics: Dict[str, float],
    tables: Dict[str, pd.DataFrame],
    output_dir: str,
    cfg: Optional[AnalyzeConfig] = None,
) -> Dict[str, str]:
    if cfg is None:
        cfg = AnalyzeConfig()

    os.makedirs(output_dir, exist_ok=True)

    # Metrics -> 2-column CSV
    metrics_df = pd.DataFrame([{"metric": k, "value": v} for k, v in metrics.items()])
    metrics_path = os.path.join(output_dir, cfg.metrics_filename)
    metrics_df.to_csv(metrics_path, index=False)

    daily_path = os.path.join(output_dir, cfg.daily_trend_filename)
    tables["daily_trend"].to_csv(daily_path, index=False)

    top_path = os.path.join(output_dir, cfg.top_products_filename)
    tables["top_products"].to_csv(top_path, index=False)

    anomalies_path = os.path.join(output_dir, cfg.anomalies_filename)
    tables["anomalies"].to_csv(anomalies_path, index=False)

    return {
        "metrics": metrics_path,
        "daily_trend": daily_path,
        "top_products": top_path,
        "anomalies": anomalies_path,
    }
