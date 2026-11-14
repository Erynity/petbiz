"""Chrome & Oak – business health check (Hack2theFuture, Business track, Option B).

Two pages, matching the approved mockup:
  1. Welcome page  -> "Open the dashboard" button
  2. Dashboard     -> chrome sidebar, banner, KPIs, charts, data prep, insights, alerts

This file only DISPLAYS results. The data work lives in analysis.py (teammate).
Until analysis.py has these functions, clearly-labelled placeholders are shown:

    get_focus()            -> str, the one problem we chose, in one sentence
    get_kpis()             -> list of dicts {"label", "value", "delta"}
    get_charts()           -> list of dicts {"title", "caption", "data": DataFrame, "kind": "line"|"bar"}
    get_prep_steps()       -> list of dicts {"what", "rows", "why"}
    get_insights()         -> list of dicts {"title", "what", "why", "todo"}
    detect_issues(days)    -> list of dicts {"name", "severity", "rule", "rows": DataFrame,
                                             "found", "actions": [str], "notify"}
                              `days` comes from the slider (Simulation bonus).

Run with:  streamlit run app.py
"""

import altair as alt
import pandas as pd
import streamlit as st

from pet import MASCOT_CSS, mascot_svg, mascots_pair

st.set_page_config(page_title="Chrome & Oak · Health Check", page_icon="💼", layout="wide")

# ---------------------------------------------------------------------------
# 1. Connect to analysis.py (placeholders until it's ready)
# ---------------------------------------------------------------------------
try:
    from analysis import detect_issues, get_charts, get_focus, get_insights, get_kpis, get_prep_steps

    USING_PLACEHOLDERS = False
except ImportError:
    USING_PLACEHOLDERS = True

    def get_focus():
        return "[The one problem we chose, in one sentence]"

    def get_kpis():
        return [
            {"label": "Revenue", "value": "$ —", "delta": "— vs last year"},
            {"label": "Gross margin", "value": "— %", "delta": "— pts vs last year"},
            {"label": "Overdue invoices", "value": "$ —", "delta": "— invoices"},
            {"label": "Return rate", "value": "— %", "delta": "— of orders"},
        ]

    def get_charts():
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
        line = pd.DataFrame({"Revenue": [10, 11, 12, 13, 14, 15], "Cash collected": [9, 9, 9, 9, 9, 9]}, index=months)
        bars = pd.DataFrame({"Avg discount %": [4, 5, 6, 9]}, index=["Q1", "Q2", "Q3", "Q4"])
        return [
            {"title": "Revenue vs. cash collected", "caption": "Placeholder shape", "data": line, "kind": "line"},
            {"title": "Average discount by quarter", "caption": "Placeholder shape", "data": bars, "kind": "bar"},
        ]

    def get_prep_steps():
        return [
            {"what": "Removed duplicate orders", "rows": "— rows", "why": "So the same sale isn't counted twice."},
            {"what": "Fixed dates and amounts stored as text", "rows": "— rows", "why": "So we can sort by date and add up dollars."},
            {"what": "Handled missing values", "rows": "— rows", "why": "[What we did, and why]"},
            {"what": "Joined orders, customers and returns", "rows": "3 files → 1", "why": "So each order shows its customer, region, rep and returns."},
        ]

    def get_insights():
        return [
            {"title": "Insight title", "what": "Filled in once we have the data.", "why": "Filled in once we have the data.", "todo": "Filled in once we have the data."},
            {"title": "Insight title", "what": "Filled in once we have the data.", "why": "Filled in once we have the data.", "todo": "Filled in once we have the data."},
        ]

    def detect_issues(days=30):
        rows = pd.DataFrame({"customer": ["[Customer A]", "[Customer B]"], "region": ["[Region]", "[Region]"], "detail": ["—", "—"]})
        return [
            {"name": "customers over their credit limit", "severity": "High",
             "rule": f"owes more than their credit limit AND is {days}+ days late",
             "rows": rows, "found": "[Customer A] owes too much",
             "actions": ["New orders paused", "Reminder email written", "[Account rep] notified"],
             "notify": "Account rep"},
            {"name": "long-time customers gone quiet", "severity": "Low",
             "rule": "ordered every quarter before, nothing in the last 90 days",
             "rows": rows.head(1), "found": "[Customer B] stopped ordering",
             "actions": ["Check-in task created", "Customer Success notified"],
             "notify": "Customer Success"},
        ]


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
        f'<div class="stage">{mascots_pair("happy", "happy", 150, walk_in=True)}</div>'
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
        rerun()
    st.stop()


