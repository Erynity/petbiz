"""Paths and constants shared by the whole app."""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"          # exports exactly as received, never edited
CLEAN_DIR = DATA_DIR / "clean"      # written by chrome_oak.data.cleaning
ACTION_LOG = DATA_DIR / "action_log.csv"  # every alert sent or dismissed (git-ignored)
CLEANING_LOG = ROOT / "docs" / "CLEANING_LOG.md"

# The data was extracted on this date. Every "days late" number counts up to it.
ASOF = pd.Timestamp("2026-10-31")
DATE_RANGE = "Jan 2025 – Sep 2026"

TERMS_DAYS = {"Prepaid": 0, "Net 30": 30, "Net 60": 60}
