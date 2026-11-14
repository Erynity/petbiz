"""Chrome & Oak – business health check, working copy (Hack2theFuture, Business track, Option B).

Same look as app.py (welcome page + the dashboard_view.py design), but every part works:

  Welcome    -> "Open the dashboard" button (copied from app.py)
  Dashboard  -> banner, KPIs, charts, insights, data prep        (DATA, DETECT, DECIDE)
                Alerts inbox: three detections, each with its own slider (Simulation bonus),
                drafted messages, Send / Dismiss, and an action log you can export   (ACT)

All numbers and all detection rules come from analysis.py. The page's JavaScript only
switches between results that Python already computed for every slider position.

Run with:  streamlit run app_copy.py
"""

import html as _html
import json
from urllib.parse import quote

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from analysis import (ASOF, detect_discounts, detect_overdue, detect_returns, get_charts, get_focus,
                      get_insights, get_kpis, get_prep_steps, load_data)
from dashboard_view import BG, CARD, I, SLAB, bar_chart_svg, esc, sparkline
from dashboard_view import CSS as DV_CSS
from dashboard_view import DAISY as DV_DAISY
from dashboard_view import SPARK as DV_SPARK
from pet import MASCOT_CSS, mascot_svg, mascots_pair, show_pets

st.set_page_config(page_title="Chrome & Oak · Health Check", page_icon="💼", layout="wide")


