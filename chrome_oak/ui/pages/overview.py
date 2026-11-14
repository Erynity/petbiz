"""Overview: the problem we chose and the four headline numbers, in detail. Charts live on the Insights page."""

import streamlit as st

from chrome_oak.analysis import get_focus, get_kpis
from chrome_oak.config import ASOF
from chrome_oak.ui.charts import trend_svg
from chrome_oak.ui.components import esc, html
from chrome_oak.ui.theme import DAISY, MUT, OAK, SPARK, inject_page_css


def kpi_card(k, color):
    details = "".join(f'<div class="krow"><span>{esc(a)}</span><b>{esc(b)}</b></div>' for a, b in k.get("details", []))
    return (f'<div class="kbig"><div class="klab">{esc(k["label"])}</div>'
            f'<div class="kval">{esc(k["value"])}</div><div class="kdel" style="color:{color}">{esc(k["delta"])}</div>'
            f'{trend_svg(k.get("trend"), k.get("trend_labels", ["", ""]), color, k.get("trend_fmt"))}'
            f'<div class="kdetails">{details}</div></div>')


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
    html('<div class="kgrid">' + "".join(kpi_card(k, OAK if i % 2 == 0 else MUT) for i, k in enumerate(kpis)) + "</div>")
    html('<p class="more">The charts behind these numbers are on the <a href="?page=insights" target="_self">Insights</a> page.</p>')
