"""Data list: every cleaned order, filterable and sortable, with a download."""

import streamlit as st

from chrome_oak.analysis import get_data
from chrome_oak.ui.components import page_head, sortable_table


def render(ctx):
    df = get_data().copy()
    page_head("Data list", f"Every cleaned order, {len(df):,} rows. Click a column title to sort; click again to flip.")
    c1, c2 = st.columns([2, 2])
    regions = sorted(df["region"].dropna().astype(str).unique())
    pick = c1.multiselect("Region", regions, placeholder="All regions")
    if pick:
        df = df[df["region"].astype(str).isin(pick)]
    q = c2.text_input("Search", placeholder="Customer, product, rep…")
    if q:
        df = df[df.astype(str).apply(lambda r: r.str.contains(q, case=False, regex=False)).any(axis=1)]
    sortable_table(df)
    st.download_button("Download these rows (CSV)", df.to_csv(index=False), "chrome_oak_orders.csv", "text/csv")
