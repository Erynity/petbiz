"""Overview: the problem we chose, the headline numbers, and a dashboard of charts."""

import streamlit as st

from chrome_oak.analysis import get_dashboard_charts, get_focus, get_kpis
from chrome_oak.config import ASOF
from chrome_oak.ui.charts import chart_svg, sparkline
from chrome_oak.ui.components import esc, html
from chrome_oak.ui.theme import DAISY, MUT, OAK, SPARK, inject_page_css


def chart_card(ch):
    wide = ch.get("wide")
    ch = {**ch, "width": 1100 if wide else 560, "height": 300}
    return (f'<div class="dcard{" wide" if wide else ""}"><div class="dtitle">{esc(ch["title"])}</div>'
            f'<div class="dsub">{esc(ch.get("caption", ""))}</div>{chart_svg(ch)}</div>')


def render(ctx):
    inject_page_css(__file__)
    html(
        '<div class="banner"><div class="ring"></div>'
        + SPARK.format(pos="top:22px;right:34%", s=22) + SPARK.format(pos="bottom:18px;left:48%", s=16)
        + DAISY.format(s=84)
        + "<div><h1>How's business?</h1>"
        "<p>Revenue is up, but cash is tight. Here's what's driving the gap.</p>"
        f'<div class="focus"><b>Our focus:</b> {esc(get_focus())}</div></div>'
        f'<span class="checked">✓ Data as of {ASOF:%b %d, %Y}</span>'
        '</div><div class="checker"></div>'
    )

    kpis = get_kpis()
    for i, (col, k) in enumerate(zip(st.columns(len(kpis)), kpis)):
        color = OAK if i % 2 == 0 else MUT
        col.markdown(
            f'<div class="card kpi"><div class="lab">{esc(k["label"])}</div><div class="val">{esc(k["value"])}</div>'
            f'<div class="del" style="color:{color}">{esc(k["delta"])}</div>{sparkline(k.get("trend"), color)}</div>',
            unsafe_allow_html=True,
        )

    html('<div class="dash">' + "".join(chart_card(ch) for ch in get_dashboard_charts()) + "</div>")
