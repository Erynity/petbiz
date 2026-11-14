"""Data cleaning for the PetBiz CSVs.

Run with:  .venv/bin/python cleaning.py

Reads data/*.csv, writes cleaned copies to data/clean/ and a row-by-row record
of everything dropped (grouped by reason) to CLEANING_LOG.md.
Raw files are never modified.
"""

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent
RAW = ROOT / "data"
CLEAN = RAW / "clean"
LOG_PATH = ROOT / "CLEANING_LOG.md"

REGION_MAP = {
    "ontario": "Ontario", "on": "Ontario",
    "quebec": "Quebec", "québec": "Quebec", "qc": "Quebec",
    "bc": "BC", "b.c.": "BC", "british columbia": "BC",
    "prairies": "Prairies",
    "atlantic": "Atlantic", "atl": "Atlantic",
}

# key = lowercase with everything except letters/digits removed
PRODUCT_MAP = {
    "24inmonitor": 'Monitor 24"', "monitor24": 'Monitor 24"',
    "27inmonitor": 'Monitor 27"', "monitor27": 'Monitor 27"',
    "ergoliftstandingdesk": "ErgoLift Standing Desk", "ergoliftdesk": "ErgoLift Standing Desk",
    "mechkeyboard": "Mechanical Keyboard", "mechanicalkeyboard": "Mechanical Keyboard",
    "usbcdock": "USB-C Dock",
    "desklamp": "Desk Lamp", "laptopstand": "Laptop Stand", "officechair": "Office Chair",
    "webcamhd": "Webcam HD", "wirelessmouse": "Wireless Mouse",
}

# Reasons rows get dropped (each becomes a section in the log).
DUPLICATE = "Exact duplicate row"
NEG_QTY = "Negative or zero quantity"
ORPHAN_RETURN = "Return belongs to a dropped order"


