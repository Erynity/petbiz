"""All the numbers behind the petbiz UI (app_live.py). Self-contained: reads data/raw/*.csv in this folder.

app_live.py calls these functions and only displays what they return:
    get_data, get_focus, get_kpis, get_charts, get_prep_steps, get_insights, detect_issues
"""

import re
from functools import lru_cache
from pathlib import Path

import pandas as pd

RAW = Path(__file__).resolve().parent / "data" / "raw"   # exports exactly as received, never edited

# The data was extracted on this date. Every "days late" number counts up to it.
ASOF = pd.Timestamp("2026-10-31")
TERMS_DAYS = {"Prepaid": 0, "Net 30": 30, "Net 60": 60}


# ===========================================================================
# 1. CLEAN the three CSVs
# ===========================================================================
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

    return customers, orders, returns, dropped, fixes


# ===========================================================================
# 2. LOAD: join customers, orders and returns into one orders table
# ===========================================================================
@lru_cache(maxsize=1)
def load_data():
    """Return (customers, orders, returns, dropped, fixes). Cached: treat the tables as read-only."""
    customers, orders, returns, dropped, fixes = clean_all()
    orders = orders.merge(
        customers[["customer_id", "segment", "payment_terms", "credit_limit", "account_rep"]], on="customer_id"
    )
    refunds = returns.groupby("order_id")["refund_amount"].sum().rename("refund")
    orders = orders.merge(refunds, on="order_id", how="left")
    orders["refund"] = orders["refund"].fillna(0)
    orders["terms_days"] = orders["payment_terms"].map(TERMS_DAYS)
    orders["due_date"] = orders["order_date"] + pd.to_timedelta(orders["terms_days"], unit="D")
    orders["days_overdue"] = (ASOF - orders["due_date"]).dt.days
    return customers, orders, returns, dropped, fixes


def get_data():
    """The cleaned orders table, one row per order (Data page and overview tiles)."""
    _, orders, *_ = load_data()
    out = orders.rename(columns={"sales_rep": "rep", "net": "amount"})
    out["order_date"] = out["order_date"].dt.date
    out["payment_date"] = out["payment_date"].dt.date
    # 92 orders have a blank cost: use that product's median so the margin tile isn't inflated
    out["unit_cost"] = out["unit_cost"].fillna(out.groupby("product")["unit_cost"].transform("median"))
    out["paid"] = out["payment_date"].notna().map({True: "Yes", False: "No"})
    cols = ["order_id", "order_date", "customer_id", "segment", "region", "rep", "sales_channel", "product", "category",
            "quantity", "unit_price", "unit_cost", "discount", "amount", "margin", "refund", "payment_terms",
            "payment_date", "paid"]
    out = out[cols].copy()
    out["amount"] = out["amount"].round(2)
    out["margin"] = out["margin"].round(2)
    return out


def get_prep_steps():
    """What the cleaning did. Raw files are untouched."""
    _, _, _, dropped, fixes = load_data()
    n = lambda reason: sum(1 for d in dropped if d["reason"] == reason)
    fx = {d: c for _, d, c in fixes}
    find = lambda s: next(c for d, c in fx.items() if s in d)
    return [
        {"what": "Removed exact duplicate orders", "rows": f"{n(DUPLICATE)} rows",
         "why": "Same order_id copied twice: keeping both would count the sale twice in revenue."},
        {"what": "Removed orders with negative or zero quantity", "rows": f"{n(NEG_QTY)} rows",
         "why": "Likely returns keyed in as sales. Real returns are in returns.csv, so keeping them would double count."},
        {"what": "Normalized regions and product names", "rows": f"{find('region') + find('product')} rows",
         "why": "ON / QC / B.C. / ATL and 22 product spellings would split the same group in our charts."},
        {"what": "Fixed dates and discounts", "rows": f"{find('order_date') + find('discount')} rows",
         "why": "MM/DD/YYYY dates converted, and discounts stored as 5.6 turned into 0.056 so averages are right."},
        {"what": "Kept blank payment dates and costs", "rows": f"{find('blank payment_date') + find('blank unit_cost')} rows",
         "why": "A blank payment date means unpaid (that's the data we need), and blank cost means margin unknown, not zero."},
    ]


# ===========================================================================
# 3. DECIDE: headline numbers
# ===========================================================================
def margin_pct(df):
    """Margin as a share of revenue, on orders where the cost is known."""
    known = df[df["cost"].notna()]
    return known["margin"].sum() / known["net"].sum()


def jan_sep(orders, year):
    return orders[(orders["order_date"].dt.year == year) & (orders["order_date"].dt.month <= 9)]


