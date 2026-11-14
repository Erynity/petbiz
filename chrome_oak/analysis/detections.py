"""DETECT -> ACT: three conditions, each with a drafted action.

Each detect_* function is a few lines of plain rule logic (see the "# RULE:" comment),
then builds the table shown on the Alerts page and the messages to send.
"""

import pandas as pd

from chrome_oak.data.loader import load_data


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


def detect_issues(settings=None):
    """Run all three detections. `settings` maps rule id -> slider value; missing ones use the defaults."""
    settings = {**DEFAULTS, **(settings or {})}
    return [run_rule(r["id"], settings[r["id"]]) for r in ALERT_RULES]