def _key(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def _parse_dates(s: pd.Series) -> pd.Series:
    """Mixed ISO (YYYY-MM-DD) and US (MM/DD/YYYY) strings -> datetime."""
    s = s.astype("string")
    iso = pd.to_datetime(s.where(s.str.match(r"^\d{4}-")), format="%Y-%m-%d", errors="coerce")
    us = pd.to_datetime(s.where(s.str.match(r"^\d{1,2}/")), format="%m/%d/%Y", errors="coerce")
    return iso.fillna(us)


def clean_all():
    """Return (customers, orders, returns, dropped, fixes).

    dropped: list of dicts {reason, file, csv_line, id, detail}
    fixes:   list of (file, description, count) for values changed but rows kept
    """
    dropped, fixes = [], []

    def drop(mask, df, file, id_col, reason, detail_cols):
        for idx, row in df[mask].iterrows():
            detail = ", ".join(f"{c}={row[c]}" for c in detail_cols)
            dropped.append(
                {"reason": reason, "file": file, "csv_line": idx + 2, "id": row[id_col], "detail": detail}
            )
        return df[~mask]

    # ---- customers: already clean -------------------------------------
    customers = pd.read_csv(RAW / "customers.csv", parse_dates=["signup_date"])
    customers["account_rep"] = customers["account_rep"].fillna("Self-serve")
    fixes.append(("customers.csv", 'blank account_rep -> "Self-serve" (all Consumer accounts)', int((customers["account_rep"] == "Self-serve").sum())))

    # ---- orders -------------------------------------------------------
    orders = pd.read_csv(RAW / "orders.csv", dtype={"order_date": "string", "payment_date": "string"})
    # index = original row, so csv_line = index + 2 (header is line 1)
    orders = drop(
        orders.duplicated(keep="first"), orders, "orders.csv", "order_id", DUPLICATE,
        ["order_date", "customer_id", "product", "quantity"],
    )

    raw_dates = orders["order_date"].copy()
    orders["order_date"] = _parse_dates(orders["order_date"])
    orders["payment_date"] = _parse_dates(orders["payment_date"])
    fixes.append(("orders.csv", "order_date in MM/DD/YYYY converted to a real date", int((~raw_dates.str.match(r"^\d{4}-")).sum())))

    before = orders["region"].copy()
    orders["region"] = orders["region"].map(lambda r: REGION_MAP[str(r).strip().lower()])
    fixes.append(("orders.csv", "region spelling normalized (e.g. ON, QC, B.C., ATL)", int((before != orders["region"]).sum())))

    before = orders["product"].copy()
    orders["product"] = orders["product"].map(lambda p: PRODUCT_MAP[_key(p)])
    fixes.append(("orders.csv", "product name normalized (22 spellings -> 10 products)", int((before != orders["product"]).sum())))

    pct = orders["discount"] >= 1
    orders.loc[pct, "discount"] = orders.loc[pct, "discount"] / 100
    fixes.append(("orders.csv", "discount stored as a percent (e.g. 5.6) divided by 100", int(pct.sum())))

    orders = drop(
        orders["quantity"] <= 0, orders, "orders.csv", "order_id", NEG_QTY,
        ["order_date", "customer_id", "product", "quantity", "unit_price"],
    )

    # kept but worth knowing about
    fixes.append(("orders.csv", "blank unit_cost kept (margin unknown for these rows)", int(orders["unit_cost"].isna().sum())))
    fixes.append(("orders.csv", "blank payment_date kept (= unpaid)", int(orders["payment_date"].isna().sum())))

    orders["sales_rep"] = orders["sales_rep"].fillna("Self-serve")

    # derived columns used by every analysis
    orders["gross"] = orders["quantity"] * orders["unit_price"]
    orders["net"] = orders["gross"] * (1 - orders["discount"])
    orders["cost"] = orders["quantity"] * orders["unit_cost"]
    orders["margin"] = orders["net"] - orders["cost"]

    # ---- returns ------------------------------------------------------
    returns = pd.read_csv(RAW / "returns.csv", parse_dates=["return_date"])
    returns = drop(
        ~returns["order_id"].isin(orders["order_id"]), returns, "returns.csv", "return_id", ORPHAN_RETURN,
        ["order_id", "return_date", "quantity_returned", "refund_amount"],
    )

    # ---- save ---------------------------------------------------------
    CLEAN.mkdir(exist_ok=True)
    customers.to_csv(CLEAN / "customers.csv", index=False)
    orders.to_csv(CLEAN / "orders.csv", index=False)
    returns.to_csv(CLEAN / "returns.csv", index=False)

    return customers, orders, returns, dropped, fixes


def write_log(dropped, fixes, kept):
    reasons = [DUPLICATE, NEG_QTY, ORPHAN_RETURN]
    why = {
        DUPLICATE: "Every column identical to an earlier row, including `order_id`. The first copy is kept.",
        NEG_QTY: "A sale can't have negative units. These may be returns keyed in as sales; the real returns live in returns.csv, so counting them again would double count.",
        ORPHAN_RETURN: "The order this return points to was dropped above, so the return has nothing to attach to.",
    }
    out = ["# Cleaning log", "", "Generated by `cleaning.py`. Raw files in `data/` are untouched; cleaned copies are in `data/clean/`.", ""]
    out += ["## Summary", "", "| File | Rows in | Dropped | Rows out |", "|---|---|---|---|"]
    for f, (n_in, n_out) in kept.items():
        out.append(f"| {f} | {n_in:,} | {n_in - n_out:,} | {n_out:,} |")
    out += ["", "## Dropped rows, by reason", ""]
    for reason in reasons:
        rows = [d for d in dropped if d["reason"] == reason]
        out += [f"### {reason} ({len(rows)})", "", why[reason], ""]
        if not rows:
            out += ["_None._", ""]
            continue
        out += ["| File | CSV line | ID | Details |", "|---|---|---|---|"]
        out += [f"| {d['file']} | {d['csv_line']} | {d['id']} | {d['detail']} |" for d in rows]
        out.append("")
    out += ["## Fixed but kept (not dropped)", "", "| File | Change | Rows affected |", "|---|---|---|"]
    out += [f"| {f} | {desc} | {n:,} |" for f, desc, n in fixes]
    out.append("")
    LOG_PATH.write_text("\n".join(out))


if __name__ == "__main__":
    n_in = {f: len(pd.read_csv(RAW / f"{f}.csv")) for f in ["customers", "orders", "returns"]}
    c, o, r, dropped, fixes = clean_all()
    kept = {
        "customers.csv": (n_in["customers"], len(c)),
        "orders.csv": (n_in["orders"], len(o)),
        "returns.csv": (n_in["returns"], len(r)),
    }
    write_log(dropped, fixes, kept)
    print(f"dropped {len(dropped)} rows -> {LOG_PATH.name}")
