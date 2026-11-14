"""Data loading and analysis helpers for the pet insights application."""

from pathlib import Path
from typing import Dict, Union

import pandas as pd


def load_dataset(path: Union[str, Path]) -> pd.DataFrame:
    """Load a CSV dataset and reject empty files."""
    dataset = pd.read_csv(path)
    if dataset.empty:
        raise ValueError("the dataset is empty")
    return dataset


def summarize_dataset(dataset: pd.DataFrame) -> Dict[str, int]:
    """Return the basic dimensions needed by the app dashboard."""
    return {"rows": len(dataset), "columns": len(dataset.columns)}


# ---- Paste everything below at the BOTTOM of analysis.py ----
# Connector for app.py: these functions hand results to the dashboard.
# app.py uses each one as soon as it exists; missing ones stay placeholders.


def get_focus():
    return "Atlantic's growth is bought with discounts: one rep gives 2-3x more than everyone else."


def get_prep_steps():
    """From cleaning_log.md (cleaning.py). Raw files untouched; cleaned copies in data/clean/."""
    return [
        {"what": "Removed exact duplicate orders", "rows": "25 rows",
         "why": "Same order_id copied twice: keeping both would count the sale twice in revenue."},
        {"what": "Removed orders with negative or zero quantity", "rows": "8 rows",
         "why": "Likely returns keyed in as sales. Real returns are in returns.csv, so keeping them would double count."},
        {"what": "Normalized regions and product names", "rows": "405 rows",
         "why": "ON / QC / B.C. / ATL and 22 product spellings would split the same group in our charts."},
        {"what": "Fixed dates and discounts", "rows": "304 rows",
         "why": "MM/DD/YYYY dates converted, and discounts stored as 5.6 turned into 0.056 so averages are right."},
        {"what": "Kept blank payment dates and costs", "rows": "184 rows",
         "why": "A blank payment date means unpaid (that's the data we need), and blank cost means margin unknown, not zero."},
    ]
