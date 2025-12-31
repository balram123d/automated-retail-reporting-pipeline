# src/ingest.py
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

import pandas as pd


@dataclass(frozen=True)
class IngestConfig:
    required_columns: Tuple[str, ...] = (
        "invoiceno",
        "stockcode",
        "description",
        "quantity",
        "invoicedate",
        "unitprice",
        "customerid",
        "country",
    )


def _normalize_columns(cols: List[str]) -> List[str]:
    """
    Convert to lowercase, remove non-alphanumerics, replace spaces with underscores.
    Example: 'InvoiceNo' -> 'invoiceno', 'Unit Price' -> 'unit_price'
    """
    out = []
    for c in cols:
        c2 = c.strip().lower()
        c2 = re.sub(r"\s+", "_", c2)
        c2 = re.sub(r"[^a-z0-9_]", "", c2)
        out.append(c2)
    return out


def _read_excel(path: str, sheet_name: Optional[str] = None) -> pd.DataFrame:
    """
    Read xlsx. If sheet_name is None, reads first sheet.
    """
    return pd.read_excel(path, sheet_name=sheet_name, engine="openpyxl")


def _read_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


def load_data(path: str, sheet_name: Optional[str] = None, cfg: Optional[IngestConfig] = None) -> pd.DataFrame:
    """
    Loads raw data from .xlsx or .csv, normalizes columns, and validates required schema.
    """
    if cfg is None:
        cfg = IngestConfig()

    if not os.path.exists(path):
        raise FileNotFoundError(f"Raw data file not found: {path}")

    ext = os.path.splitext(path)[1].lower()
    if ext in [".xlsx", ".xlsm", ".xls"]:
        df = _read_excel(path, sheet_name=sheet_name)
    elif ext == ".csv":
        df = _read_csv(path)
    else:
        raise ValueError(f"Unsupported file type: {ext}. Use .xlsx or .csv")

    if df.empty:
        raise ValueError("Loaded dataframe is empty. Check file/sheet.")

    # Normalize columns
    df.columns = _normalize_columns([str(c) for c in df.columns])

    # Validate required columns exist (case-insensitive already normalized)
    missing = [c for c in cfg.required_columns if c not in df.columns]
    if missing:
        raise ValueError(
            f"Missing required columns: {missing}\n"
            f"Found columns: {list(df.columns)}\n"
            f"Tip: If your Excel has different column names, update IngestConfig.required_columns."
        )

    return df
