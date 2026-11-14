"""Overview: the problem we chose, the headline numbers, the insights, and what needs attention."""

import streamlit as st

from chrome_oak.analysis import get_focus, get_insights, get_kpis
from chrome_oak.config import ASOF
from chrome_oak.ui.charts import sparkline
from chrome_oak.ui.components import esc, html, section
from chrome_oak.ui.theme import DAISY, MUT, OAK, SPARK, inject_page_css


def insight_card(n, x):
    return (f'<div class="card"><span class="pill">Insight {n}</span>'
            f'<div style="font-size:20px;font-weight:700;margin:10px 0 4px">{esc(x["title"])}</div>'
            f'<div class="lbl">What happened</div><p>{esc(x["what"])}</p>'
            f'<div class="lbl">Why it matters</div><p>{esc(x["why"])}</p>'
            f'<div class="lbl">What to do</div><p>{esc(x["todo"])}</p></div>')


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

    ins = get_insights()
    section("Key insights", "The short version. Open Insights for the charts behind each one.")
    for i, (col, x) in enumerate(zip(st.columns(len(ins)), ins), start=1):
        col.markdown(insight_card(i, x), unsafe_allow_html=True)

    open_issues = ctx["open_issues"]
    if open_issues:
        section("Needs attention", f"{len(open_issues)} alerts were triggered automatically. Oak has drafted the follow-ups.")
        for i in open_issues:
            html(f'<div class="card cta" style="padding:14px 20px"><div><span class="sev {i["severity"]}">{esc(i["severity"])}</span>'
                 f'<b>{len(i["rows"])} {esc(i["name"])}</b> · ${i["impact"]:,.0f} involved · goes to {esc(i["notify"])}</div>'
                 '<a href="?page=alerts" target="_self">Open alerts →</a></div>')
