"""Load the cleaned data and join the three files into one orders table."""

from functools import lru_cache

import pandas as pd

from chrome_oak.config import ASOF, TERMS_DAYS
from chrome_oak.data import cleaning


@lru_cache(maxsize=1)
def load_data():
    """Return (customers, orders, returns, dropped, fixes). Cached: treat the tables as read-only."""
    customers, orders, returns, dropped, fixes = cleaning.clean_all()

    # each order gets its customer's details ...
    orders = orders.merge(
        customers[["customer_id", "segment", "payment_terms", "credit_limit", "account_rep"]], on="customer_id"
    )
    # ... and the refund paid back on it, if any
    refunds = returns.groupby("order_id")["refund_amount"].sum().rename("refund")
    orders = orders.merge(refunds, on="order_id", how="left")
    orders["refund"] = orders["refund"].fillna(0)

    # an order is one invoice, due `terms` days after the order date
    orders["terms_days"] = orders["payment_terms"].map(TERMS_DAYS)
    orders["due_date"] = orders["order_date"] + pd.to_timedelta(orders["terms_days"], unit="D")
    orders["days_overdue"] = (ASOF - orders["due_date"]).dt.days
    return customers, orders, returns, dropped, fixes


def get_data():
    """The cleaned orders table, one row per order (Data list page)."""
    _, orders, *_ = load_data()
    out = orders.rename(columns={"sales_rep": "rep", "net": "amount"})
    out["order_date"] = out["order_date"].dt.date
    out["payment_date"] = out["payment_date"].dt.date
    cols = ["order_id", "order_date", "customer_id", "segment", "region", "rep", "sales_channel", "product", "category",
            "quantity", "unit_price", "discount", "amount", "margin", "refund", "payment_terms", "payment_date"]
    out = out[cols].copy()
    out["amount"] = out["amount"].round(2)
    out["margin"] = out["margin"].round(2)
    return out
