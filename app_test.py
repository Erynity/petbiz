"""PetBiz – testing app: insights + visualizations on the cleaned data.

Run with:  .venv/bin/streamlit run app_test.py
"""

import altair as alt
import pandas as pd
import streamlit as st

from cleaning import clean_all

st.set_page_config(page_title="PetBiz (test)", page_icon="🐱", layout="wide")

ASOF = pd.Timestamp("2026-10-31")  # the date the data was extracted

# Chart colors: one muted base, one highlight (orange from the reference palette)
BASE, HILITE, INK, MUTED = "#B9B3C6", "#EB6834", "#3A2350", "#6B5A80"

THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Alfa+Slab+One&family=Nunito:wght@400;600;700;800&display=swap');
.stApp{background:#FFF8F0}
html, body, [class*="css"], .stMarkdown, p, li, label{font-family:'Nunito',sans-serif;color:#3A2350}
h1, h2, h3{font-family:'Alfa Slab One',serif !important;font-weight:400 !important;color:#3A2350 !important}
.block-container{padding-top:1.5rem;max-width:1250px}
[data-testid="stMetric"]{background:#FFFFFF;border:3px solid #E4D6F5;border-radius:24px;padding:18px 20px}
[data-testid="stMetricLabel"] p{font-weight:700;color:#6B5A80}
[data-testid="stMetricValue"]{font-family:'Alfa Slab One',serif;color:#3A2350}
.card{background:#FFFFFF;border:3px solid #E4D6F5;border-radius:24px;padding:20px 22px;height:100%}
.card h4{margin:0 0 10px;font-size:19px;font-weight:800;color:#3A2350}
.card .label{font-size:13px;font-weight:800;color:#8E6FC2;text-transform:uppercase;letter-spacing:1px;margin-top:10px}
.card p{margin:2px 0 0;font-size:16px;line-height:1.5}
.step{display:inline-block;background:#3A2350;color:#FFFFFF;font-weight:800;font-size:13px;letter-spacing:1px;padding:4px 12px;border-radius:999px;margin:18px 0 6px}
</style>
"""
st.markdown(THEME_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# DATA
# ---------------------------------------------------------------------------
@st.cache_data
def load():
    customers, orders, returns, dropped, fixes = clean_all()
    orders = orders.merge(customers[["customer_id", "segment", "payment_terms", "credit_limit"]], on="customer_id")
    refunds = returns.groupby("order_id")["refund_amount"].sum().rename("refund")
    orders = orders.merge(refunds, on="order_id", how="left")
    orders["refund"] = orders["refund"].fillna(0)
    orders["terms_days"] = orders["payment_terms"].map({"Prepaid": 0, "Net 30": 30, "Net 60": 60})
    orders["due_date"] = orders["order_date"] + pd.to_timedelta(orders["terms_days"], unit="D")
    return customers, orders, returns, dropped, fixes


customers, orders, returns, dropped, fixes = load()

# Margin is only known where unit_cost exists
known = orders[orders["cost"].notna()]


def margin_pct(df):
    return df["margin"].sum() / df["net"].sum()


def bar(df, x, y, highlight, fmt, title_x="", horizontal=False, height=260):
    """One-series bar chart: muted bars, highlighted entity in orange, value labels on the bars."""
    d = df.copy()
    d["_hi"] = d[x].isin(highlight)
    color = alt.condition(alt.datum._hi, alt.value(HILITE), alt.value(BASE))
    tip = [alt.Tooltip(f"{x}:N"), alt.Tooltip(f"{y}:Q", format=fmt)]
    base = alt.Chart(d).encode(
        x=alt.X(f"{x}:N", sort="-y", title=title_x, axis=alt.Axis(labelAngle=0, domain=False, ticks=False, labelColor=MUTED)),
        y=alt.Y(f"{y}:Q", title=None, axis=alt.Axis(format=fmt, grid=True, gridColor="#EFE8F7", domain=False, ticks=False, labelColor=MUTED)),
        tooltip=tip,
    )
    bars = base.mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, size=34).encode(color=color)
    labels = base.mark_text(dy=-8, fontWeight="bold", color=INK).encode(text=alt.Text(f"{y}:Q", format=fmt))
    return (bars + labels).properties(height=height).configure_view(strokeWidth=0).configure(background="transparent")


# ---------------------------------------------------------------------------
# HEADLINE NUMBERS
# ---------------------------------------------------------------------------
jan_sep = orders[orders["order_date"].dt.month <= 9]
rev_25 = jan_sep.loc[jan_sep["order_date"].dt.year == 2025, "net"].sum()
rev_26 = jan_sep.loc[jan_sep["order_date"].dt.year == 2026, "net"].sum()
growth = rev_26 / rev_25 - 1

region = known.groupby("region").apply(lambda d: pd.Series({"margin": margin_pct(d), "net": d["net"].sum()}), include_groups=False)
atl_margin = region.loc["Atlantic", "margin"]
rest = known[known["region"] != "Atlantic"]
rest_margin = margin_pct(rest)
atl_net = region.loc["Atlantic", "net"]
margin_gap_dollars = (rest_margin - atl_margin) * atl_net

unpaid = orders[orders["payment_date"].isna()].copy()
unpaid["days_overdue"] = (ASOF - unpaid["due_date"]).dt.days

# ---------------------------------------------------------------------------
# PAGE
# ---------------------------------------------------------------------------
st.title("Chrome & Oak · what's behind the growth?")
st.caption(f"Cleaned data · orders Jan 2025 – Sep 2026 · extracted {ASOF:%b %d, %Y} · {len(orders):,} orders ({len(dropped)} removed in cleaning)")

tab_insights, tab_recv, tab_data = st.tabs(["Insights", "Receivables monitor", "Explore data"])

with tab_insights:
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Net revenue, Jan–Sep 2026", f"${rev_26/1e6:,.2f}M", f"{growth:+.0%} vs 2025")
    k2.metric("Margin, all regions except Atlantic", f"{rest_margin:.0%}")
    k3.metric("Margin, Atlantic", f"{atl_margin:.0%}", f"{(atl_margin - rest_margin) * 100:+.0f} pts", delta_color="inverse")
    k4.metric("Unpaid invoices", f"${unpaid['net'].sum()/1e3:,.0f}K", f"{len(unpaid)} orders", delta_color="off")

    # ----- Insight 1: discounts -----
    st.markdown('<span class="step">INSIGHT 1 · MARGIN</span>', unsafe_allow_html=True)
    st.subheader("Atlantic's growth is bought with discounts")
    rep = (
        known[known["sales_rep"] != "Self-serve"]
        .groupby("sales_rep")
        .apply(lambda d: pd.Series({"discount": d["discount"].mean(), "net": d["net"].sum(), "region": d["region"].mode()[0]}), include_groups=False)
        .reset_index()
    )
    top_rep = rep.sort_values("discount", ascending=False).iloc[0]
    other_reps_disc = rep[rep["sales_rep"] != top_rep["sales_rep"]]["discount"].mean()
    atl_all = orders[orders["region"] == "Atlantic"]
    top_rep_share = atl_all.loc[atl_all["sales_rep"] == top_rep["sales_rep"], "net"].sum() / atl_all["net"].sum()
    region_chart = region.reset_index()

    c1, c2 = st.columns(2)
    with c1:
        st.caption("Average discount by sales rep (Atlantic rep highlighted)")
        st.altair_chart(bar(rep, "sales_rep", "discount", [top_rep["sales_rep"]], ".0%", "Sales rep"), width="stretch", theme=None)
    with c2:
        st.caption("Margin % by region (Atlantic highlighted)")
        st.altair_chart(bar(region_chart, "region", "margin", ["Atlantic"], ".0%", "Region"), width="stretch", theme=None)

    st.markdown(
        f'<div class="card"><h4>One rep is discounting at 2–3× everyone else</h4>'
        f'<div class="label">What happened</div><p>Revenue is up {growth:.0%}, and Atlantic is the second-biggest region '
        f'(${atl_net/1e6:,.1f}M). But rep {top_rep["sales_rep"]} gives an average {top_rep["discount"]:.0%} discount against '
        f'{other_reps_disc:.0%} for the other reps, and sells {top_rep_share:.0%} of Atlantic revenue. '
        f'Atlantic earns a {atl_margin:.0%} margin vs {rest_margin:.0%} elsewhere.</p>'
        f'<div class="label">Why it matters</div><p>At the other regions\' margin, Atlantic would have earned about '
        f'<b>${margin_gap_dollars/1e3:,.0f}K</b> more. This is why profit isn\'t keeping up with revenue.</p>'
        f'<div class="label">What to do</div><p>Put a discount cap on rep {top_rep["sales_rep"]} that needs manager approval to exceed, '
        f'and review whether the Atlantic volume survives at normal prices.</p></div>',
        unsafe_allow_html=True,
    )

    # ----- Insight 2: returns -----
    st.markdown('<span class="step">INSIGHT 2 · RETURNS</span>', unsafe_allow_html=True)
    st.subheader("Furniture returns cost 4× more than accessories")
    cat = orders.groupby("category").apply(lambda d: pd.Series({"refund_rate": d["refund"].sum() / d["net"].sum(), "refund": d["refund"].sum()}), include_groups=False).reset_index()
    worst = cat.sort_values("refund_rate", ascending=False).iloc[0]
    best = cat.sort_values("refund_rate").iloc[0]
    ret_cat = returns.merge(orders[["order_id", "category", "product"]], on="order_id")
    f_reasons = ret_cat[ret_cat["category"] == worst["category"]]["reason"].value_counts()
    prod = (
        orders[orders["category"] == worst["category"]]
        .groupby("product")
        .apply(lambda d: d["refund"].sum() / d["net"].sum(), include_groups=False)
        .rename("refund_rate")
        .reset_index()
    )

    c3, c4 = st.columns(2)
    with c3:
        st.caption("Refunds as % of revenue, by category")
        st.altair_chart(bar(cat, "category", "refund_rate", [worst["category"]], ".1%", "Category"), width="stretch", theme=None)
    with c4:
        st.caption(f"Return reasons for {worst['category']} (number of returns)")
        rs = f_reasons.rename_axis("reason").reset_index(name="returns")
        st.altair_chart(bar(rs, "reason", "returns", [rs.iloc[0]["reason"]], "d", "Reason"), width="stretch", theme=None)

    st.markdown(
        f'<div class="card"><h4>Big items come back, and cost real money</h4>'
        f'<div class="label">What happened</div><p>{worst["category"]} refunds are {worst["refund_rate"]:.1%} of its revenue '
        f'(${worst["refund"]/1e3:,.0f}K), against {best["refund_rate"]:.1%} for {best["category"]}. '
        f'The most common reason for {worst["category"]} returns is "{f_reasons.index[0]}".</p>'
        f'<div class="label">Why it matters</div><p>Refunds come straight out of margin, and damaged big items usually can\'t be resold.</p>'
        f'<div class="label">What to do</div><p>Look at packaging and carrier handling for furniture first.</p></div>',
        unsafe_allow_html=True,
    )

    # ----- Insight 3: unpaid -----
    st.markdown('<span class="step">INSIGHT 3 · CASH</span>', unsafe_allow_html=True)
    st.subheader("Unpaid invoices are a smaller problem than they feel")
    bins = [-10_000, 0, 30, 60, 90, 10_000]
    labels = ["Not yet due", "1–30 days late", "31–60 days late", "61–90 days late", "90+ days late"]
    unpaid["bucket"] = pd.cut(unpaid["days_overdue"], bins=bins, labels=labels)
    aging = unpaid.groupby("bucket", observed=False)["net"].sum().reset_index()
    overdue_total = unpaid.loc[unpaid["days_overdue"] > 0, "net"].sum()
    total_net = orders["net"].sum()

    st.caption(f"Unpaid orders by how late they are on {ASOF:%b %d, %Y} ($)")
    aging_chart = bar(aging, "bucket", "net", labels[1:], "$,.0f", "", height=260)
    st.altair_chart(aging_chart, width="stretch", theme=None)

    st.markdown(
        f'<div class="card"><h4>The overdue pile is real, but it is not the main leak</h4>'
        f'<div class="label">What happened</div><p>{len(unpaid)} orders (${unpaid["net"].sum()/1e3:,.0f}K) are unpaid; '
        f'${overdue_total/1e3:,.0f}K of that is past its due date. That is {unpaid["net"].sum()/total_net:.1%} of all revenue billed.</p>'
        f'<div class="label">Why it matters</div><p>It explains some of the cash squeeze, but the Atlantic margin gap '
        f'(~${margin_gap_dollars/1e3:,.0f}K) is larger.</p>'
        f'<div class="label">What to do</div><p>Chase the oldest invoices first, but fix discounting before it.</p></div>',
        unsafe_allow_html=True,
    )

with tab_recv:
    st.subheader("Who owes us money, and how late is it?")
    st.caption(
        "Business customers pay on terms (Net 30 / Net 60). Each order is treated as one invoice, "
        f"due on order date + terms. Status is as of {ASOF:%b %d, %Y}."
    )

    # --- per-customer picture (business customers only; consumers prepay) ---
    biz = orders[orders["terms_days"] > 0]
    paid = biz[biz["payment_date"].notna()].copy()
    paid["days_late"] = (paid["payment_date"] - paid["due_date"]).dt.days
    history = paid.groupby("customer_id").agg(
        avg_days_late=("days_late", "mean"),
        pct_paid_late=("days_late", lambda s: (s > 0).mean()),
    )

    open_inv = unpaid[unpaid["terms_days"] > 0]
    balance = open_inv.groupby("customer_id").agg(
        unpaid=("net", "sum"), open_invoices=("order_id", "count"), oldest_days_overdue=("days_overdue", "max")
    )
    balance["overdue"] = open_inv[open_inv["days_overdue"] > 0].groupby("customer_id")["net"].sum()
    balance["overdue"] = balance["overdue"].fillna(0)

    recv = (
        balance.join(history)
        .reset_index()
        .merge(customers[["customer_id", "segment", "region", "payment_terms", "credit_limit"]], on="customer_id")
    )
    recv["credit_used"] = recv["unpaid"] / recv["credit_limit"]

    def flag(r):
        if r["credit_used"] > 1:
            return "Over credit limit"
        if r["oldest_days_overdue"] > 60:
            return "60+ days overdue"
        if r["oldest_days_overdue"] > 0:
            return "Overdue"
        return "Not yet due"

    recv["status"] = recv.apply(flag, axis=1)

    # --- headline numbers ---
    n_overdue_cust = int((recv["overdue"] > 0).sum())
    near_limit = int((recv["credit_used"] >= 0.8).sum())
    r1, r2, r3, r4, r5 = st.columns(5)
    r1.metric("Unpaid", f"${recv['unpaid'].sum()/1e3:,.0f}K", f"{int(recv['open_invoices'].sum())} invoices", delta_color="off")
    r2.metric("Past due", f"${recv['overdue'].sum()/1e3:,.0f}K", f"{n_overdue_cust} customers", delta_color="off")
    r3.metric("Oldest invoice", f"{int(recv['oldest_days_overdue'].max())} days late")
    r4.metric("Paid late (history)", f"{(paid['days_late'] > 0).mean():.0%}", f"avg {paid['days_late'].mean():+.1f} days vs due", delta_color="off")
    r5.metric("Near/over credit limit", near_limit, "customers ≥ 80% used", delta_color="off")

    # --- charts ---
    cc1, cc2 = st.columns(2)
    with cc1:
        st.caption("Unpaid orders by how late they are ($) — late buckets highlighted")
        st.altair_chart(bar(aging, "bucket", "net", labels[1:], "$,.0f", "", height=280), width="stretch", theme=None)
    with cc2:
        top = recv.sort_values("overdue", ascending=False).head(10)
        st.caption("Top 10 customers by past-due $ — 60+ days late highlighted")
        st.altair_chart(
            bar(top, "customer_id", "overdue", top.loc[top["oldest_days_overdue"] > 60, "customer_id"].tolist(), "$,.0f", "Customer", height=280),
            width="stretch",
            theme=None,
        )

    # --- filterable, sortable customer table ---
    st.markdown('<span class="step">CUSTOMERS WITH OPEN INVOICES</span>', unsafe_allow_html=True)
    f1, f2, f3, f4 = st.columns(4)
    seg_sel = f1.multiselect("Segment", sorted(recv["segment"].unique()), default=sorted(recv["segment"].unique()))
    reg_sel = f2.multiselect("Region", sorted(recv["region"].unique()), default=sorted(recv["region"].unique()))
    min_late = f3.slider("Oldest invoice at least N days late", 0, int(recv["oldest_days_overdue"].max()), 0)
    sort_by = f4.selectbox(
        "Sort by",
        ["Past-due $", "Unpaid $", "Oldest days late", "Credit used", "Avg days late (history)"],
    )
    sort_col = {
        "Past-due $": "overdue",
        "Unpaid $": "unpaid",
        "Oldest days late": "oldest_days_overdue",
        "Credit used": "credit_used",
        "Avg days late (history)": "avg_days_late",
    }[sort_by]

    view = recv[
        recv["segment"].isin(seg_sel) & recv["region"].isin(reg_sel) & (recv["oldest_days_overdue"] >= min_late)
    ].sort_values(sort_col, ascending=False)

    st.caption(f"{len(view)} customers · ${view['unpaid'].sum():,.0f} unpaid · ${view['overdue'].sum():,.0f} past due")
    st.dataframe(
        view[
            ["customer_id", "status", "segment", "region", "payment_terms", "unpaid", "overdue", "open_invoices",
             "oldest_days_overdue", "credit_limit", "credit_used", "avg_days_late", "pct_paid_late"]
        ],
        width="stretch",
        hide_index=True,
        column_config={
            "customer_id": "Customer",
            "status": "Status",
            "segment": "Segment",
            "region": "Region",
            "payment_terms": "Terms",
            "unpaid": st.column_config.NumberColumn("Unpaid $", format="$%,.0f"),
            "overdue": st.column_config.NumberColumn("Past due $", format="$%,.0f"),
            "open_invoices": st.column_config.NumberColumn("Open invoices"),
            "oldest_days_overdue": st.column_config.NumberColumn("Oldest days late", help="Negative = not yet due"),
            "credit_limit": st.column_config.NumberColumn("Credit limit", format="$%,.0f"),
            "credit_used": st.column_config.ProgressColumn("Credit used", format="percent", min_value=0, max_value=1),
            "avg_days_late": st.column_config.NumberColumn("Avg days late (paid)", format="%.1f"),
            "pct_paid_late": st.column_config.NumberColumn("% paid late", format="percent"),
        },
    )

    # --- drill-down: the invoices behind one customer ---
    if len(view):
        pick = st.selectbox("See the invoices behind a customer", view["customer_id"].tolist())
        inv = open_inv[open_inv["customer_id"] == pick].sort_values("days_overdue", ascending=False)
        st.dataframe(
            inv[["order_id", "order_date", "due_date", "days_overdue", "product", "quantity", "net"]],
            width="stretch",
            hide_index=True,
            column_config={
                "net": st.column_config.NumberColumn("Amount", format="$%,.0f"),
                "days_overdue": st.column_config.NumberColumn("Days late", help="Negative = not yet due"),
                "order_date": st.column_config.DateColumn("Ordered"),
                "due_date": st.column_config.DateColumn("Due"),
            },
        )

with tab_data:
    st.subheader("Cleaned data")
    st.caption("Raw files are untouched. Row-by-row drops are in CLEANING_LOG.md.")
    tables = {"customers": customers, "orders": orders, "returns": returns}
    sub = st.tabs(list(tables))
    for t, (name, df) in zip(sub, tables.items()):
        with t:
            st.caption(f"{len(df):,} rows × {df.shape[1]} columns")
            st.dataframe(df, width="stretch", hide_index=True)
