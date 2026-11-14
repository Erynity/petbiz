"""Insights: one collapsible section per finding. The chart, the numbers behind it, and what Chrome and Oak say about it."""

import streamlit as st

from chrome_oak.analysis import get_data, get_insight_charts, get_insights
from chrome_oak.ui.charts import chart_svg
from chrome_oak.ui.components import esc, html, page_head, table
from chrome_oak.ui.theme import inject_page_css


def _explain(x):
    """Chrome (the analyst) explains what happened; Oak (the advisor) says what to do."""
    return (f'<div class="say"><b class="who chrome">Chrome:</b> <b>{esc(x["title"])}.</b> {esc(x["what"])}</div>'
            f'<div class="say"><b class="who chrome">Chrome:</b> <b>Why it matters:</b> {esc(x["why"])}</div>'
            f'<div class="say oak"><b class="who oak">Oak:</b> {esc(x["todo"])}</div>')


def _numbers(ch, key):
    if st.toggle("Show the numbers", key=key):
        d = ch["data"].copy()
        if ch.get("sort"):
            d = d.sort_values(d.columns[0], ascending=False)
        d = d.reset_index()
        d.columns = [ch.get("x_title", d.columns[0]), d.columns[1]]
        hl = ch.get("highlight")
        table(d, highlight=hl if isinstance(hl, str) else None)


def render(ctx):
    inject_page_css(__file__)
    page_head("Insights", "The patterns, problems and opportunities we found. Open a finding to see the chart and what it means.")
    regions = sorted(get_data()["region"].dropna().astype(str).unique())
    region = st.selectbox("Show data for", ["All regions"] + regions)
    charts = get_insight_charts(region=None if region == "All regions" else region)
    ins = get_insights()

    for n, (x, chs) in enumerate(zip(ins, charts), start=1):
        with st.expander(f"{n}. {x['title']}", expanded=(n == 1)):
            left, right = st.columns([1, 1], gap="large")
            with left:
                for k, ch in enumerate(chs):
                    html(f'<div class="chartbox"><div class="ctitle">{esc(ch["title"])}</div>'
                         f'<div class="sub">{esc(ch.get("caption", ""))}</div>{chart_svg(ch)}</div>')
                    _numbers(ch, key=f"nums_{n}_{k}")
            right.markdown(_explain(x), unsafe_allow_html=True)
