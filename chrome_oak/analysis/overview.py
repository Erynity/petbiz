"""DATA -> DECIDE: the headline. The one problem we chose, and the numbers on the Overview page."""

from chrome_oak.analysis.metrics import jan_sep, margin_pct, money
from chrome_oak.data.loader import load_data


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
    """The four headline numbers, each with a quarterly trend and a few supporting details."""
    _, orders, returns, *_ = load_data()
    known = orders[orders["cost"].notna()]
    quarter = orders["order_date"].dt.to_period("Q")
    q_labels = [f"Q{p.quarter} {p.year}" for p in sorted(quarter.unique())]

    # Revenue
    r25, r26 = jan_sep(orders, 2025)["net"].sum(), jan_sep(orders, 2026)["net"].sum()
    q_net = orders.groupby(quarter)["net"].sum()
    by_region = orders.groupby("region")["net"].sum().sort_values(ascending=False)
    biz_share = orders.loc[orders["terms_days"] > 0, "net"].sum() / orders["net"].sum()

    # Margin
    kq = known["order_date"].dt.to_period("Q")
    q_margin = known.groupby(kq)["margin"].sum() / known.groupby(kq)["net"].sum()
    atl = margin_pct(orders[orders["region"] == "Atlantic"])
    rest = margin_pct(orders[orders["region"] != "Atlantic"])

    # Past due
    unpaid = orders[orders["payment_date"].isna()]
    past_due = unpaid[unpaid["days_overdue"] > 0]
    q_past_due = past_due.groupby(past_due["order_date"].dt.to_period("Q"))["net"].sum().reindex(q_net.index, fill_value=0)

    # Refunds
    refund_total = orders["refund"].sum()
    q_refund = orders.groupby(quarter)["refund"].sum() / q_net
    by_product = orders.groupby("product")["refund"].sum().sort_values(ascending=False)
    top_reason = returns["reason"].value_counts()

    return [
        {"label": "Revenue, Jan–Sep 2026", "value": money(r26), "delta": f"{r26 / r25 - 1:+.0%} vs Jan–Sep 2025",
         "trend": q_net.round(0).tolist(), "trend_labels": q_labels, "trend_fmt": "dollar",
         "details": [("Same period 2025", money(r25)),
                     ("Biggest region", f"{by_region.index[0]} · {money(by_region.iloc[0])}"),
                     ("From business customers", f"{biz_share:.0%}")]},
        {"label": "Gross margin", "value": f"{margin_pct(orders):.0%}", "delta": f"{(q_margin.iloc[-1] - q_margin.iloc[0]) * 100:+.1f} pts since {q_labels[0]}",
         "trend": q_margin.round(3).tolist(), "trend_labels": q_labels, "trend_fmt": "percent",
         "details": [("Atlantic", f"{atl:.0%}"), ("All other regions", f"{rest:.0%}"),
                     ("Orders with no cost (left out)", f"{orders['cost'].isna().sum()}")]},
        {"label": "Past-due invoices", "value": money(past_due["net"].sum()), "delta": f"{len(past_due)} invoices from {past_due['customer_id'].nunique()} customers",
         "trend": q_past_due.round(0).tolist(), "trend_labels": q_labels, "trend_fmt": "dollar",
         "details": [("Total unpaid (incl. not due yet)", money(unpaid["net"].sum())),
                     ("More than 60 days late", money(past_due.loc[past_due["days_overdue"] > 60, "net"].sum())),
                     ("Oldest invoice", f"{int(past_due['days_overdue'].max())} days late")]},
        {"label": "Refunded", "value": f"{refund_total / orders['net'].sum():.1%}", "delta": f"{money(refund_total)} given back on {len(returns)} returns",
         "trend": q_refund.round(3).tolist(), "trend_labels": q_labels, "trend_fmt": "percent",
         "details": [("Biggest product", f"{by_product.index[0]} · {by_product.iloc[0] / refund_total:.0%}"),
                     ("Top reason", f"{top_reason.index[0]} · {top_reason.iloc[0]}"),
                     ("Orders returned", f"{len(returns) / len(orders):.1%} of all orders")]},
    ]
