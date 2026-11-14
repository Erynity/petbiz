"""Interactive analysis tabs for the PetBiz test app: Analyze, Customers, Returns."""

import altair as alt
import pandas as pd
import streamlit as st

import viz

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------
TIME_COLS = ["month", "quarter", "year"]

DIMS = {
    "Region": "region",
    "Category": "category",
    "Product": "product",
    "Sales channel": "sales_channel",
    "Sales rep": "sales_rep",
    "Customer segment": "segment",
    "Payment terms": "payment_terms",
    "Customer": "customer_id",
    "Month": "month",
    "Quarter": "quarter",
    "Year": "year",
}

# label -> (column, altair format, kind for table formatting)
MEASURES = {
    "Net revenue": ("net", "$,.0f", "money"),
    "Margin %": ("margin_pct", ".1%", "pct"),
    "Margin $": ("margin", "$,.0f", "money"),
    "Effective discount %": ("discount_pct", ".1%", "pct"),
    "Orders": ("orders", ",d", "num"),
    "Units sold": ("units", ",d", "num"),
    "Customers": ("customers", ",d", "num"),
    "Average order value": ("avg_order", "$,.0f", "money"),
    "Refunds $": ("refund", "$,.0f", "money"),
    "Refund rate (% of revenue)": ("refund_rate", ".1%", "pct"),
    "Unpaid $": ("unpaid", "$,.0f", "money"),
    "Unpaid (% of revenue)": ("unpaid_pct", ".1%", "pct"),
    "Avg days to pay (paid orders)": ("days_to_pay", ".1f", "days"),
    "Avg days late (business, paid)": ("days_late", ".1f", "days"),
}
COL_LABEL = {v[0]: k for k, v in MEASURES.items()}


def col_cfg(label, kind):
    if kind == "money":
        return st.column_config.NumberColumn(label, format="dollar")
    if kind == "pct":
        return st.column_config.NumberColumn(label, format="percent")
    if kind == "days":
        return st.column_config.NumberColumn(label, format="%.1f")
    return st.column_config.NumberColumn(label, format="localized")


def prepare(orders):
    """Add the helper columns the analysis tabs rely on."""
    o = orders.copy()
    o["net_known"] = o["net"].where(o["cost"].notna(), 0.0)  # revenue on rows where margin is known
    o["unpaid_net"] = o["net"].where(o["payment_date"].isna(), 0.0)
    o["days_to_pay"] = (o["payment_date"] - o["order_date"]).dt.days
    late = (o["payment_date"] - o["due_date"]).dt.days
    o["days_late"] = late.where(o["terms_days"] > 0)  # consumers prepay: lateness doesn't apply
    o["month"] = o["order_date"].dt.to_period("M").astype(str)
    o["quarter"] = o["order_date"].dt.to_period("Q").astype(str)
    o["year"] = o["order_date"].dt.year.astype(str)
    return o


def aggregate(df, dims):
    g = (
        df.groupby(dims, observed=True)
        .agg(
            orders=("order_id", "count"),
            customers=("customer_id", "nunique"),
            units=("quantity", "sum"),
            gross=("gross", "sum"),
            net=("net", "sum"),
            margin=("margin", "sum"),
            net_known=("net_known", "sum"),
            refund=("refund", "sum"),
            unpaid=("unpaid_net", "sum"),
            days_to_pay=("days_to_pay", "mean"),
            days_late=("days_late", "mean"),
        )
        .reset_index()
    )
    g["margin_pct"] = g["margin"] / g["net_known"].where(g["net_known"] > 0)
    g["discount_pct"] = 1 - g["net"] / g["gross"]
    g["avg_order"] = g["net"] / g["orders"]
    g["refund_rate"] = g["refund"] / g["net"]
    g["unpaid_pct"] = g["unpaid"] / g["net"]
    return g


def _top_values(df, dim, n):
    return df.groupby(dim)["net"].sum().sort_values(ascending=False).head(n).index.tolist()