def money(x):
    return f"${x/1e6:,.2f}M" if abs(x) >= 1e6 else f"${x/1e3:,.0f}K"

def get_focus():
    _, orders, *_ = load_data()
    r25, r26 = jan_sep(orders, 2025), jan_sep(orders, 2026)
    rev_growth = r26["net"].sum() / r25["net"].sum() - 1
    k25, k26 = r25[r25["cost"].notna()], r26[r26["cost"].notna()]
    profit_growth = k26["margin"].sum() / k25["margin"].sum() - 1
    return (
        f"Revenue grew {rev_growth:.0%} but gross profit only {profit_growth:.0%}: "
        "the growth is being bought with discounts."
    )


def get_kpis():
    _, orders, *_ = load_data()
    r25, r26 = jan_sep(orders, 2025)["net"].sum(), jan_sep(orders, 2026)["net"].sum()
    atl = margin_pct(orders[orders["region"] == "Atlantic"])
    rest = margin_pct(orders[orders["region"] != "Atlantic"])
    past_due = orders[orders["payment_date"].isna() & (orders["days_overdue"] > 0)]
    refund_rate = orders["refund"].sum() / orders["net"].sum()

    # quarterly trends for the sparklines
    quarter = orders["order_date"].dt.to_period("Q")
    known = orders["cost"].notna()
    q_net = orders.groupby(quarter)["net"].sum()
    q_margin = orders[known].groupby(quarter[known])["margin"].sum() / orders[known].groupby(quarter[known])["net"].sum()
    q_past_due = past_due.groupby(past_due["order_date"].dt.to_period("Q"))["net"].sum().reindex(q_net.index, fill_value=0)
    q_refund = orders.groupby(quarter)["refund"].sum() / q_net
    return [
        {"label": "Revenue, Jan–Sep 2026", "value": money(r26), "delta": f"{r26 / r25 - 1:+.0%} vs Jan–Sep 2025",
         "trend": q_net.round(0).tolist()},
        {"label": "Gross margin", "value": f"{margin_pct(orders):.0%}", "delta": f"Atlantic {atl:.0%} · elsewhere {rest:.0%}",
         "trend": q_margin.round(3).tolist()},
        {"label": "Past-due invoices", "value": money(past_due["net"].sum()), "delta": f"{len(past_due)} invoices",
         "trend": q_past_due.round(0).tolist()},
        {"label": "Refunded", "value": f"{refund_rate:.1%} of revenue", "delta": f"{money(orders['refund'].sum())} given back",
         "trend": q_refund.round(3).tolist()},
    ]

def get_charts(region=None):
    """Two bar charts in the shape ui/charts.py draws (format / sort / highlight / x_title).

    `region` (optional, from the Insights page's region box) limits the rep chart to that region.
    """
    _, orders, *_ = load_data()

    # Chart 1: average discount by sales rep (online orders have no rep)
    reps = orders[orders["sales_rep"] != "Self-serve"]
    all_disc = reps.groupby("sales_rep")["discount"].mean().sort_values(ascending=False)
    top_rep = all_disc.index[0]
    top_region = reps.loc[reps["sales_rep"] == top_rep, "region"].mode()[0]
    if region:
        reps = reps[reps["region"] == region]
    disc = reps.groupby("sales_rep")["discount"].mean().round(3).sort_values(ascending=False)
    rep_caption = f"Reps in {region}" if region else f"Rep {top_rep} ({top_region}) highlighted"

    # Chart 2: margin % by region (orders with a known cost only)
    known = orders[orders["cost"].notna()]
    margin = known.groupby("region").apply(lambda d: d["margin"].sum() / d["net"].sum(), include_groups=False)
    margin = margin.round(3).sort_values(ascending=False)

    return [
        {"title": "Average discount by sales rep", "caption": rep_caption,
         "desc": "How much off list price each rep gives on average. One rep stands far above the rest.",
         "data": disc.to_frame("avg_discount"), "kind": "bar", "format": "percent", "sort": True,
         "highlight": top_rep, "x_title": "Sales rep"},
        {"title": "Margin % by region", "caption": f"{top_region} keeps half as much of each dollar",
         "desc": "Profit left after costs and discounts, per region. Orders with an unknown cost are left out.",
         "data": margin.to_frame("margin"), "kind": "bar", "format": "percent",
         "highlight": top_region, "x_title": "Region"},
    ]


