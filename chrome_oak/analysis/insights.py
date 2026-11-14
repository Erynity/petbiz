"""DETECT: the charts and the insights (what happened / why it matters / what to do)."""

import pandas as pd

from chrome_oak.analysis.metrics import margin_pct, money
from chrome_oak.config import ASOF
from chrome_oak.data.loader import load_data


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


def refunds_chart():
    _, orders, *_ = load_data()
    refunds = orders.groupby("product")["refund"].sum().sort_values(ascending=False)
    return {"title": "Refunds by product", "caption": "One product drives most of the refunds",
            "data": refunds.to_frame("refunds"), "kind": "hbar", "format": "dollar", "highlight": refunds.index[0]}


def aging_chart():
    _, orders, *_ = load_data()
    unpaid = orders[orders["payment_date"].isna()]
    buckets = pd.cut(unpaid["days_overdue"], [-10_000, 0, 30, 60, 90, 10_000],
                     labels=["Not due yet", "1–30", "31–60", "61–90", "90+"])
    aging = unpaid.groupby(buckets, observed=False)["net"].sum()
    return {"title": "Unpaid invoices by days late", "caption": f"Money still owed on {ASOF:%b %d, %Y}",
            "data": aging.to_frame("unpaid"), "kind": "bar", "format": "dollar", "highlight": ["61–90", "90+"],
            "x_title": "Days late"}


def growth_chart():
    """Revenue vs gross profit per quarter (orders with a known cost)."""
    _, orders, *_ = load_data()
    known = orders[orders["cost"].notna()]
    quarter = known["order_date"].dt.to_period("Q")
    q = known.groupby(quarter).agg(Revenue=("net", "sum"), **{"Gross profit": ("margin", "sum")})
    q.index = [f"{p.year} Q{p.quarter}" for p in q.index]
    return {"title": "Revenue is growing faster than profit", "caption": "Revenue and gross profit per quarter",
            "data": q.round(0), "kind": "line", "format": "dollar"}


def region_revenue_chart():
    _, orders, *_ = load_data()
    rev = orders.groupby("region")["net"].sum().sort_values(ascending=False)
    return {"title": "Revenue by region", "caption": "Atlantic is the #2 region for sales…",
            "data": rev.to_frame("revenue"), "kind": "bar", "format": "dollar", "highlight": "Atlantic", "x_title": "Region"}


def get_insight_charts(region=None):
    """The charts behind each insight, in the same order as get_insights()."""
    rep_chart, region_chart = get_charts(region)
    return [[growth_chart(), region_revenue_chart(), {**region_chart, "caption": "…but keeps half the margin"}, rep_chart],
            [refunds_chart()], [aging_chart()]]