# ---------------------------------------------------------------------------
# 4. Static charts (no scroll-to-zoom)
# ---------------------------------------------------------------------------
def draw_chart(chart):
    df = chart["data"].reset_index()
    x = df.columns[0]
    ys = list(df.columns[1:])
    long = df.melt(id_vars=x, value_vars=ys, var_name="_series", value_name="_value")
    x_type = "T" if pd.api.types.is_datetime64_any_dtype(long[x]) else "N"
    base = alt.Chart(long)
    mark = (base.mark_line(point=True, strokeWidth=3) if chart.get("kind") == "line"
            else base.mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8))
    enc = dict(
        x=alt.X(f"{x}:{x_type}", sort=None, title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("_value:Q", title=None),
        color=alt.Color("_series:N", scale=alt.Scale(range=[OAK, "#9AA0A8", "#D4A84A", OAKD]),
                        legend=alt.Legend(orient="top", title=None) if len(ys) > 1 else None),
        tooltip=[alt.Tooltip(f"{x}:{x_type}", title=str(x)), alt.Tooltip("_series:N", title="series"),
                 alt.Tooltip("_value:Q", title="value", format=",.0f")],
    )
    if chart.get("kind") != "line" and len(ys) > 1:
        enc["xOffset"] = "_series:N"
    st.altair_chart(
        mark.encode(**enc).properties(height=260).configure_view(strokeWidth=0)
        .configure_axis(labelColor=MUT, gridColor="#EEF0F2", domainColor=LINE, labelFont="Nunito", labelFontSize=12),
        use_container_width=True,
    )


# ---------------------------------------------------------------------------
# 5. Dashboard
# ---------------------------------------------------------------------------
# Simulation bonus: threshold slider (in the sidebar so it's always reachable)
with st.sidebar:
    html(f'<div class="logo">{LEAF} Chrome &amp; Oak</div>')
    days = st.slider("Flag invoices after (days late)", 15, 90, 30, 5)

issues = detect_issues(days)
flagged = [i for i in issues if len(i["rows"]) > 0]

with st.sidebar:
    html(
        '<div class="navi on">Overview</div>'
        f'<div class="navi">Alerts<span class="badge">{len(flagged)}</span></div>'
        f'<div class="duty"><div style="display:flex;justify-content:center">{mascots_pair("happy", "happy", 72)}</div>'
        "<b>Your analysts are on duty</b><span>Chrome checks the data. Oak handles the follow-ups.</span></div>"
    )
    if st.button("← Back to welcome"):
        st.session_state.started = False
        rerun()

if USING_PLACEHOLDERS:
    html('<span class="tag">Placeholders · waiting for analysis.py</span>')

# Banner
html(
    '<div class="banner"><div class="ring"></div>'
    + SPARK.format(pos="top:22px;right:34%", s=22) + SPARK.format(pos="bottom:18px;left:48%", s=16)
    + DAISY.format(s=84)
    + "<div><h1>How's business?</h1>"
    "<p>Revenue is up, but cash is tight. Here's what's driving the gap.</p>"
    f'<div class="focus"><b>Our focus:</b> {get_focus()}</div></div>'
    '<span class="checked">✓ Data checked today</span>'
    '</div><div class="checker"></div>'
)

# KPIs
kpis = get_kpis()
for col, k in zip(st.columns(len(kpis)), kpis):
    col.markdown(
        f'<div class="card kpi"><div class="lab">{k["label"]}</div><div class="val">{k["value"]}</div>'
        f'<div class="del">{k["delta"]}</div></div>',
        unsafe_allow_html=True,
    )

# Charts (DETECT)
charts = get_charts()
for col, ch in zip(st.columns([2, 1]) if len(charts) == 2 else st.columns(len(charts)), charts):
    with col:
        with st.container(border=True):
            html(f'<div class="ttl">{ch["title"]}</div><div class="sub">{ch["caption"]}</div>')
            draw_chart(ch)

# Data prep (DATA)
prep = "".join(
    f'<div class="prep"><div><div class="ttl" style="font-size:15px">✓ {p["what"]}</div>'
    f'<p style="margin:2px 0 0"><b style="color:#8B5E3C">Why:</b> {p["why"]}</p></div>'
    f'<span class="rows">{p["rows"]}</span></div>'
    for p in get_prep_steps()
)
html(f'<div class="card"><div class="slab">How we prepared the data</div>'
     f'<div class="sub">Every change we made before trusting a number</div>{prep}</div>')

# Insights (DECIDE)
ins = get_insights()
for i, (col, x) in enumerate(zip(st.columns(len(ins)), ins), start=1):
    col.markdown(
        f'<div class="card"><span class="pill">Insight {i}</span>'
        f'<div style="font-size:20px;font-weight:700;margin:10px 0 4px">{x["title"]}</div>'
        f'<div class="lbl">What happened</div><p>{x["what"]}</p>'
        f'<div class="lbl">Why it matters</div><p>{x["why"]}</p>'
        f'<div class="lbl">What to do</div><p>{x["todo"]}</p></div>',
        unsafe_allow_html=True,
    )

# Alerts (ACT)
html('<div class="slab" style="margin:8px 0 2px">Alerts inbox</div>'
     f'<div class="sub">Triggered automatically when a condition is met · flagging after <b>{days} days</b></div>')

log = []
for n, issue in enumerate(issues):
    count = len(issue["rows"])
    with st.expander(f"{issue['severity']} · {count} {issue['name']}", expanded=(n == 0 and count > 0)):
        if not count:
            st.write("All clear, nothing to do.")
            continue
        c1, c2, c3 = st.columns(3)
        c1.markdown(
            f'<div class="step3"><div class="who"><span style="flex:none">{mascot_svg("chrome", "worried", 58)}</span>'
            f'<div><div class="k">Step 1 · Chrome noticed</div><div class="h">{issue["found"]}</div></div></div>'
            f'<p style="margin:8px 0 0;font-size:15px;color:#565B62">Rule: {issue["rule"]}.</p></div>',
            unsafe_allow_html=True,
        )
        done = "".join(f'<div class="done">✓ {a}</div>' for a in issue["actions"])
        c2.markdown(
            f'<div class="step3 oak"><div class="who"><span style="flex:none">{mascot_svg("oak", "happy", 58)}</span>'
            f'<div><div class="k">Step 2 · Oak took care of it</div><div class="h">{len(issue["actions"])} things done</div></div></div>'
            f"{done}</div>",
            unsafe_allow_html=True,
        )
        with c3:
            html('<div class="step3"><div class="k">Step 3 · Your turn</div><div class="h">Review and send?</div></div>')
            if st.button("Preview & send", key=f"send{n}"):
                st.toast(f"Sent to {issue['notify']} ✓")
            st.button("Not a problem, dismiss", key=f"dis{n}")
        table(issue["rows"])
        for a in issue["actions"]:
            log.append({"condition": issue["name"], "records": count, "action": a, "sent to": issue["notify"]})

if log:
    with st.expander("View action log"):
        log_df = pd.DataFrame(log)
        table(log_df)
        st.download_button("Download action log (CSV)", log_df.to_csv(index=False), "action_log.csv", "text/csv")