def get_insights():
    _, orders, returns, *_ = load_data()

    # 1. discounting
    reps = orders[orders["sales_rep"] != "Self-serve"]
    rep_disc = reps.groupby("sales_rep")["discount"].mean().sort_values(ascending=False)
    top_rep, top_disc = rep_disc.index[0], rep_disc.iloc[0]
    others_disc = rep_disc.iloc[1:].mean()
    top_region = reps.loc[reps["sales_rep"] == top_rep, "region"].mode()[0]
    in_region = orders[orders["region"] == top_region]
    region_margin, rest_margin = margin_pct(in_region), margin_pct(orders[orders["region"] != top_region])
    known_region_net = in_region.loc[in_region["cost"].notna(), "net"].sum()
    gap = (rest_margin - region_margin) * known_region_net

    # 2. returns
    by_product = orders.groupby("product").agg(refund=("refund", "sum"), net=("net", "sum"))
    by_product["rate"] = by_product["refund"] / by_product["net"]
    worst = by_product.sort_values("rate", ascending=False).iloc[0]
    worst_name = worst.name
    reasons = returns.merge(orders[["order_id", "product"]], on="order_id")
    top_reason = reasons.loc[reasons["product"] == worst_name, "reason"].value_counts()
    overall_rate = orders["refund"].sum() / orders["net"].sum()

    # 3. unpaid invoices
    unpaid = orders[orders["payment_date"].isna()]
    past_due = unpaid[unpaid["days_overdue"] > 0]

    return [
        {
            "title": f"{top_region}'s growth is bought with discounts",
            "what": f"Rep {top_rep} gives an average {top_disc:.0%} discount, against {others_disc:.0%} for the other reps. "
                    f"{top_region} keeps a {region_margin:.0%} margin; the other regions keep {rest_margin:.0%}.",
            "why": f"At the other regions' margin, {top_region} would have earned about {money(gap)} more. "
                   "This is why profit isn't keeping up with revenue.",
            "todo": "Require manager approval for any discount above a cap, and check whether the volume survives at normal prices.",
        },
        {
            "title": f"One product drives the refunds: {worst_name}",
            "what": f"{worst['rate']:.0%} of its revenue is refunded ({money(worst['refund'])}), against {overall_rate:.0%} overall. "
                    f"The most common reason is \"{top_reason.index[0]}\" ({top_reason.iloc[0]} of {top_reason.sum()} returns).",
            "why": "Refunds come straight out of profit, and damaged big items usually can't be resold.",
            "todo": "Review packaging and the carrier for this product before the next shipment.",
        },
        {
            "title": "Unpaid invoices are real, but the smaller leak",
            "what": f"{len(unpaid)} invoices ({money(unpaid['net'].sum())}) are unpaid; "
                    f"{len(past_due)} of them ({money(past_due['net'].sum())}) are past their due date.",
            "why": f"That is {unpaid['net'].sum() / orders['net'].sum():.0%} of revenue: worth chasing, but less than the discount gap.",
            "todo": "Send reminders automatically, oldest first, and hold new orders for customers over their credit limit.",
        },
    ]

def detect_discounts(orders, discount_cap):
    """Orders from the latest quarter where a rep gave more than the discount cap."""
    # RULE: a sales rep's order whose discount is above the cap, in the most recent quarter.
    latest_quarter = orders["order_date"].max().to_period("Q")
    recent = orders[orders["order_date"].dt.to_period("Q") == latest_quarter]
    flagged = recent[(recent["sales_rep"] != "Self-serve") & (recent["discount"] > discount_cap)].copy()

    # What the extra discount cost: the part of the discount above the cap, in dollars.
    flagged["given_up"] = flagged["gross"] * (flagged["discount"] - discount_cap)

    per_rep = (
        flagged.groupby(["sales_rep", "region"])
        .agg(orders=("order_id", "count"), avg_discount=("discount", "mean"), revenue=("net", "sum"), given_up=("given_up", "sum"))
        .reset_index()
        .sort_values("given_up", ascending=False)
    )
    rows = pd.DataFrame(
        {
            "Sales rep": per_rep["sales_rep"],
            "Region": per_rep["region"],
            "Orders over cap": per_rep["orders"],
            "Avg discount": per_rep["avg_discount"].map("{:.0%}".format),
            "Revenue": per_rep["revenue"].map("${:,.0f}".format),
            "Margin given up": per_rep["given_up"].map("${:,.0f}".format),
        }
    )
    drafts = pd.DataFrame(
        [
            {
                "to": "Sales manager",
                "subject": f"Discount approval needed: rep {r.sales_rep} ({r.region})",
                "message": (
                    f"Rep {r.sales_rep} ({r.region}) closed {r.orders} orders in {latest_quarter} with a discount above "
                    f"the {discount_cap:.0%} cap (average {r.avg_discount:.0%}). The discount above the cap cost about "
                    f"${r.given_up:,.0f} in margin. Please review and approve or decline these discounts."
                ),
            }
            for r in per_rep.itertuples()
        ]
    )
    total = flagged["given_up"].sum()
    found = "No orders above the cap"
    if len(per_rep):
        top = per_rep.iloc[0]
        found = f"{len(flagged)} orders above the {discount_cap:.0%} cap, {top['orders']} from rep {top['sales_rep']}"
    return {
        "name": "reps with orders above the discount cap",
        "severity": "High",
        "rule": f"a rep's order in {latest_quarter} with a discount above {discount_cap:.0%}",
        "rows": rows,
        "found": found,
        "actions": [
            f"Approval request drafted for {len(per_rep)} reps",
            f"Margin given up calculated: ${total:,.0f}",
            "Orders listed for the sales manager",
        ],
        "notify": "Sales manager",
        "impact": total,
        "drafts": drafts,
    }


