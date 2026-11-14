"""DATA: what we changed in the data, how many rows, and why."""

import pandas as pd

from chrome_oak.data import cleaning
from chrome_oak.data.loader import load_data


def get_prep_steps():
    _, _, _, dropped, fixes = load_data()
    n_dropped = lambda reason: sum(1 for d in dropped if d["reason"] == reason)  # noqa: E731
    n_fixed = lambda word: sum(n for _, desc, n in fixes if word in desc)  # noqa: E731
    return [
        {"what": "Removed duplicate orders", "rows": f"{n_dropped(cleaning.DUPLICATE)} rows",
         "why": "The same order appeared twice with the same ID, which counted the sale twice."},
        {"what": "Removed orders with a negative quantity", "rows": f"{n_dropped(cleaning.NEG_QTY)} rows",
         "why": "A sale can't have negative units. Returns are already recorded in their own file."},
        {"what": "Converted dates typed as MM/DD/YYYY", "rows": f"{n_fixed('MM/DD/YYYY')} rows",
         "why": "Two date formats were mixed in one column, which breaks monthly totals."},
        {"what": "Standardized region and product names", "rows": f"{n_fixed('region') + n_fixed('product')} rows",
         "why": "'ON', 'ontario' and 'Ontario' are one region. Left alone they split every ranking."},
        {"what": "Rescaled discounts typed as percentages", "rows": f"{n_fixed('discount')} rows",
         "why": "A discount of 5.6 meant 5.6%, not 560%. Uncorrected, those orders show negative revenue."},
        {"what": "Kept blank costs as unknown", "rows": f"{n_fixed('unit_cost')} rows",
         "why": "A blank cost is missing, not free. Those orders are left out of margin, not counted as 100% profit."},
        {"what": "Treated blank payment dates as unpaid", "rows": f"{n_fixed('payment_date')} rows",
         "why": "They all belong to customers on Net 30 or Net 60 terms, so they are open invoices."},
        {"what": "Joined orders, customers and returns", "rows": "3 files → 1",
         "why": "So each order shows its customer's terms and credit limit, and any refund paid on it."},
    ]


def get_removed_rows():
    """Every row dropped in cleaning, with the line it came from in the raw file."""
    _, _, _, dropped, _ = load_data()
    cols = ["reason", "file", "csv_line", "id", "detail"]
    return pd.DataFrame(dropped, columns=cols).rename(columns={"csv_line": "line_in_raw_file"})
