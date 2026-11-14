"""DETECT: the charts and the insights (what happened / why it matters / what to do)."""

from chrome_oak.analysis.metrics import margin_pct, money
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