def detect_overdue(orders, days):
    """Unpaid invoices more than `days` past their due date, grouped by customer."""
    # RULE: no payment date AND more than `days` days after the due date (order date + terms).
    flagged = orders[orders["payment_date"].isna() & (orders["days_overdue"] > days)]

    # Everything the customer still owes (not only the late part) against their credit limit.
    owed = orders[orders["payment_date"].isna()].groupby("customer_id")["net"].sum().rename("owed")

    per_customer = (
        flagged.groupby(["customer_id", "segment", "account_rep", "credit_limit"])
        .agg(region=("region", lambda r: r.mode()[0]), invoices=("order_id", "count"),
             amount=("net", "sum"), oldest=("days_overdue", "max"))
        .reset_index()
        .merge(owed, on="customer_id")
        .sort_values("amount", ascending=False)
    )
    per_customer["over_limit"] = per_customer["owed"] > per_customer["credit_limit"]
    rows = pd.DataFrame(
        {
            "customer": per_customer["customer_id"],
            "segment": per_customer["segment"],
            "region": per_customer["region"],
            "rep": per_customer["account_rep"],
            "invoices": per_customer["invoices"],
            "owes": per_customer["amount"].map("${:,.0f}".format),
            "days_late": per_customer["oldest"],  # oldest invoice; app.py's slider filters on this
            "credit used": (per_customer["owed"] / per_customer["credit_limit"]).map("{:.0%}".format),
        }
    )
    drafts = pd.DataFrame(
        [
            {
                "to": f"Customer {r.customer_id} (cc rep {r.account_rep})",
                "subject": f"Payment reminder: {r.invoices} overdue invoice(s)",
                "message": (
                    f"Hello, our records show {r.invoices} invoice(s) totalling ${r.amount:,.0f} past due, "
                    f"the oldest by {r.oldest} days. Could you let us know when we can expect payment? "
                    "Thank you, Chrome & Oak Accounts Receivable."
                ),
                "internal note": "Over credit limit: hold new orders" if r.over_limit else "",
            }
            for r in per_customer.itertuples()
        ]
    )
    total, n_hold = flagged["net"].sum(), int(per_customer["over_limit"].sum())
    actions = [f"Reminder email drafted for {len(per_customer)} customers", "Account reps copied on each reminder"]
    if n_hold:
        actions.append(f"Order hold recommended for {n_hold} customer(s) over their credit limit")
    return {
        "name": "customers with overdue invoices",
        "severity": "High",
        "rule": f"unpaid AND more than {days} days past the due date (order date + payment terms)",
        "rows": rows,
        "found": f"${total:,.0f} is more than {days} days late" if len(per_customer) else "No invoices this late",
        "actions": actions,
        "notify": "Finance (accounts receivable)",
        "impact": total,
        "drafts": drafts,
    }