# ---------------------------------------------------------------------------
# ANALYZE – pivot-style explorer
# ---------------------------------------------------------------------------
def render_analyze(f):
    st.subheader("Slice the whole dataset any way you like")
    st.caption("Pick a measure, group it, optionally break it down by a second dimension. Sidebar filters apply.")
    if f.empty:
        st.warning("No orders match the sidebar filters.")
        return

    t = aggregate(f.assign(_all="all"), ["_all"]).iloc[0]
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("Orders", f"{int(t['orders']):,}")
    m2.metric("Customers", f"{int(t['customers']):,}")
    m3.metric("Net revenue", f"${t['net']/1e6:,.2f}M")
    m4.metric("Margin", f"{t['margin_pct']:.1%}")
    m5.metric("Refund rate", f"{t['refund_rate']:.1%}")
    m6.metric("Unpaid", f"${t['unpaid']/1e3:,.0f}K")

    c1, c2, c3 = st.columns(3)
    m_label = c1.selectbox("Measure", list(MEASURES), key="a_measure")
    d1_label = c2.selectbox("Group by", list(DIMS), index=0, key="a_d1")
    d2_label = c3.selectbox("Break down by (optional)", ["None"] + [k for k in DIMS if k != d1_label], key="a_d2")
    c4, c5, c6 = st.columns(3)
    topn = c4.slider("Show top N groups", 5, 50, 15, key="a_topn")
    lowest = c5.checkbox("Lowest first", key="a_low")
    min_orders = c6.number_input("Ignore groups with fewer orders than", 1, 500, 1, key="a_min")

    col, fmt, kind = MEASURES[m_label]
    d1, d2 = DIMS[d1_label], DIMS.get(d2_label)
    if d2 in TIME_COLS and d1 not in TIME_COLS:  # time always goes on the x axis
        d1, d2 = d2, d1
        d1_label, d2_label = d2_label, d1_label

    dims = [d1] + ([d2] if d2 else [])
    g = aggregate(f, dims)
    g = g[g["orders"] >= min_orders].dropna(subset=[col])
    if g.empty:
        st.info("Nothing to show with these settings (try lowering the minimum orders).")
        return

    st.markdown(f"**{m_label}** by **{d1_label}**" + (f" × **{d2_label}**" if d2 else ""))

    if not d2:
        if d1 in TIME_COLS:
            st.altair_chart(viz.line(g.sort_values(d1), d1, col, fmt), width="stretch", theme=None)
        else:
            shown = g.sort_values(col, ascending=lowest).head(topn)
            note = f" (top {topn} of {len(g)})" if len(g) > topn else ""
            st.caption(f"Orange = {'lowest' if lowest else 'highest'}{note}")
            st.altair_chart(
                viz.bar(shown, d1, col, [shown.iloc[0][d1]], fmt, d1_label, height=300, sort=shown[d1].tolist()),
                width="stretch",
                theme=None,
            )
    elif d1 in TIME_COLS and d2 not in TIME_COLS:
        keep = _top_values(f, d2, viz.MAX_SERIES)
        if f[d2].nunique() > viz.MAX_SERIES:
            st.caption(f"Showing the top {viz.MAX_SERIES} of {f[d2].nunique()} {d2_label.lower()} values by revenue.")
        shown = g[g[d2].isin(keep)].sort_values(d1)
        st.altair_chart(viz.line(shown, d1, col, fmt, color=d2), width="stretch", theme=None)
    else:
        rows = _top_values(f, d1, topn) if d1 not in TIME_COLS else sorted(f[d1].unique())
        cols_ = _top_values(f, d2, 12) if d2 not in TIME_COLS else sorted(f[d2].unique())
        shown = g[g[d1].isin(rows) & g[d2].isin(cols_)]
        if f[d1].nunique() > len(rows) or f[d2].nunique() > len(cols_):
            st.caption("Showing the largest groups by revenue; the table below has everything.")
        st.altair_chart(
            viz.heat(shown, d2, d1, col, fmt, x_order=cols_, y_order=rows, labels=len(shown) <= 120),
            width="stretch",
            theme=None,
        )

    # full table – every measure for the same grouping
    st.markdown("**All measures for this grouping**")
    table = g.sort_values(col, ascending=lowest)
    show_cols = dims + [v[0] for v in MEASURES.values()]
    cfg = {c: col_cfg(COL_LABEL[c], MEASURES[COL_LABEL[c]][2]) for c in show_cols if c in COL_LABEL}
    st.dataframe(table[show_cols], width="stretch", hide_index=True, column_config=cfg)
    st.download_button("Download this table (CSV)", table[show_cols].to_csv(index=False), file_name="analysis.csv", mime="text/csv")

    with st.expander("How each measure is calculated"):
        st.markdown(
            "- **Net revenue**: quantity × unit price × (1 − discount).\n"
            "- **Margin $ / %**: net revenue minus cost. Orders with a blank unit cost are left out of both the profit and the revenue it is divided by.\n"
            "- **Effective discount %**: 1 − net ÷ gross, weighted by order value (a $5,000 order counts more than a $50 one).\n"
            "- **Refunds / refund rate**: refund dollars from returns.csv, and as a share of net revenue.\n"
            "- **Unpaid $**: net revenue on orders with no payment date.\n"
            "- **Avg days to pay**: payment date − order date, paid orders only.\n"
            "- **Avg days late**: payment date − due date (order date + terms). Business customers only; negative = paid early."
        )


