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
