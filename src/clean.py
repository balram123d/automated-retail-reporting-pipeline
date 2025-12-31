# src/clean.py
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class CleanConfig:
    drop_missing_customerid: bool = False  # keep customers even if missing by default (realistic)
    drop_missing_description: bool = False
    processed_filename: str = "clean.csv"


def clean_data(df: pd.DataFrame, cfg: Optional[CleanConfig] = None) -> pd.DataFrame:
    """
    Cleans Online Retail-style transactional data.
    Assumes columns exist: invoiceno, stockcode, description, quantity, invoicedate, unitprice, customerid, country
    """
    if cfg is None:
        cfg = CleanConfig()

    out = df.copy()

    # Strip strings
    for col in ["invoiceno", "stockcode", "description", "country"]:
        out[col] = out[col].astype(str).str.strip()

    # Coerce numeric
    out["quantity"] = pd.to_numeric(out["quantity"], errors="coerce")
    out["unitprice"] = pd.to_numeric(out["unitprice"], errors="coerce")
    out["customerid"] = pd.to_numeric(out["customerid"], errors="coerce")  # may become NaN

    # Parse datetime
    out["invoicedate"] = pd.to_datetime(out["invoicedate"], errors="coerce")

    # Drop rows that are unusable
    out = out.dropna(subset=["invoicedate", "quantity", "unitprice"])

    # Remove nonsense prices/quantities
    out = out[(out["unitprice"] != 0) & (out["quantity"] != 0)]

    if cfg.drop_missing_customerid:
        out = out.dropna(subset=["customerid"])
    if cfg.drop_missing_description:
        out = out.dropna(subset=["description"])

    # Remove duplicates
    out = out.drop_duplicates()

    # Derive revenue (can be negative for returns)
    out["revenue"] = out["quantity"] * out["unitprice"]

    # Helpful flags
    out["is_return"] = out["quantity"] < 0
    out["invoice_date"] = out["invoicedate"].dt.date
    out["invoice_month"] = out["invoicedate"].dt.to_period("M").astype(str)
    out["invoice_week"] = out["invoicedate"].dt.to_period("W").astype(str)

    return out


def save_processed(df_clean: pd.DataFrame, processed_dir: str, cfg: Optional[CleanConfig] = None) -> str:
    if cfg is None:
        cfg = CleanConfig()

    os.makedirs(processed_dir, exist_ok=True)
    out_path = os.path.join(processed_dir, cfg.processed_filename)
    df_clean.to_csv(out_path, index=False)
    return out_path
