"""Insights: one section per finding. The chart, the numbers behind it, and Chrome & Oak explaining it."""

import streamlit as st

from chrome_oak.analysis import get_charts, get_data, get_insights
from chrome_oak.ui.charts import bar_chart_svg
from chrome_oak.ui.components import esc, html, page_head, section, table
from chrome_oak.ui.mascots import mascot_svg
from chrome_oak.ui.theme import inject_page_css


def talk(who, mood, label, text):
    """A mascot with a speech bubble. who: "chrome" (analyst) or "oak" (advisor)."""
    side = "oak" if who == "oak" else "chrome"
    return (f'<div class="talk {side}"><span class="av">{mascot_svg(who, mood, 74)}</span>'
            f'<div class="bubble"><div class="k">{label}</div>{text}</div></div>')


def _explain(x):
    return ('<div class="duo-talk stack">'
            + talk("chrome", "worried", "Chrome · what it means",
                   f"<b>{esc(x['title'])}.</b> {esc(x['what'])}<br><br><b>Why it matters:</b> {esc(x['why'])}")
            + talk("oak", "happy", "Oak · what we can do", esc(x["todo"]))
            + "</div>")


def render(ctx):
    inject_page_css(__file__)
    page_head("Insights", "The patterns, problems and opportunities we found. One finding per section.")
    regions = sorted(get_data()["region"].dropna().astype(str).unique())
    region = st.selectbox("Show data for", ["All regions"] + regions)
    charts = get_charts(region=None if region == "All regions" else region)
    ins = get_insights()

    for n, ch in enumerate(charts):
        section(f'<span style="color:#8B5E3C">{n + 1}.</span> {esc(ch["title"])}', esc(ch.get("desc", ch.get("caption", ""))))
        left, right = st.columns([1, 1], gap="large")
        with left:
            html(f'<div class="chartbox"><div class="sub">{esc(ch.get("caption", ""))}</div>{bar_chart_svg(ch)}</div>')
            with st.expander("See the numbers"):
                d = ch["data"].copy()
                if ch.get("sort"):
                    d = d.sort_values(d.columns[0], ascending=False)
                d = d.reset_index()
                d.columns = [ch.get("x_title", d.columns[0]), d.columns[1]]
                hl = ch.get("highlight")
                table(d, highlight=hl if isinstance(hl, str) else None)
        if n < len(ins):
            right.markdown(_explain(ins[n]), unsafe_allow_html=True)

    for n, x in enumerate(ins[len(charts):], start=len(charts) + 1):  # insights without a chart
        section(f'<span style="color:#8B5E3C">{n}.</span> {esc(x["title"])}')
        html(_explain(x).replace("duo-talk stack", "duo-talk"))