# ---------------------------------------------------------------------------
# 2. Theme (Chrome-led: light grey, silver banner, oak highlights)
# ---------------------------------------------------------------------------
INK, MUT, LINE, OAK, OAKD = "#2A2420", "#565B62", "#DDE0E4", "#8B5E3C", "#5E3B22"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Alfa+Slab+One&family=Nunito:wght@400;600;700;800&display=swap');
.stApp{background:#F4F5F7}
html, body, .stMarkdown, p, li, label, button, input{font-family:'Nunito',sans-serif;color:#2A2420}
h1, h2, h3{font-family:'Alfa Slab One',serif !important;font-weight:400 !important;color:#2A2420 !important}
.block-container{padding-top:1.4rem;padding-bottom:4rem;max-width:1180px}
header[data-testid="stHeader"]{background:transparent}

/* sidebar = brushed chrome */
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#F1F3F5 0%,#D9DCE0 55%,#C9CDD2 100%);border-right:1px solid #B9BFC6}
section[data-testid="stSidebar"] *{color:#2A2420}
.logo{display:flex;align-items:center;gap:8px;font-family:'Alfa Slab One',serif;font-size:21px;color:#5E3B22 !important;margin:4px 0 18px}
.navlbl{font-size:11px;font-weight:800;letter-spacing:1.5px;text-transform:uppercase;color:#565B62 !important;margin:4px 0 8px 14px}
.simnote{font-size:13px;color:#565B62 !important;line-height:1.45;padding:0 6px}
a.navi{text-decoration:none}
a.navi:hover{background:rgba(255,255,255,.6)}
.navi{display:flex;align-items:center;gap:10px;padding:10px 14px;border-radius:999px;font-weight:800;font-size:15px;margin-bottom:4px}
.navi.on{background:#FFFFFF;color:#5E3B22 !important;box-shadow:0 2px 6px rgba(42,36,32,.12)}
.navi .badge{margin-left:auto;background:#8B5E3C;color:#FFFFFF !important;font-size:12px;padding:1px 9px;border-radius:999px}
.duty{background:#FFFFFF;border:3px solid #E6CDAE;border-radius:24px;padding:14px;text-align:center;margin-top:24px}
.duty b{display:block;font-size:14px;margin-top:4px}
.duty span{font-size:13px;color:#565B62}

/* banner */
.banner{position:relative;overflow:hidden;background:#C9CDD2;border-radius:28px 28px 0 0;padding:30px 32px;display:flex;justify-content:space-between;align-items:center;gap:20px;flex-wrap:wrap}
.banner .ring{position:absolute;width:520px;height:520px;border-radius:50%;border:40px solid #D9DCE0;top:-330px;right:-100px}
.banner h1{position:relative;margin:0;font-size:44px;line-height:1.05;color:#5E3B22 !important;text-shadow:0 3px 0 #FFFFFF}
.banner p{position:relative;margin:8px 0 0;font-size:17px;font-weight:700}
.focus{position:relative;display:inline-block;background:#FFFFFF;border-radius:14px;padding:8px 14px;font-size:15px;font-weight:600;margin-top:10px}
.focus b{color:#8B5E3C}
.checked{position:relative;background:#FFFFFF;border-radius:999px;padding:8px 14px;font-size:14px;font-weight:800;color:#5E3B22;margin-right:90px}
.checker{height:26px;border-radius:0 0 28px 28px;margin-bottom:18px;background-image:repeating-conic-gradient(#DDE0E4 0 25%, #FFFFFF 0 50%);background-size:26px 26px}
.daisy{position:absolute;top:-14px;right:18px;animation:spin 14s linear infinite}
.sparkle{position:absolute;animation:twinkle 2.4s ease-in-out infinite}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes twinkle{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.35;transform:scale(.75)}}

/* cards */
.card{background:#FFFFFF;border:3px solid #DDE0E4;border-radius:24px;padding:20px 22px;margin-bottom:16px}
.kpi .lab{font-size:14px;font-weight:600;color:#565B62}
.kpi .val{font-size:28px;font-weight:600;letter-spacing:-.3px;white-space:nowrap;margin-top:4px}
.kpi .del{font-size:13px;font-weight:600;color:#8B5E3C;white-space:nowrap}
.ttl{font-size:18px;font-weight:800}
.sub{font-size:14px;color:#565B62;margin-bottom:6px}
.slab{font-family:'Alfa Slab One',serif;font-size:22px}
.pill{display:inline-block;font-size:12px;font-weight:800;letter-spacing:1px;text-transform:uppercase;color:#FFFFFF;background:#8B5E3C;border-radius:999px;padding:3px 12px}
.lbl{font-size:12px;font-weight:800;color:#8B5E3C;text-transform:uppercase;letter-spacing:1px;margin-top:8px}
.card p{margin:2px 0 6px;font-size:15px;line-height:1.5;color:#565B62}
.prep{display:grid;grid-template-columns:1fr auto;gap:12px;padding:10px 0;border-top:2px solid #EEF0F2}
.prep .rows{font-size:13px;font-weight:700;color:#565B62;background:#EEF0F2;border-radius:999px;padding:3px 10px;white-space:nowrap;align-self:start}

/* alerts: 3-step story */
.sev{font-size:13px;font-weight:800;border-radius:999px;padding:4px 12px;margin-right:8px}
.sev.High{color:#8B5E3C;background:#F5E9DA}.sev.Medium{color:#5E3B22;background:#EFE4D6}.sev.Low{color:#565B62;background:#EEF0F2}
.step3{background:#FFFFFF;border:3px solid #DDE0E4;border-radius:22px;padding:14px 16px;height:100%}
.step3.oak{border-color:#E6CDAE}
.step3 .who{display:flex;align-items:center;gap:10px}
.step3 .k{font-size:12px;font-weight:800;color:#565B62;text-transform:uppercase;letter-spacing:1px}
.step3.oak .k{color:#8B5E3C}
.step3 .h{font-size:16px;font-weight:800}
.step3 .done{font-size:15px;margin:4px 0}
[data-testid="stExpander"]{background:#FFFFFF;border:3px solid #DDE0E4 !important;border-radius:22px !important}
[data-testid="stExpander"] summary p{font-size:16px;font-weight:800}

/* buttons */
.stButton button, .stDownloadButton button{background:#8B5E3C;color:#FFFFFF;border:none;border-radius:999px;font-weight:800;min-height:46px;padding:0 22px;box-shadow:0 3px 0 #5E3B22}
.stButton button p, .stDownloadButton button p{color:#FFFFFF !important;font-weight:800}
.stButton button:hover{background:#9A6943;color:#FFFFFF}
.stButton button[kind="secondary"].ghost{background:#FFFFFF}

/* welcome */
.hero{position:relative;overflow:hidden;background:#C9CDD2;border-radius:28px 28px 0 0;padding:44px 40px;display:grid;grid-template-columns:1fr auto;gap:24px;align-items:center}
.hero .ring{position:absolute;width:700px;height:700px;border-radius:50%;border:50px solid #D9DCE0;top:-420px;right:-160px}
.hero .hi{position:relative;display:inline-block;background:#FFFFFF;border-radius:18px 18px 18px 4px;padding:10px 16px;font-size:16px;font-weight:700}
.hero h1{position:relative;margin:18px 0 10px;font-size:52px;line-height:1.05;color:#5E3B22 !important;text-shadow:0 3px 0 #FFFFFF}
.hero p{position:relative;margin:0;font-size:18px;font-weight:600;max-width:480px}
.stage{position:relative;background:radial-gradient(circle at 50% 40%,#FFFFFF,#EEF0F2 75%);border:5px solid #FFFFFF;border-radius:32px;padding:18px 18px 6px}
.topbar{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap;background:linear-gradient(180deg,#F1F3F5,#D9DCE0);border:1px solid #B9BFC6;border-radius:999px;padding:8px 8px 8px 20px;margin-bottom:22px}
.topbar .t{font-size:14px;font-weight:700;color:#565B62;background:#FFFFFF;border-radius:999px;padding:8px 14px}
.tbl{background:#FFFFFF;border:3px solid #DDE0E4;border-radius:18px;overflow:hidden;overflow-x:auto;margin:14px 0 6px}
.tbl table{width:100%;border-collapse:collapse;font-size:15px}
.tbl th{text-align:left;background:#F4F5F7;color:#565B62;font-size:12px;font-weight:800;text-transform:uppercase;letter-spacing:1px;padding:10px 14px}
.tbl td{padding:11px 14px;border-top:2px solid #EEF0F2;color:#2A2420}
.tbl tr:nth-child(even) td{background:#FBF8F4}
[data-testid="stElementToolbar"]{display:none !important}
.vega-embed details,.vega-actions{display:none !important}
[data-testid="stVegaLiteChart"]{background:#FFFFFF;border:3px solid #DDE0E4;border-radius:24px;overflow:hidden}
.tag{display:inline-block;background:#FFFFFF;border:2px dashed #B9BFC6;border-radius:999px;padding:5px 14px;font-weight:700;font-size:13px;color:#565B62;margin-bottom:12px}
</style>
"""
st.markdown(CSS + MASCOT_CSS, unsafe_allow_html=True)

LEAF = ('<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#8B5E3C" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M11 20A7 7 0 0 1 4 13c0-6 7-10 16-10-1 9-5 16-9 17z"/>'
        '<path d="M4 21c4-6 8-9 12-11"/></svg>')
DAISY = ('<svg class="daisy" width="{s}" height="{s}" viewBox="0 0 100 100" aria-hidden="true"><g fill="#FFFFFF">'
         '<ellipse cx="50" cy="20" rx="11" ry="20"/><ellipse cx="50" cy="80" rx="11" ry="20"/><ellipse cx="20" cy="50" rx="20" ry="11"/>'
         '<ellipse cx="80" cy="50" rx="20" ry="11"/><ellipse cx="29" cy="29" rx="11" ry="20" transform="rotate(-45 29 29)"/>'
         '<ellipse cx="71" cy="71" rx="11" ry="20" transform="rotate(-45 71 71)"/><ellipse cx="71" cy="29" rx="11" ry="20" transform="rotate(45 71 29)"/>'
         '<ellipse cx="29" cy="71" rx="11" ry="20" transform="rotate(45 29 71)"/></g><circle cx="50" cy="50" r="14" fill="#D4A84A"/></svg>')
SPARK = ('<svg class="sparkle" style="{pos}" width="{s}" height="{s}" viewBox="0 0 24 24" aria-hidden="true">'
         '<path d="M12 0 L14 10 L24 12 L14 14 L12 24 L10 14 L0 12 L10 10 Z" fill="#FFFFFF"/></svg>')

ICONS = {
    "home": '<path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10"/>',
    "chart": '<path d="M4 20V10"/><path d="M10 20V4"/><path d="M16 20v-7"/><path d="M22 20H2"/>',
    "data": '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v6c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 11v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/>',
    "bulb": '<path d="M9 18h6"/><path d="M10 22h4"/><path d="M12 2a7 7 0 0 0-4 12.7V16h8v-1.3A7 7 0 0 0 12 2z"/>',
    "bell": '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10 21a2 2 0 0 0 4 0"/>',
    "log": '<path d="M8 6h13M8 12h13M8 18h13"/><path d="M3 6h.01M3 12h.01M3 18h.01"/>',
}


def icon(name, color="#565B62", size=18):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>')



def html(s):
    st.markdown(s, unsafe_allow_html=True)


def table(df):
    """Plain, styled HTML table (no interactive grid)."""
    head = "".join(f"<th>{c}</th>" for c in df.columns)
    body = "".join("<tr>" + "".join(f"<td>{v}</td>" for v in row) + "</tr>" for row in df.astype(str).values)
    html(f'<div class="tbl"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>')


def rerun():
    (getattr(st, "rerun", None) or st.experimental_rerun)()


# ---------------------------------------------------------------------------
# 3. Welcome page
# ---------------------------------------------------------------------------
if "started" not in st.session_state:
    st.session_state.started = False
_page = st.query_params.get("page") if hasattr(st, "query_params") else None
if _page == "dashboard":
    st.session_state.started = True
elif _page == "welcome":
    st.session_state.started = False
    st.query_params.clear()

if not st.session_state.started:
    html(
        f'<div class="topbar"><span class="logo" style="margin:0">{LEAF} Chrome &amp; Oak</span>'
        '<span class="t">Office Supply · Business health check</span></div>'
        '<div class="hero"><div class="ring"></div>'
        + SPARK.format(pos="top:26px;left:46%", s=26) + SPARK.format(pos="bottom:30px;left:6%", s=18)
        + DAISY.format(s=96)
        + '<div><div class="hi">Hi! We\'re Chrome &amp; Oak. Let\'s check on the business.</div>'
        "<h1>Revenue is up.<br>So why is cash tight?</h1>"
        "<p>We dig through the orders, returns and customers, then act on what needs attention.</p></div>"
        f'<div class="stage">{mascots_pair("happy", "happy", 150)}</div>'
        '</div><div class="checker"></div>'
    )
    steps = [
        ("Chrome detects", "Reads every order, return and customer to spot what's wrong."),
        ("Oak decides", "Picks the problem worth fixing first, with the numbers to back it."),
        ("Oak acts", "Pauses risky orders, drafts reminders and tells the right person."),
    ]
    for col, (t, d) in zip(st.columns(3), steps):
        col.markdown(f'<div class="card"><div class="ttl">{t}</div><p>{d}</p></div>', unsafe_allow_html=True)
    if st.button("Open the dashboard  →"):
        st.session_state.started = True
        st.query_params["page"] = "dashboard"
        rerun()
    st.stop()


# ---------------------------------------------------------------------------
# 4. Dashboard: one HTML page in the dashboard_view.py design, with working tools
# ---------------------------------------------------------------------------
# Every alert is computed in Python (analysis.py) for every slider position,
# then embedded in the page. The page's JavaScript only switches between those
# precomputed results, so the detection logic stays in analysis.py.

ALERT_SETTINGS = {
    # id: slider settings, and the detection it runs for each slider value
    "overdue": dict(label="Flag after", unit="days late", lo=0, hi=90, step=5, default=30),
    "discount": dict(label="Discount cap", unit="%", lo=5, hi=40, step=1, default=15),
    "returns": dict(label="Flag refunds above", unit="% of revenue", lo=2, hi=15, step=1, default=5),
}
PRETTY = {"days_late": "Oldest (days late)", "owes": "Past due", "rep": "Account rep", "credit used": "Credit used"}
SEV = {"High": (OAK, "#F5E9DA"), "Medium": (OAKD, "#EFE4D6"), "Low": (MUT, "#EEF0F2")}


def run_detection(alert_id, value, orders, returns):
    if alert_id == "overdue":
        return detect_overdue(orders, value)
    if alert_id == "discount":
        return detect_discounts(orders, value / 100)
    return detect_returns(orders, returns, value / 100)


def table_html(df):
    df = df.rename(columns=PRETTY)
    head = "".join(f"<th>{esc(c)}</th>" for c in df.columns)
    body = "".join("<tr>" + "".join(f"<td>{esc(v)}</td>" for v in row) + "</tr>" for row in df.astype(str).values)
    return f'<div class="tbl"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>'


@st.cache_data(show_spinner="Chrome is reading every order…")
def build_alerts():
    _, orders, returns, *_ = load_data()
    alerts = []
    for alert_id, cfg in ALERT_SETTINGS.items():
        results = {}
        for v in range(cfg["lo"], cfg["hi"] + 1, cfg["step"]):
            r = run_detection(alert_id, v, orders, returns)
            results[str(v)] = {
                "count": len(r["rows"]),
                "name": r["name"], "severity": r["severity"], "found": r["found"], "rule": r["rule"],
                "actions": r["actions"], "notify": r["notify"], "impact": float(r["impact"]),
                "table": table_html(r["rows"]) if len(r["rows"]) else "",
                "drafts": r["drafts"].fillna("").to_dict("records"),
            }
        alerts.append({"id": alert_id, **cfg, "results": results})
    return alerts


def kpi_cards(kpis):
    return "".join(
        f'<div style="{CARD}; padding: 20px 22px 14px"><div style="font-size: 14px; font-weight: 600; color: {MUT}">{esc(k["label"])}</div>'
        f'<div style="font-size: 28px; font-weight: 600; letter-spacing: -0.3px; margin-top: 4px; white-space: nowrap; line-height: 1.15">{esc(k["value"])}</div>'
        f'<div style="font-size: 13px; font-weight: 600; color: {OAK if i % 2 == 0 else MUT}; margin: 2px 0 0; white-space: nowrap">{esc(k["delta"])}</div>'
        f'{sparkline(k.get("trend"), OAK if i % 2 == 0 else MUT)}</div>'
        for i, k in enumerate(kpis)
    )


def chart_cards(charts):
    return "".join(
        f'<div style="{CARD}; padding: 20px 22px"><div style="font-size: 18px; font-weight: 800">{esc(c["title"])}</div>'
        f'<div style="font-size: 14px; color: {MUT}; margin-bottom: 8px">{esc(c.get("caption", ""))}</div>{bar_chart_svg(c)}</div>'
        for c in charts
    )


def insight_cards(insights):
    return "".join(
        f'<div style="{CARD}; padding: 22px"><div style="display: inline-block; font-size: 12px; font-weight: 800; letter-spacing: 1px; text-transform: uppercase; color: #FFFFFF; background: {OAK}; border-radius: 999px; padding: 3px 12px">Insight {n}</div>'
        f'<div style="font-size: 20px; font-weight: 700; margin: 10px 0 8px">{esc(x["title"])}</div>'
        + "".join(f'<div style="font-size: 12px; font-weight: 800; color: {OAK}; text-transform: uppercase; letter-spacing: 1px">{lbl}</div>'
                  f'<p style="margin: 2px 0 8px; font-size: 15px; line-height: 1.5; color: {MUT}">{esc(x[key])}</p>'
                  for lbl, key in (("What happened", "what"), ("Why it matters", "why"), ("What to do", "todo")))
        + "</div>"
        for n, x in enumerate(insights, start=1)
    )


def prep_rows(prep):
    return "".join(
        f'<div style="display: grid; grid-template-columns: 28px 1fr auto; gap: 12px; align-items: start; padding: 12px 0; border-top: 2px solid #EEF0F2">'
        f'<span style="width: 28px; height: 28px; border-radius: 50%; background: #F5E9DA; display: flex; align-items: center; justify-content: center">{I("check", 14, OAK, 3)}</span>'
        f'<div><div style="font-size: 15px; font-weight: 800">{esc(p["what"])}</div><div style="font-size: 14px; color: {MUT}; margin-top: 2px"><b style="color: {OAK}">Why:</b> {esc(p["why"])}</div></div>'
        f'<span style="font-size: 13px; font-weight: 700; color: {MUT}; background: #EEF0F2; border-radius: 999px; padding: 3px 10px; white-space: nowrap">{esc(p["rows"])}</span></div>'
        for p in prep
    )


def alert_block(a):
    """The shell of one alert. The JavaScript fills in the parts that depend on the slider."""
    sid = a["id"]
    step3_card = f'<div style="background: #FFFFFF; border: 3px solid {LINE}; border-radius: 22px; padding: 16px; display: flex; flex-direction: column; gap: 10px" data-f="step3"></div>'
    return f'''<div class="issue" id="iss-{sid}" data-id="{sid}">
<div class="ihead">
<span class="sev" data-f="sev"></span>
<div><div style="font-size: 16px; font-weight: 800"><span data-f="count"></span> <span data-f="name"></span></div>
<div style="font-size: 14px; color: {MUT}; margin-top: 2px" data-f="sub"></div></div>
<button class="openbtn" data-act="toggle">Open</button></div>
<div class="ibody" hidden>
<div style="background: #FBF8F4; border-top: 2px solid #EEF0F2; padding: 22px">
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 14px">
<div style="background: #FFFFFF; border: 3px solid {LINE}; border-radius: 22px; padding: 16px; display: flex; flex-direction: column; gap: 8px">
<div style="display: flex; align-items: center; gap: 10px"><span style="flex: none; width: 58px">{mascot_svg("chrome", "worried", 58)}</span><div><div class="k">Step 1 · Chrome noticed</div><div style="font-size: 16px; font-weight: 800" data-f="found"></div></div></div>
<p style="margin: 0; font-size: 15px; line-height: 1.5; color: {MUT}">Rule: <span data-f="rule"></span>.</p></div>
<div style="background: #FFFFFF; border: 3px solid #E6CDAE; border-radius: 22px; padding: 16px; display: flex; flex-direction: column; gap: 8px">
<div style="display: flex; align-items: center; gap: 10px"><span style="flex: none; width: 58px">{mascot_svg("oak", "happy", 58)}</span><div><div class="k" style="color: {OAK}">Step 2 · Oak prepared</div><div style="font-size: 16px; font-weight: 800" data-f="nactions"></div></div></div>
<div style="display: flex; flex-direction: column; gap: 6px; font-size: 15px" data-f="actions"></div></div>
{step3_card}
</div>
<div class="simbar">
<span style="font-size: 14px; font-weight: 800; white-space: nowrap; display: inline-flex; align-items: center; gap: 6px">{I("gear", 15, OAK)} {esc(a["label"])}</span>
<input type="range" min="{a["lo"]}" max="{a["hi"]}" step="{a["step"]}" value="{a["default"]}" aria-label="{esc(a["label"])}" data-act="slide" style="flex: 1; min-width: 160px">
<span style="font-size: 15px; font-weight: 800; color: {OAKD}; white-space: nowrap" data-f="val"></span>
</div>
<div class="impact" data-f="impact"></div>
</div>
<div data-f="table"></div>
<div style="display: flex; gap: 10px; flex-wrap: wrap; padding: 0 22px 18px">
<button class="btn ghost" data-act="drafts">{I("send", 15, INK)} <span data-f="draftlbl"></span></button>
<button class="btn ghost" data-act="dldrafts">{I("down", 15, INK)} Download drafts (CSV)</button>
</div>
<div data-f="drafts" hidden style="padding: 0 22px 18px; display: grid; gap: 10px"></div>
</div>
<div class="idis" hidden>Dismissed for this session. <button class="linkbtn" data-act="restore">Restore</button></div>
</div>'''


EXTRA_CSS = """
.issue{border-top:2px solid #EEF0F2}
.ihead{display:grid;grid-template-columns:auto 1fr auto;gap:14px;align-items:center;padding:14px 22px}
.sev{font-size:13px;font-weight:800;border-radius:999px;padding:4px 12px}
.openbtn{font-family:inherit;font-size:14px;font-weight:800;color:#5E3B22;background:#FFFFFF;border:2px solid #E6CDAE;border-radius:999px;padding:8px 16px;cursor:pointer}
.openbtn:hover{background:#FBF8F4}
.k{font-size:12px;font-weight:800;color:#565B62;text-transform:uppercase;letter-spacing:1px}
.simbar{margin-top:14px;display:flex;align-items:center;gap:14px;flex-wrap:wrap;background:#FFFFFF;border:3px solid #DDE0E4;border-radius:999px;padding:10px 20px}
.impact{margin:10px 6px 0;font-size:14px;color:#565B62}
.impact b{color:#5E3B22}
.idis{padding:12px 22px;font-size:14px;color:#565B62;background:#F4F5F7}
.linkbtn{font-family:inherit;font-size:14px;font-weight:800;color:#5E3B22;background:none;border:none;text-decoration:underline;cursor:pointer;padding:0}
.draft{background:#FFFFFF;border:3px solid #DDE0E4;border-radius:18px;padding:14px 16px;font-size:14px;line-height:1.5}
.draft .to{font-size:12px;font-weight:800;color:#565B62;text-transform:uppercase;letter-spacing:1px}
.draft .subj{font-size:15px;font-weight:800;margin:2px 0 6px}
.draft .note{margin-top:8px;font-size:13px;font-weight:800;color:#8B5E3C}
.sent{display:flex;align-items:center;gap:8px;font-size:15px;font-weight:800;color:#5E3B22}
.empty td{color:#565B62;font-style:italic}
details.removed summary{cursor:pointer;font-size:15px;font-weight:800;padding:12px 0;border-top:2px solid #EEF0F2}
details.removed .tbl{margin:0 0 14px}
mark{background:#F5E9DA;color:inherit;border-radius:4px}
.page{display:flex;flex-direction:column;gap:18px}
.page[hidden]{display:none}
.ptitle{font-family:'Alfa Slab One',serif;font-size:30px;color:#5E3B22}
.card-cta{display:flex;justify-content:space-between;align-items:center;gap:14px;flex-wrap:wrap;background:#FFFFFF;border:3px solid #E6CDAE;border-radius:24px;padding:18px 22px}
"""

JS = r"""
<script>
const ALERTS = __ALERTS__;
const SEV = __SEV__;
const KEY = 'chrome_oak_action_log';
const state = {value: {}, sent: {}, dismissed: {}, open: {}};
let log = [];
try { log = JSON.parse(localStorage.getItem(KEY) || '[]'); } catch (e) { log = []; }
const saveLog = () => { try { localStorage.setItem(KEY, JSON.stringify(log)); } catch (e) {} };

const money = x => '$' + Math.round(x).toLocaleString('en-US');
const escH = s => String(s).replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
const now = () => new Date().toLocaleString('en-CA', {hour12: false}).replace(',', '');
const toast = msg => { const t = document.getElementById('toast'); t.textContent = msg; t.classList.add('show'); setTimeout(() => t.classList.remove('show'), 2200); };
const byId = id => ALERTS.find(a => a.id === id);
const cur = id => byId(id).results[String(state.value[id])];
const f = (el, name) => el.querySelector('[data-f="' + name + '"]');
const CHECK = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#8B5E3C" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20 6L9 17l-5-5"/></svg>';

function csv(rows) {
  if (!rows.length) return '';
  const cols = Object.keys(rows[0]);
  const q = v => '"' + String(v ?? '').replace(/"/g, '""') + '"';
  return [cols.map(q).join(',')].concat(rows.map(r => cols.map(c => q(r[c])).join(','))).join('\n');
}
function download(name, text) {
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([text], {type: 'text/csv'}));
  a.download = name; document.body.appendChild(a); a.click(); a.remove();
}

function renderIssue(id) {
  const a = byId(id), r = cur(id), el = document.getElementById('iss-' + id);
  const [c, bg] = SEV[r.severity] || ['#565B62', '#EEF0F2'];
  const sev = f(el, 'sev'); sev.textContent = r.severity; sev.style.color = c; sev.style.background = bg;
  f(el, 'count').textContent = r.count;
  f(el, 'name').textContent = r.name;
  f(el, 'sub').textContent = r.count ? r.actions.slice(0, 2).join(' · ') : 'All clear at this setting';
  f(el, 'found').textContent = r.found;
  f(el, 'rule').textContent = r.rule;
  f(el, 'nactions').textContent = r.actions.length + ' things ready';
  f(el, 'actions').innerHTML = r.actions.map(x => '<span style="display:flex;align-items:center;gap:8px">' + CHECK + escH(x) + '</span>').join('');
  f(el, 'val').textContent = state.value[id] + (a.unit.startsWith('%') ? '' : ' ') + a.unit;
  f(el, 'impact').innerHTML = 'At this setting: <b>' + r.count + '</b> flagged · <b>' + money(r.impact) + '</b> involved';
  f(el, 'table').innerHTML = r.table || '<div class="tbl"><table><tbody><tr class="empty"><td>Nothing flagged at this setting.</td></tr></tbody></table></div>';
  f(el, 'draftlbl').textContent = 'Preview ' + r.drafts.length + ' drafted message' + (r.drafts.length === 1 ? '' : 's');
  const sentAt = state.sent[id + ':' + state.value[id]];
  const s3 = f(el, 'step3');
  if (!r.count) {
    s3.innerHTML = '<div class="k">Step 3 · Your turn</div><div style="font-size:16px;font-weight:800">Nothing to send</div>';
  } else if (sentAt) {
    s3.innerHTML = '<div class="k">Step 3 · Done</div><div class="sent">' + CHECK + 'Sent to ' + escH(r.notify) + '</div><div style="font-size:14px;color:#565B62">' + escH(sentAt) + '</div>';
  } else {
    s3.innerHTML = '<div class="k">Step 3 · Your turn</div><div style="font-size:16px;font-weight:800">Send to ' + escH(r.notify) + '?</div>'
      + '<button class="btn oak" data-act="send">Send ' + r.drafts.length + ' drafted message' + (r.drafts.length === 1 ? '' : 's') + '</button>'
      + '<button class="btn ghost" data-act="dismiss">Not a problem, dismiss</button>';
  }
  const drafts = f(el, 'drafts');
  drafts.innerHTML = r.drafts.map(d => '<div class="draft"><div class="to">To: ' + escH(d.to) + '</div><div class="subj">' + escH(d.subject) + '</div>'
    + escH(d.message) + (d['internal note'] ? '<div class="note">Internal: ' + escH(d['internal note']) + '</div>' : '') + '</div>').join('');
  const dis = !!state.dismissed[id];
  el.querySelector('.ihead').hidden = dis;
  el.querySelector('.idis').hidden = !dis;
  el.querySelector('.ibody').hidden = dis || !state.open[id];
  el.querySelector('[data-act="toggle"]').textContent = state.open[id] ? 'Close' : (r.count ? 'Open' : 'View');
  applySearch();
}

function renderBadge() {
  const n = ALERTS.filter(a => !state.dismissed[a.id] && cur(a.id).count > 0).length;
  document.querySelectorAll('[data-badge]').forEach(b => b.textContent = n);
}

function renderLog() {
  const body = document.getElementById('logbody');
  body.innerHTML = log.length
    ? log.slice().reverse().map(l => '<tr><td>' + escH(l.time) + '</td><td>' + escH(l.condition) + '</td><td>' + l.records + '</td><td>' + escH(l.action) + '</td><td>' + escH(l.sent_to) + '</td></tr>').join('')
    : '<tr class="empty"><td colspan="5">No actions yet. Send or dismiss an alert and it will appear here.</td></tr>';
  document.getElementById('logcount').textContent = log.length;
}

function addLog(id, action) {
  const r = cur(id);
  log.push({time: now(), condition: r.name, records: r.count, action: action, sent_to: r.notify});
  saveLog(); renderLog();
}

function applySearch() {
  const q = (document.getElementById('search').value || '').trim().toLowerCase();
  document.querySelectorAll('#alerts .tbl tbody tr:not(.empty)').forEach(tr => {
    tr.style.display = !q || tr.textContent.toLowerCase().includes(q) ? '' : 'none';
  });
}

document.addEventListener('click', e => {
  const b = e.target.closest('[data-act]'); if (!b) return;
  const el = b.closest('.issue'); const id = el && el.dataset.id; const act = b.dataset.act;
  if (act === 'toggle') { state.open[id] = !state.open[id]; renderIssue(id); }
  else if (act === 'send') {
    const r = cur(id);
    r.actions.forEach(x => addLog(id, x));
    state.sent[id + ':' + state.value[id]] = now();
    renderIssue(id); toast('Sent ✓ ' + r.notify + ' notified');
  }
  else if (act === 'dismiss') { state.dismissed[id] = true; addLog(id, 'Dismissed by reviewer'); renderIssue(id); renderBadge(); toast('Alert dismissed'); }
  else if (act === 'restore') { state.dismissed[id] = false; renderIssue(id); renderBadge(); }
  else if (act === 'drafts') { const d = f(el, 'drafts'); d.hidden = !d.hidden; }
  else if (act === 'dldrafts') { const r = cur(id); if (r.drafts.length) download('drafts_' + id + '.csv', csv(r.drafts)); else toast('No drafts at this setting'); }
  else if (act === 'export') { if (log.length) download('action_log.csv', csv(log)); else toast('The action log is empty'); }
  else if (act === 'clearlog') { log = []; saveLog(); renderLog(); toast('Action log cleared'); }
});
document.addEventListener('input', e => {
  if (e.target.dataset.act === 'slide') { const id = e.target.closest('.issue').dataset.id; state.value[id] = +e.target.value; renderIssue(id); renderBadge(); }
  if (e.target.id === 'search') applySearch();
});
document.querySelectorAll('[data-go]').forEach(a => a.addEventListener('click', e => {
  e.preventDefault();
  try { window.parent.location.search = '?page=' + a.dataset.go; } catch (err) { window.top.location.search = '?page=' + a.dataset.go; }
}));
function showPage(name) {
  document.querySelectorAll('.page').forEach(p => p.hidden = p.dataset.page !== name);
  document.querySelectorAll('a.navi[href^="#"]').forEach(n => n.classList.toggle('on', n.getAttribute('href') === '#' + name));
  window.scrollTo(0, 0);
  try { sessionStorage.setItem('chrome_oak_page', name); } catch (e) {}
}
document.querySelectorAll('a[href^="#"]').forEach(a => a.addEventListener('click', e => {
  e.preventDefault(); showPage(a.getAttribute('href').slice(1));
}));
let startPage = 'overview';
try { startPage = sessionStorage.getItem('chrome_oak_page') || 'overview'; } catch (e) {}
showPage(document.querySelector('.page[data-page="' + startPage + '"]') ? startPage : 'overview');

let firstOpen = false;
ALERTS.forEach(a => {
  state.value[a.id] = a.default;
  if (!firstOpen && a.results[String(a.default)].count) { state.open[a.id] = true; firstOpen = true; }
  renderIssue(a.id);
});
renderBadge(); renderLog();
</script>
"""


def render_page(focus, kpis, charts, prep, insights, alerts, dropped):
    nav = [("overview", "home", "Overview"), ("insights", "chart", "Insights"), ("alerts", "bell", "Alerts"),
           ("data", "data", "Data prep"), ("log", "log", "Action log")]
    navh = "".join(
        f'<a href="#{a}" class="navi{" on" if i == 0 else ""}">{I(ic, 18, OAK if i == 0 else MUT)}<span style="flex:1">{t}</span>'
        + ('<span class="badge" data-badge>0</span>' if a == "alerts" else "") + "</a>"
        for i, (a, ic, t) in enumerate(nav)
    )
    removed = pd.DataFrame(dropped)[["reason", "file", "csv_line", "id", "detail"]] if dropped else pd.DataFrame()
    removed_csv = removed.to_csv(index=False)
    removed_html = (
        f'<details class="removed"><summary>See the {len(removed)} rows we removed, one by one</summary>'
        f'{table_html(removed.rename(columns={"csv_line": "line in raw file"}))}'
        f'<a class="btn ghost" style="text-decoration:none;margin-bottom:14px" download="removed_rows.csv" '
        f'href="data:text/csv;charset=utf-8,{_html.escape(quote(removed_csv))}">{I("down", 15, INK)} Download removed rows</a></details>'
        if len(removed) else ""
    )

    body = f'''<div style="min-height: 100vh; display: grid; grid-template-columns: 256px 1fr; background: {BG}">
<aside style="background: linear-gradient(180deg, #F1F3F5 0%, #D9DCE0 55%, #C9CDD2 100%); border-right: 1px solid #B9BFC6; padding: 22px 16px">
<div style="position: sticky; top: 22px; display: flex; flex-direction: column; gap: 6px">
<div style="display: flex; align-items: center; gap: 8px; padding: 4px 10px 18px; {SLAB}; font-size: 20px; color: {OAKD}">{I("leaf", 22, OAK)} Chrome &amp; Oak</div>
<div style="font-size: 11px; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase; color: {MUT}; padding: 0 14px 6px">Workspace</div>
{navh}
<a href="#" data-go="welcome" class="navi" style="margin-top: 18px">{I("back", 18, MUT)}<span>Back to welcome</span></a>
</div></aside>
<main style="padding: 22px 32px 160px; min-width: 0; display: flex; flex-direction: column; gap: 18px">
<div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap">
<label style="flex: 1; min-width: 220px; display: flex; align-items: center; gap: 8px; background: #FFFFFF; border: 3px solid {LINE}; border-radius: 999px; padding: 0 16px; min-height: 46px; color: {MUT}">{I("search", 16, MUT)}<input id="search" placeholder="Search alerts: customer, rep, product, region" style="border: none; outline: none; font-family: inherit; font-size: 15px; flex: 1; background: transparent"></label>
<span style="display: inline-flex; align-items: center; gap: 8px; background: #FFFFFF; border: 3px solid {LINE}; border-radius: 999px; padding: 0 16px; min-height: 46px; font-size: 15px; font-weight: 700">{I("cal", 16, MUT)} Jan 2025 – Sep 2026</span>
<button class="btn oak" data-act="export" style="min-height: 46px">{I("down", 16, "#FFFFFF")} Export log</button>
</div>
<section class="page" data-page="overview">
<div>
<div style="position: relative; overflow: hidden; background: #C9CDD2; border-radius: 28px 28px 0 0; padding: 30px 32px; display: flex; justify-content: space-between; align-items: center; gap: 20px; flex-wrap: wrap">
<div style="position: absolute; width: 520px; height: 520px; border-radius: 50%; border: 40px solid #D9DCE0; top: -330px; right: -100px"></div>
<span style="position: absolute; top: 22px; right: 34%">{DV_SPARK.format(s=22)}</span><span style="position: absolute; bottom: 18px; left: 48%">{DV_SPARK.format(s=16)}</span>
<span style="position: absolute; top: -14px; right: 18px">{DV_DAISY.format(s=84)}</span>
<div style="position: relative"><h1 style="margin: 0; {SLAB}; font-size: 44px; line-height: 1.05; color: {OAKD}; text-shadow: 0 3px 0 #FFFFFF">How's business?</h1>
<p style="margin: 8px 0 0; font-size: 17px; font-weight: 700">Revenue is up, but cash is tight. Here's what's driving the gap.</p>
<p style="margin: 10px 0 0; display: inline-block; background: #FFFFFF; border-radius: 14px; padding: 8px 14px; font-size: 15px; font-weight: 600"><b style="color: {OAK}">Our focus:</b> {esc(focus)}</p></div>
<span style="position: relative; display: inline-flex; align-items: center; gap: 8px; font-size: 14px; font-weight: 800; color: {OAKD}; background: #FFFFFF; border-radius: 999px; padding: 8px 14px; margin-right: 90px">{I("check", 14, OAK, 3)} Data as of {ASOF:%b %d, %Y}</span>
</div>
<div class="checker" style="height: 26px; border-radius: 0 0 28px 28px"></div>
</div>
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 16px">{kpi_cards(kpis)}</div>
<div class="card-cta"><div><div style="font-size: 18px; font-weight: 800"><span data-badge>0</span> alerts need a decision</div><div style="font-size: 14px; color: {MUT}">Chrome and Oak have drafted the follow-ups. Review and send them.</div></div><a href="#alerts" class="btn oak" style="text-decoration: none">Open alerts {I("arrow", 15, "#FFFFFF")}</a></div>
</section>
<section class="page" data-page="insights" hidden>
<div class="ptitle">Insights</div>
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(380px, 1fr)); gap: 16px">{chart_cards(charts)}</div>
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px">{insight_cards(insights)}</div>
</section>
<section class="page" data-page="alerts" hidden>
<div id="alerts" style="{CARD}; overflow: hidden">
<div style="display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; padding: 18px 22px"><div><div style="{SLAB}; font-size: 22px">Alerts inbox</div><div style="font-size: 14px; color: {MUT}">Triggered automatically when a rule is met. Move a slider to change the rule and see what it catches.</div></div><a href="#log" class="navlink" style="font-size: 15px; font-weight: 800; text-decoration: none; color: {OAKD}; display: inline-flex; align-items: center; gap: 6px">View action log {I("arrow", 14, OAKD)}</a></div>
{"".join(alert_block(a) for a in alerts)}
</div>
</section>
<section class="page" data-page="data" hidden>
<div id="data" style="{CARD}; padding: 20px 22px 8px"><div style="display: flex; align-items: center; gap: 10px">{I("data", 20, OAK)}<div style="{SLAB}; font-size: 22px">How we prepared the data</div></div><div style="font-size: 14px; color: {MUT}; margin: 4px 0 8px">Every change we made before trusting a number. The raw exports are never edited.</div>{prep_rows(prep)}{removed_html}</div>
</section>
<section class="page" data-page="log" hidden>
<div id="log" style="{CARD}; overflow: hidden; padding-top: 18px">
<div style="display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; padding: 0 22px 12px"><div><div style="{SLAB}; font-size: 22px">Action log · <span id="logcount">0</span></div><div style="font-size: 14px; color: {MUT}">Everything sent or dismissed, newest first. Saved in this browser. Nothing is emailed for real in this prototype.</div></div>
<div style="display: flex; gap: 10px"><button class="btn ghost" data-act="clearlog">Clear</button><button class="btn oak" data-act="export">{I("down", 15, "#FFFFFF")} Download (CSV)</button></div></div>
<div class="tbl"><table><thead><tr><th>Time</th><th>Condition</th><th>Records</th><th>Action</th><th>Sent to</th></tr></thead><tbody id="logbody"></tbody></table></div>
</div>
</section>
</main></div><div id="toast" role="status"></div>'''

    js = JS.replace("__ALERTS__", json.dumps(alerts).replace("</", "<\\/")).replace(
        "__SEV__", json.dumps({k: list(v) for k, v in SEV.items()})
    )
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Alfa+Slab+One&family=Nunito:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>{DV_CSS}{EXTRA_CSS}</style>{MASCOT_CSS}</head><body>{body}{js}</body></html>'''


# The dashboard fills the whole browser window and scrolls inside itself.
html("""<style>
header[data-testid="stHeader"], section[data-testid="stSidebar"], [data-testid="collapsedControl"]{display:none !important}
.block-container{max-width:none !important;padding:0 !important}
iframe{border:none;display:block;height:100vh !important}
</style>""")

_, _orders, _returns, _dropped, _ = load_data()
alerts = build_alerts()
components.html(
    render_page(get_focus(), get_kpis(), get_charts(), get_prep_steps(), get_insights(), alerts, _dropped),
    height=900,
    scrolling=True,
)


# ---------------------------------------------------------------------------
# 5. Chrome & Oak floating in the bottom-right corner, talking to each other
# ---------------------------------------------------------------------------
flagged = [(a, a["results"][str(a["default"])]) for a in alerts if a["results"][str(a["default"])]["count"]]
if not flagged:
    show_pets("happy", "I checked every order, return and invoice. All clear!", "Great, nothing needs action right now.")
else:
    a, top = max(flagged, key=lambda x: x[1]["impact"])
    show_pets(
        "worried" if len(flagged) == 1 else "sad",
        f"{len(flagged)} alerts are open. Biggest: {top['count']} {top['name']}.",
        f"I drafted everything. Open the alert and send it to {top['notify']}.",
    )