def detect_returns(orders, returns, refund_rate, min_orders=20):
    """Products whose refunds are an unusually large share of their revenue."""
    # RULE: refund dollars / net revenue above the threshold, for products with at least `min_orders` orders.
    per_product = orders.groupby(["product", "category"]).agg(
        orders=("order_id", "count"), net=("net", "sum"), refund=("refund", "sum")
    ).reset_index()
    per_product["rate"] = per_product["refund"] / per_product["net"]
    flagged = per_product[(per_product["orders"] >= min_orders) & (per_product["rate"] > refund_rate)].sort_values(
        "refund", ascending=False
    )

    # Most common return reason for each flagged product
    reasons = returns.merge(orders[["order_id", "product"]], on="order_id")
    top_reason = reasons.groupby("product")["reason"].agg(lambda s: s.value_counts().index[0])
    n_returns = reasons.groupby("product").size()
    flagged = flagged.assign(
        reason=flagged["product"].map(top_reason), returns=flagged["product"].map(n_returns).fillna(0).astype(int)
    )
    rows = pd.DataFrame(
        {
            "Product": flagged["product"],
            "Category": flagged["category"],
            "Returns": flagged["returns"],
            "Refunded": flagged["refund"].map("${:,.0f}".format),
            "Refund rate": flagged["rate"].map("{:.1%}".format),
            "Top reason": flagged["reason"],
        }
    )
    drafts = pd.DataFrame(
        [
            {
                "to": "Operations manager",
                "subject": f"High returns: {r.product}",
                "message": (
                    f"{r.product} has had {r.returns} returns and ${r.refund:,.0f} refunded, {r.rate:.1%} of its revenue "
                    f"(threshold {refund_rate:.0%}). The most common reason is \"{r.reason}\". "
                    "Please review packaging and the carrier for this product."
                ),
            }
            for r in flagged.itertuples()
        ]
    )
    total = flagged["refund"].sum()
    found = "No product above the threshold"
    if len(flagged):
        top = flagged.iloc[0]
        found = f"{top['product']}: {top['rate']:.0%} of revenue refunded"
    return {
        "name": "products with high return rates",
        "severity": "Medium",
        "rule": f"refunds above {refund_rate:.0%} of the product's revenue (at least {min_orders} orders)",
        "rows": rows,
        "found": found,
        "actions": [f"Ticket drafted for {len(flagged)} product(s)", "Top return reason attached to each ticket"],
        "notify": "Operations manager",
        "impact": total,
        "drafts": drafts,
    }


# ---------------------------------------------------------------------------
# DECIDE: the rules, their default thresholds, and the slider range for each
# ---------------------------------------------------------------------------
ALERT_RULES = [
    {"id": "overdue", "slider": "Flag invoices more than N days late", "unit": "days",
     "min": 0, "max": 90, "step": 5, "default": 30},
    {"id": "discount", "slider": "Discount cap (%)", "unit": "%",
     "min": 5, "max": 40, "step": 1, "default": 15},
    {"id": "returns", "slider": "Flag refunds above (% of a product's revenue)", "unit": "%",
     "min": 2, "max": 15, "step": 1, "default": 5},
]
DEFAULTS = {r["id"]: r["default"] for r in ALERT_RULES}


def run_rule(rule_id, value):
    """Run one detection at one slider value (days for overdue, whole percent for the others)."""
    _, orders, returns, *_ = load_data()
    if rule_id == "overdue":
        issue = detect_overdue(orders, value)
    elif rule_id == "discount":
        issue = detect_discounts(orders, value / 100)
    else:
        issue = detect_returns(orders, returns, value / 100)
    return {"id": rule_id, "setting": value, **issue}


def _detect_all(settings=None):
    """Run all three detections. `settings` maps rule id -> slider value; missing ones use the defaults."""
    settings = {**DEFAULTS, **(settings or {})}
    return [run_rule(r["id"], settings[r["id"]]) for r in ALERT_RULES]

# ---------------------------------------------------------------------------
# What the petbiz UI shows for each alert on Insights / Alerts
# ---------------------------------------------------------------------------
_EXTRA = {
    "overdue": {
        "button": "Send reminders",
        "how": "Invoices past their due date with no payment date, totalled per customer.",
        "what": "Cash is stuck with customers who haven't paid. That's why cash feels tight even though revenue is up.",
        "fix": "Send payment reminders and pause new orders for accounts over their credit limit.",
    },
    "discount": {
        "button": "Send to manager",
        "how": "The part of each discount above the cap, in dollars, for the latest quarter.",
        "what": "A few reps give far more off than the rest, so revenue grows while profit doesn't.",
        "fix": "Require manager approval for discounts above the cap.",
    },
    "returns": {
        "button": "Send to operations",
        "how": "Refunds paid on each product as a share of that product's revenue.",
        "what": "Some products come back far more often than others, and every refund is revenue given back.",
        "fix": "Check packaging and the carrier for the flagged products.",
    },
}


def detect_issues(days=30):
    """The three alerts. The overdue rule follows the petbiz 'days' slider."""
    issues = _detect_all({"overdue": days})
    for i in issues:
        i["cost"] = -float(i["impact"])  # petbiz ranks problems by cost, shown as -$
        for k, v in _EXTRA[i["id"]].items():
            i.setdefault(k, v)
    return issues