# ---------------------------------------------------------------------------
# CUSTOMERS
# ---------------------------------------------------------------------------
def render_customers(orders, customers):
    st.subheader("Every customer, ranked and searchable")
    orders_end = orders["order_date"].max()
    st.caption(f"'Days since last order' counts back from {orders_end:%b %d, %Y}, the last order date in the data.")

    by = orders.groupby("customer_id")
    cust = by.agg(
        orders=("order_id", "count"),
        net=("net", "sum"),
        margin=("margin", "sum"),
        net_known=("net_known", "sum"),
        last_order=("order_date", "max"),
        refund=("refund", "sum"),
        unpaid=("unpaid_net", "sum"),
        avg_days_late=("days_late", "mean"),
    )
    jan_sep = orders[orders["order_date"].dt.month <= 9]
    cust["net_2025"] = jan_sep[jan_sep["order_date"].dt.year == 2025].groupby("customer_id")["net"].sum()
    cust["net_2026"] = jan_sep[jan_sep["order_date"].dt.year == 2026].groupby("customer_id")["net"].sum()
    cust[["net_2025", "net_2026"]] = cust[["net_2025", "net_2026"]].fillna(0)
    cust["change"] = (cust["net_2026"] / cust["net_2025"].where(cust["net_2025"] > 0) - 1)
    cust["margin_pct"] = cust["margin"] / cust["net_known"].where(cust["net_known"] > 0)
    cust["days_since_last"] = (orders_end - cust["last_order"]).dt.days
    cust = cust.reset_index().merge(
        customers[["customer_id", "segment", "region", "payment_terms", "account_rep", "credit_limit", "signup_date"]],
        on="customer_id",
    )

    # --- concentration ---
    ranked = cust.sort_values("net", ascending=False).reset_index(drop=True)
    ranked["cum_share"] = ranked["net"].cumsum() / ranked["net"].sum()
    ranked["pct_customers"] = (ranked.index + 1) / len(ranked)
    top10 = ranked.loc[int(len(ranked) * 0.10) - 1, "cum_share"]
    top20 = ranked.loc[int(len(ranked) * 0.20) - 1, "cum_share"]
    biz = cust[cust["payment_terms"] != "Prepaid"]
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Customers with orders", f"{len(cust):,}")
    k2.metric("Top 10% of customers", f"{top10:.0%} of revenue")
    k3.metric("Top 20% of customers", f"{top20:.0%} of revenue")
    k4.metric("Business customers", f"{len(biz):,}", f"{biz['net'].sum()/cust['net'].sum():.0%} of revenue", delta_color="off")

    st.caption("How concentrated is revenue? (cumulative share of revenue, customers ranked biggest first)")
    pareto = (
        alt.Chart(ranked)
        .mark_area(line={"color": viz.LINE, "strokeWidth": 2.5}, color="#E4D6F5", opacity=0.8)
        .encode(
            x=alt.X("pct_customers:Q", title="Share of customers", axis=alt.Axis(format="%", grid=False, labelColor=viz.MUTED, domain=False)),
            y=alt.Y("cum_share:Q", title=None, axis=alt.Axis(format="%", gridColor=viz.GRID, labelColor=viz.MUTED, domain=False), scale=alt.Scale(domain=[0, 1])),
            tooltip=[alt.Tooltip("pct_customers:Q", format=".0%", title="Top % of customers"), alt.Tooltip("cum_share:Q", format=".0%", title="Share of revenue")],
        )
        .properties(height=220)
        .configure_view(strokeWidth=0)
        .configure(background="transparent")
    )
    st.altair_chart(pareto, width="stretch", theme=None)

    # --- filters + table ---
    st.markdown('<span class="step">CUSTOMER LIST</span>', unsafe_allow_html=True)
    f1, f2, f3 = st.columns(3)
    segs = sorted(cust["segment"].unique())
    seg_sel = f1.multiselect("Segment", segs, default=segs, key="c_seg")
    regs = sorted(cust["region"].unique())
    reg_sel = f2.multiselect("Customer region", regs, default=regs, key="c_reg")
    sort_by = f3.selectbox(
        "Sort by",
        ["Lifetime revenue", "Change vs 2025 (Jan–Sep)", "Days since last order", "Margin %", "Refunds $", "Unpaid $"],
        key="c_sort",
    )
    q1, q2, q3 = st.columns([1, 1, 1])
    quiet_on = q1.checkbox("Only show 'gone quiet' customers", key="c_quiet")
    min_orders = q2.slider("…who had at least this many orders", 1, 20, 4, key="c_minord")
    silent_days = q3.slider("…and nothing for at least this many days", 30, 365, 120, key="c_silent")

    view = cust[cust["segment"].isin(seg_sel) & cust["region"].isin(reg_sel)]
    if quiet_on:
        view = view[(view["orders"] >= min_orders) & (view["days_since_last"] >= silent_days)]
    sort_col, asc = {
        "Lifetime revenue": ("net", False),
        "Change vs 2025 (Jan–Sep)": ("change", True),
        "Days since last order": ("days_since_last", False),
        "Margin %": ("margin_pct", True),
        "Refunds $": ("refund", False),
        "Unpaid $": ("unpaid", False),
    }[sort_by]
    view = view.sort_values(sort_col, ascending=asc)

    st.caption(
        f"{len(view):,} customers · ${view['net'].sum():,.0f} lifetime revenue · "
        f"${view['net_2025'].sum():,.0f} of it in Jan–Sep 2025"
    )
    show = ["customer_id", "segment", "region", "payment_terms", "account_rep", "orders", "net", "margin_pct",
            "net_2025", "net_2026", "change", "last_order", "days_since_last", "refund", "unpaid", "avg_days_late"]
    st.dataframe(
        view[show],
        width="stretch",
        hide_index=True,
        column_config={
            "customer_id": "Customer", "segment": "Segment", "region": "Region", "payment_terms": "Terms",
            "account_rep": "Account rep",
            "orders": st.column_config.NumberColumn("Orders"),
            "net": st.column_config.NumberColumn("Lifetime revenue", format="dollar"),
            "margin_pct": st.column_config.NumberColumn("Margin %", format="percent"),
            "net_2025": st.column_config.NumberColumn("Jan–Sep 2025", format="dollar"),
            "net_2026": st.column_config.NumberColumn("Jan–Sep 2026", format="dollar"),
            "change": st.column_config.NumberColumn("Change", format="percent", help="Jan–Sep 2026 vs Jan–Sep 2025"),
            "last_order": st.column_config.DateColumn("Last order"),
            "days_since_last": st.column_config.NumberColumn("Days since last order"),
            "refund": st.column_config.NumberColumn("Refunds", format="dollar"),
            "unpaid": st.column_config.NumberColumn("Unpaid", format="dollar"),
            "avg_days_late": st.column_config.NumberColumn("Avg days late", format="%.1f"),
        },
    )
    st.download_button("Download this list (CSV)", view[show].to_csv(index=False), file_name="customers.csv", mime="text/csv")

    # --- customer 360 ---
    if len(view):
        st.markdown('<span class="step">ONE CUSTOMER IN DETAIL</span>', unsafe_allow_html=True)
        pick = st.selectbox("Customer", view["customer_id"].tolist(), key="c_pick")
        row = cust[cust["customer_id"] == pick].iloc[0]
        p1, p2, p3, p4, p5 = st.columns(5)
        p1.metric("Segment", f"{row['segment']}", f"{row['region']} · {row['payment_terms']}", delta_color="off")
        p2.metric("Lifetime revenue", f"${row['net']:,.0f}", f"{int(row['orders'])} orders", delta_color="off")
        p3.metric("Margin", "n/a" if pd.isna(row["margin_pct"]) else f"{row['margin_pct']:.0%}")
        p4.metric("Last order", f"{row['last_order']:%b %d, %Y}", f"{int(row['days_since_last'])} days ago", delta_color="off")
        p5.metric("Unpaid", f"${row['unpaid']:,.0f}", f"limit ${row['credit_limit']:,.0f}", delta_color="off")

        mine = orders[orders["customer_id"] == pick]
        months = pd.period_range(orders["order_date"].min(), orders["order_date"].max(), freq="M").astype(str)
        monthly = mine.groupby("month")["net"].sum().reindex(months, fill_value=0).rename_axis("month").reset_index()
        st.caption("Revenue by month")
        st.altair_chart(viz.line(monthly, "month", "net", "$,.0f", height=240), width="stretch", theme=None)
        st.dataframe(
            mine.sort_values("order_date", ascending=False)[
                ["order_id", "order_date", "product", "quantity", "discount", "net", "margin", "payment_date", "refund"]
            ],
            width="stretch",
            hide_index=True,
            column_config={
                "order_date": st.column_config.DateColumn("Ordered"),
                "payment_date": st.column_config.DateColumn("Paid"),
                "discount": st.column_config.NumberColumn("Discount", format="percent"),
                "net": st.column_config.NumberColumn("Net", format="dollar"),
                "margin": st.column_config.NumberColumn("Margin", format="dollar"),
                "refund": st.column_config.NumberColumn("Refunded", format="dollar"),
            },
        )


