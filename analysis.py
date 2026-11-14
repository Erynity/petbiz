"""Data work for the Chrome & Oak health check.

app.py / app_copy.py only DISPLAY results; everything they show comes from here:

    get_focus()        the one problem we chose, in one sentence
    get_kpis()         headline numbers
    get_charts()       the two charts
    get_prep_steps()   what we changed in the data and why
    get_insights()     what happened / why it matters / what to do
    detect_issues()    the three detections, each with a drafted action

Cleaning itself lives in cleaning.py (clean_all).
"""

from functools import lru_cache
from pathlib import Path
from typing import Dict, Union

import pandas as pd

import cleaning

# The data was extracted on this date. Every "days late" number counts up to it.
ASOF = pd.Timestamp("2026-10-31")

TERMS_DAYS = {"Prepaid": 0, "Net 30": 30, "Net 60": 60}


def load_dataset(path: Union[str, Path]) -> pd.DataFrame:
    """Load a CSV dataset and reject empty files."""
    dataset = pd.read_csv(path)
    if dataset.empty:
        raise ValueError("the dataset is empty")
    return dataset


def summarize_dataset(dataset: pd.DataFrame) -> Dict[str, int]:
    """Return the basic dimensions needed by the app dashboard."""
    return {"rows": len(dataset), "columns": len(dataset.columns)}


# ---------------------------------------------------------------------------
# Loading: clean the three files, then join them into one orders table
# ---------------------------------------------------------------------------
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


def _margin_pct(df):
    """Margin as a share of revenue, on orders where the cost is known."""
    known = df[df["cost"].notna()]
    return known["margin"].sum() / known["net"].sum()


def _jan_sep(orders, year):
    return orders[(orders["order_date"].dt.year == year) & (orders["order_date"].dt.month <= 9)]


def _money(x):
    return f"${x/1e6:,.2f}M" if abs(x) >= 1e6 else f"${x/1e3:,.0f}K"


# ---------------------------------------------------------------------------
# Headline
# ---------------------------------------------------------------------------
def get_focus():
    _, orders, *_ = load_data()
    r25, r26 = _jan_sep(orders, 2025), _jan_sep(orders, 2026)
    rev_growth = r26["net"].sum() / r25["net"].sum() - 1
    k25, k26 = r25[r25["cost"].notna()], r26[r26["cost"].notna()]
    profit_growth = k26["margin"].sum() / k25["margin"].sum() - 1
    return (
        f"Revenue grew {rev_growth:.0%} but gross profit only {profit_growth:.0%}: "
        "the growth is being bought with discounts."
    )


def get_kpis():
    _, orders, *_ = load_data()
    r25, r26 = _jan_sep(orders, 2025)["net"].sum(), _jan_sep(orders, 2026)["net"].sum()
    atl = _margin_pct(orders[orders["region"] == "Atlantic"])
    rest = _margin_pct(orders[orders["region"] != "Atlantic"])
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
        {"label": "Revenue, Jan–Sep 2026", "value": _money(r26), "delta": f"{r26 / r25 - 1:+.0%} vs Jan–Sep 2025",
         "trend": q_net.round(0).tolist()},
        {"label": "Gross margin", "value": f"{_margin_pct(orders):.0%}", "delta": f"Atlantic {atl:.0%} · elsewhere {rest:.0%}",
         "trend": q_margin.round(3).tolist()},
        {"label": "Past-due invoices", "value": _money(past_due["net"].sum()), "delta": f"{len(past_due)} invoices",
         "trend": q_past_due.round(0).tolist()},
        {"label": "Refunded", "value": f"{refund_rate:.1%} of revenue", "delta": f"{_money(orders['refund'].sum())} given back",
         "trend": q_refund.round(3).tolist()},
    ]


def get_charts():
    """Two bar charts in the shape dashboard_view.py draws (format / sort / highlight / x_title)."""
    _, orders, *_ = load_data()

    # Chart 1: average discount by sales rep (online orders have no rep)
    reps = orders[orders["sales_rep"] != "Self-serve"]
    disc = reps.groupby("sales_rep")["discount"].mean().round(3).sort_values(ascending=False)
    top_rep = disc.index[0]
    top_region = reps.loc[reps["sales_rep"] == top_rep, "region"].mode()[0]

    # Chart 2: margin % by region (orders with a known cost only)
    known = orders[orders["cost"].notna()]
    margin = known.groupby("region").apply(lambda d: d["margin"].sum() / d["net"].sum(), include_groups=False)
    margin = margin.round(3).sort_values(ascending=False)

    return [
        {"title": "Average discount by sales rep", "caption": f"Rep {top_rep} ({top_region}) highlighted",
         "data": disc.to_frame("avg_discount"), "kind": "bar", "format": "percent", "sort": True,
         "highlight": top_rep, "x_title": "Sales rep"},
        {"title": "Margin % by region", "caption": f"{top_region} keeps half as much of each dollar",
         "data": margin.to_frame("margin"), "kind": "bar", "format": "percent",
         "highlight": top_region, "x_title": "Region"},
    ]


# ---------------------------------------------------------------------------
# Data preparation: what we changed, how many rows, and why
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Insights
# ---------------------------------------------------------------------------
def get_insights():
    _, orders, returns, *_ = load_data()

    # 1. discounting
    reps = orders[orders["sales_rep"] != "Self-serve"]
    rep_disc = reps.groupby("sales_rep")["discount"].mean().sort_values(ascending=False)
    top_rep, top_disc = rep_disc.index[0], rep_disc.iloc[0]
    others_disc = rep_disc.iloc[1:].mean()
    top_region = reps.loc[reps["sales_rep"] == top_rep, "region"].mode()[0]
    in_region = orders[orders["region"] == top_region]
    region_margin, rest_margin = _margin_pct(in_region), _margin_pct(orders[orders["region"] != top_region])
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
            "why": f"At the other regions' margin, {top_region} would have earned about {_money(gap)} more. "
                   "This is why profit isn't keeping up with revenue.",
            "todo": "Require manager approval for any discount above a cap, and check whether the volume survives at normal prices.",
        },
        {
            "title": f"One product drives the refunds: {worst_name}",
            "what": f"{worst['rate']:.0%} of its revenue is refunded ({_money(worst['refund'])}), against {overall_rate:.0%} overall. "
                    f"The most common reason is \"{top_reason.index[0]}\" ({top_reason.iloc[0]} of {top_reason.sum()} returns).",
            "why": "Refunds come straight out of profit, and damaged big items usually can't be resold.",
            "todo": "Review packaging and the carrier for this product before the next shipment.",
        },
        {
            "title": "Unpaid invoices are real, but the smaller leak",
            "what": f"{len(unpaid)} invoices ({_money(unpaid['net'].sum())}) are unpaid; "
                    f"{len(past_due)} of them ({_money(past_due['net'].sum())}) are past their due date.",
            "why": f"That is {unpaid['net'].sum() / orders['net'].sum():.0%} of revenue: worth chasing, but less than the discount gap.",
            "todo": "Send reminders automatically, oldest first, and hold new orders for customers over their credit limit.",
        },
    ]


# ---------------------------------------------------------------------------
# DETECT + ACT: three conditions, each with a drafted action
# ---------------------------------------------------------------------------
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


def detect_issues(days=30, discount_cap=0.15, refund_rate=0.05):
    """Run the three detections. `days`, `discount_cap` and `refund_rate` come from the sliders."""
    _, orders, returns, *_ = load_data()
    return [
        detect_overdue(orders, days),  # first: app.py's built-in slider is "days late"
        detect_discounts(orders, discount_cap),
        detect_returns(orders, returns, refund_rate),
    ]
