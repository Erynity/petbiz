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
