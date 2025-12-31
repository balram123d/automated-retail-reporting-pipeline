# src/report.py
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Optional

import pandas as pd


@dataclass(frozen=True)
class ReportConfig:
    report_filename: str = "insights_report.txt"


def _fmt_money(x: float) -> str:
    try:
        return f"${x:,.2f}"
    except Exception:
        return str(x)


def generate_report(metrics: Dict[str, float], tables: Dict[str, pd.DataFrame], output_dir: str, cfg: Optional[ReportConfig] = None) -> str:
    if cfg is None:
        cfg = ReportConfig()

    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, cfg.report_filename)

    daily = tables.get("daily_trend")
    top_products = tables.get("top_products")
    anomalies = tables.get("anomalies")

    best_day_line = ""
    if daily is not None and not daily.empty:
        best = daily.sort_values("daily_revenue", ascending=False).iloc[0]
        best_day_line = f"Best day: {best['date'].date().isoformat()} with {_fmt_money(float(best['daily_revenue']))}"

    top_product_line = ""
    if top_products is not None and not top_products.empty:
        tp = top_products.iloc[0]
        top_product_line = f"Top product: {tp['stockcode']} - {str(tp['description'])[:60]}... ({_fmt_money(float(tp['total_revenue']))})"

    anomaly_line = ""
    if anomalies is not None and not anomalies.empty:
        anomaly_dates = ", ".join([str(pd.to_datetime(d).date()) for d in anomalies["date"].tolist()[:8]])
        anomaly_line = f"Revenue anomaly days detected: {len(anomalies)} (examples: {anomaly_dates})"
    else:
        anomaly_line = "Revenue anomaly days detected: 0"

    text = f"""AUTOMATED BUSINESS INSIGHTS REPORT
================================

Date range: {metrics.get('date_start', '')} to {metrics.get('date_end', '')}

Key metrics
-----------
Total revenue: {_fmt_money(float(metrics.get('total_revenue', 0.0)))}
Total orders: {int(float(metrics.get('total_orders', 0.0)))}
Total customers: {int(float(metrics.get('total_customers', 0.0)))}
Average order value: {_fmt_money(float(metrics.get('avg_order_value', 0.0)))}

Returns
-------
Return-related revenue (often negative): {_fmt_money(float(metrics.get('returns_revenue', 0.0)))}
Orders with returns: {int(float(metrics.get('returns_orders_count', 0.0)))}

Highlights
----------
{best_day_line}
{top_product_line}
{anomaly_line}

Notes
-----
- This report is generated automatically from raw transactional data.
- Outputs are designed for repeatable operational reporting.
"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

    return path