# ---------------------------------------------------------------------------
# RETURNS
# ---------------------------------------------------------------------------
RDIMS = {
    "Category": "category",
    "Product": "product",
    "Region": "region",
    "Sales channel": "sales_channel",
    "Sales rep": "sales_rep",
    "Customer segment": "segment",
    "Return reason": "reason",
    "Return month": "return_month",
}
ORDER_SIDE = {"category", "product", "region", "sales_channel", "sales_rep", "segment"}
RMEASURES = {  # label -> (column, fmt, needs order-side data)
    "Refund $": ("refund", "$,.0f", False),
    "Number of returns": ("returns", ",d", False),
    "Units returned": ("units_returned", ",d", False),
    "Avg days from order to return": ("days_to_return", ".1f", False),
    "Refund rate (% of revenue)": ("refund_rate", ".1%", True),
    "Return rate (% of orders)": ("return_rate", ".1%", True),
    "Units returned (% of units sold)": ("unit_return_rate", ".1%", True),
}


def render_returns(f, returns):
    st.subheader("Where do returns come from?")
    st.caption("Each return is linked to its order, so you can see returns by product, region, rep and more. Sidebar filters apply.")
    cols = ["order_id", "customer_id", "category", "product", "region", "sales_channel", "sales_rep", "segment", "order_date", "net", "quantity"]
    r = returns.merge(f[cols], on="order_id", how="inner")
    if r.empty:
        st.warning("No returns match the sidebar filters.")
        return
    r["return_month"] = r["return_date"].dt.to_period("M").astype(str)
    r["days_to_return"] = (r["return_date"] - r["order_date"]).dt.days

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Returns", f"{len(r):,}", f"{len(r)/len(f):.1%} of orders", delta_color="off")
    k2.metric("Refunded", f"${r['refund_amount'].sum()/1e3:,.0f}K", f"{r['refund_amount'].sum()/f['net'].sum():.1%} of revenue", delta_color="off")
    k3.metric("Units returned", f"{int(r['quantity_returned'].sum()):,}")
    k4.metric("Avg days to return", f"{r['days_to_return'].mean():.0f}")
    full = int((r["quantity_returned"] >= r["quantity"]).sum())
    k5.metric("Full-order returns", f"{full}", f"{full/len(r):.0%} of returns", delta_color="off")

    c1, c2, c3 = st.columns(3)
    d_label = c1.selectbox("Group returns by", list(RDIMS), key="r_dim")
    dim = RDIMS[d_label]
    allowed = [k for k, v in RMEASURES.items() if (not v[2]) or dim in ORDER_SIDE]
    m_label = c2.selectbox("Measure", allowed, key="r_measure")
    topn = c3.slider("Show top N", 5, 30, 12, key="r_topn")
    col, fmt, _ = RMEASURES[m_label]

    g = r.groupby(dim).agg(
        returns=("return_id", "count"),
        units_returned=("quantity_returned", "sum"),
        refund=("refund_amount", "sum"),
        days_to_return=("days_to_return", "mean"),
    )
    if dim in ORDER_SIDE:
        o = f.groupby(dim).agg(orders=("order_id", "count"), net=("net", "sum"), units=("quantity", "sum"))
        g = o.join(g).fillna({"returns": 0, "units_returned": 0, "refund": 0})
        g["refund_rate"] = g["refund"] / g["net"]
        g["return_rate"] = g["returns"] / g["orders"]
        g["unit_return_rate"] = g["units_returned"] / g["units"]
    g = g.reset_index().dropna(subset=[col])

    st.markdown(f"**{m_label}** by **{d_label}**")
    if dim == "return_month":
        st.altair_chart(viz.line(g.sort_values(dim), dim, col, fmt), width="stretch", theme=None)
    else:
        shown = g.sort_values(col, ascending=False).head(topn)
        st.altair_chart(
            viz.bar(shown, dim, col, [shown.iloc[0][dim]], fmt, d_label, height=300, sort=shown[dim].tolist()),
            width="stretch",
            theme=None,
        )

    # reason x something heatmap
    st.markdown('<span class="step">WHY ARE THEY RETURNED?</span>', unsafe_allow_html=True)
    h1, h2 = st.columns(2)
    split_label = h1.selectbox("Reasons broken down by", [k for k in RDIMS if k not in ("Return reason", "Return month")], key="r_split")
    heat_measure = h2.radio("Cell value", ["Number of returns", "Refund $"], horizontal=True, key="r_heat")
    split = RDIMS[split_label]
    hm = r.groupby(["reason", split]).agg(returns=("return_id", "count"), refund=("refund_amount", "sum")).reset_index()
    hval, hfmt = ("returns", ",d") if heat_measure == "Number of returns" else ("refund", "$,.0f")
    x_order = hm.groupby(split)[hval].sum().sort_values(ascending=False).index.tolist()
    y_order = r["reason"].value_counts().index.tolist()
    st.altair_chart(viz.heat(hm, split, "reason", hval, hfmt, x_order=x_order, y_order=y_order, labels=len(hm) <= 120), width="stretch", theme=None)

    # table + biggest refunds
    st.markdown("**All measures for this grouping**")
    show = g.sort_values(col, ascending=False)
    rcfg = {
        "refund": st.column_config.NumberColumn("Refund $", format="dollar"),
        "returns": st.column_config.NumberColumn("Returns", format="localized"),
        "units_returned": st.column_config.NumberColumn("Units returned", format="localized"),
        "days_to_return": st.column_config.NumberColumn("Avg days to return", format="%.1f"),
        "orders": st.column_config.NumberColumn("Orders", format="localized"),
        "net": st.column_config.NumberColumn("Net revenue", format="dollar"),
        "refund_rate": st.column_config.NumberColumn("Refund rate", format="percent"),
        "return_rate": st.column_config.NumberColumn("Return rate", format="percent"),
        "unit_return_rate": st.column_config.NumberColumn("Units returned %", format="percent"),
    }
    st.dataframe(show.drop(columns=["units"], errors="ignore"), width="stretch", hide_index=True, column_config=rcfg)

    st.markdown('<span class="step">LARGEST REFUNDS</span>', unsafe_allow_html=True)
    big = r.assign(share_of_order=r["refund_amount"] / r["net"]).sort_values("refund_amount", ascending=False).head(15)
    st.dataframe(
        big[["return_id", "order_id", "customer_id", "product", "region", "quantity", "quantity_returned", "reason", "days_to_return", "refund_amount", "share_of_order"]],
        width="stretch",
        hide_index=True,
        column_config={
            "quantity": st.column_config.NumberColumn("Qty ordered"),
            "quantity_returned": st.column_config.NumberColumn("Qty returned"),
            "days_to_return": st.column_config.NumberColumn("Days to return"),
            "refund_amount": st.column_config.NumberColumn("Refund", format="dollar"),
            "share_of_order": st.column_config.NumberColumn("% of order value", format="percent"),
        },
    )
