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


import pandas as pd
import streamlit as st

from pet import MASCOT_CSS, mascot_svg, mascots_pair, show_pets

st.set_page_config(page_title="Chrome & Oak · Health Check", page_icon="💼", layout="wide")

# ---------------------------------------------------------------------------
# 1. Connect to analysis.py (placeholders until it's ready)
# ---------------------------------------------------------------------------
USING_PLACEHOLDERS = True
if True:  # placeholders first; real functions from analysis.py override them below
    def get_focus():
        return "[The one problem we chose, in one sentence]"

    def get_kpis():
        return [
            {"label": "Revenue", "value": "$ —", "delta": "— vs last year", "trend": [1, 2, 3, 4, 6, 7, 9]},
            {"label": "Gross margin", "value": "— %", "delta": "— pts vs last year", "trend": [9, 8, 8, 6, 5, 3, 2]},
            {"label": "Overdue invoices", "value": "$ —", "delta": "— invoices", "trend": [1, 2, 2, 4, 5, 7, 8]},
            {"label": "Return rate", "value": "— %", "delta": "— of orders", "trend": [3, 4, 3, 5, 5, 6, 6]},
        ]

    def get_charts():
        reps = pd.DataFrame({"avg_discount": [0.23, 0.11, 0.10, 0.10, 0.09, 0.09, 0.09, 0.09, 0.09, 0.09, 0.08]},
                            index=["R07", "R09", "R06", "R03", "R05", "R08", "R01", "R10", "R04", "R11", "R02"])
        regions = pd.DataFrame({"margin": [0.33, 0.33, 0.32, 0.32, 0.16]},
                               index=["Quebec", "BC", "Prairies", "Ontario", "Atlantic"])
        return [
            {"title": "Average discount by sales rep", "caption": "Atlantic rep highlighted",
             "desc": "How much off list price each rep gives on average. One rep stands far above the rest.", "data": reps,
             "kind": "bar", "format": "percent", "sort": True, "highlight": "R07", "x_title": "Sales rep"},
            {"title": "Margin % by region", "caption": "Atlantic highlighted",
             "desc": "Profit left after costs and discounts. Atlantic keeps about half of what other regions keep.", "data": regions,
             "kind": "bar", "format": "percent", "highlight": "Atlantic", "x_title": "Region"},
        ]

    def get_data():
        """The cleaned orders table, one row per order (placeholder sample)."""
        import numpy as np
        rng = np.random.default_rng(1)
        n = 60
        regions = rng.choice(["Atlantic", "Ontario", "Quebec", "BC", "Prairies"], n)
        qty = rng.integers(1, 20, n)
        price = rng.choice([45.0, 120.0, 226.0, 331.0, 636.0], n)
        disc = np.where(regions == "Atlantic", rng.uniform(0.15, 0.3, n), rng.uniform(0.0, 0.12, n)).round(3)
        return pd.DataFrame({
            "order_id": [f"SO-{i:06d}" for i in range(n)],
            "order_date": pd.date_range("2025-01-05", periods=n, freq="9D").date,
            "customer_id": [f"C{rng.integers(1, 1200):04d}" for _ in range(n)],
            "region": regions, "rep": rng.choice(["R01", "R02", "R07", "R09"], n),
            "product": rng.choice(["Office Chair", "Monitor 27\"", "ErgoLift Standing Desk", "Wireless Mouse"], n),
            "quantity": qty, "unit_price": price, "discount": disc,
            "amount": (qty * price * (1 - disc)).round(2),
        })

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
        rows = pd.DataFrame({"customer": ["[Customer A]", "[Customer B]", "[Customer C]"], "region": ["Atlantic", "Ontario", "Atlantic"],
                             "owes": ["$ —", "$ —", "$ —"], "days_late": [72, 41, 33]})
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


# Use each function from analysis.py as soon as it exists (the rest stay placeholders)
_ALL = ("get_data", "get_focus", "get_kpis", "get_charts", "get_prep_steps", "get_insights", "detect_issues")
_real, CONNECT_ERROR = [], ""
try:
    import importlib

    import analysis as _an

    importlib.reload(_an)  # always pick up the latest analysis.py without restarting
    _real = [n for n in _ALL if hasattr(_an, n)]
    for _n in _real:
        globals()[_n] = getattr(_an, _n)
except Exception as _e:  # show the problem on the page instead of failing silently
    CONNECT_ERROR = f"{type(_e).__name__}: {_e}"
USING_PLACEHOLDERS = len(_real) < len(_ALL)
CONNECT_STATUS = (
    f"analysis.py error → {CONNECT_ERROR}" if CONNECT_ERROR
    else f"Connected: {', '.join(_real) or 'nothing yet'} · Still placeholders: {', '.join(n for n in _ALL if n not in _real) or 'none'}"
)


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
# 3. Pages: ?page=welcome (default) | overview | data | insights | alerts | prep
#    Each sidebar link opens a real new page (no scrolling jumps).
# ---------------------------------------------------------------------------
import inspect

from dashboard_view import I, bar_chart_svg, esc, sparkline

PAGES = [("overview", "home", "Overview"), ("data", "log", "Data list"), ("insights", "chart", "Insights"),
         ("alerts", "bell", "Alerts"), ("prep", "data", "Data prep")]
page = st.query_params.get("page", "welcome") if hasattr(st, "query_params") else "welcome"
if page not in {p for p, _, _ in PAGES}:
    page = "welcome"

# ---------------- Welcome ----------------
if page == "welcome":
    html(
        f'<div class="topbar"><span class="logo" style="margin:0">{LEAF} Chrome &amp; Oak</span>'
        '<span class="t">Office Supply · Business health check</span></div>'
        '<div class="hero"><div class="ring"></div>'
        + SPARK.format(pos="top:26px;left:46%", s=26) + SPARK.format(pos="bottom:30px;left:6%", s=18)
        + DAISY.format(s=96)
        + '<div><div class="hi">Hi! We\'re Chrome &amp; Oak. Let\'s check on the business.</div>'
        "<h1>Revenue is up.<br>So why is cash tight?</h1>"
        "<p>We dig through the orders, returns and customers, then act on what needs attention.</p>"
        '<a class="go" href="?page=overview" target="_self">Open the dashboard →</a></div>'
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
    st.stop()

# ---------------- Shared dashboard frame ----------------
html("""<style>
section[data-testid="stSidebar"], [data-testid="collapsedControl"], [data-testid="stSidebarCollapsedControl"]{display:none !important}
.block-container{max-width:none !important;padding:22px 36px 140px 292px !important}
.side{position:fixed;top:0;left:0;bottom:0;width:256px;z-index:999990;padding:22px 16px;display:flex;flex-direction:column;gap:6px;
  background:linear-gradient(180deg,#F1F3F5 0%,#D9DCE0 55%,#C9CDD2 100%);border-right:1px solid #B9BFC6}
.side a{text-decoration:none !important}
.side .home{display:flex;align-items:center;gap:8px;font-family:'Alfa Slab One',serif;font-size:20px;color:#5E3B22 !important;padding:4px 10px 18px}
.side .navi{color:#2A2420 !important}
.side .navi.on{color:#5E3B22 !important}
.pagehead{display:flex;justify-content:space-between;align-items:flex-end;gap:16px;flex-wrap:wrap;margin-bottom:6px}
.pagehead h2{margin:0 !important;font-size:34px !important}
.pagehead p{margin:4px 0 0;color:#565B62;font-size:16px}
.section{margin:30px 0 10px;padding-top:18px;border-top:3px solid #DDE0E4}
.section h3{margin:0 !important;font-size:24px !important}
.section p{margin:6px 0 0;color:#565B62;font-size:16px;max-width:760px}
.chartbox{background:#FFFFFF;border:3px solid #DDE0E4;border-radius:24px;padding:20px 22px;margin-top:12px}
.go{position:relative;display:inline-flex;align-items:center;gap:8px;margin-top:22px;background:#8B5E3C;color:#FFFFFF !important;text-decoration:none !important;
  font-weight:800;font-size:17px;border-radius:999px;padding:14px 28px;box-shadow:0 3px 0 #5E3B22}
div[data-baseweb="select"] > div{border-radius:999px !important;border:3px solid #DDE0E4 !important;background:#FFFFFF !important}
</style>""")


def sidebar(active, alert_count):
    links = "".join(
        f'<a class="navi{" on" if p == active else ""}" href="?page={p}" target="_self">'
        f'{icon(ic, "#8B5E3C" if p == active else "#565B62")}<span>{label}</span>'
        + (f'<span class="badge">{alert_count}</span>' if p == "alerts" and alert_count else "") + "</a>"
        for p, ic, label in PAGES
    )
    html(f'<div class="side"><a class="home" href="?page=welcome" target="_self" title="Back to the main page">{LEAF} Chrome &amp; Oak</a>'
         f'<div class="navlbl">Workspace</div>{links}</div>')


def page_head(title, sub):
    html(f'<div class="pagehead"><div><h2>{title}</h2><p>{sub}</p></div></div>')
    if USING_PLACEHOLDERS:
        html(f'<span class="tag">{esc(CONNECT_STATUS)}</span>')


def section(title, desc=""):
    html(f'<div class="section"><h3>{title}</h3>' + (f"<p>{desc}</p>" if desc else "") + "</div>")


issues = detect_issues(st.session_state.get("days", 30))
flagged = [i for i in issues if len(i["rows"]) > 0]
sidebar(page, len(flagged))

# ---------------- Overview ----------------
if page == "overview":
    html(
        '<div class="banner"><div class="ring"></div>'
        + SPARK.format(pos="top:22px;right:34%", s=22) + SPARK.format(pos="bottom:18px;left:48%", s=16)
        + DAISY.format(s=84)
        + "<div><h1>How's business?</h1>"
        "<p>Revenue is up, but cash is tight. Here's what's driving the gap.</p>"
        f'<div class="focus"><b>Our focus:</b> {esc(get_focus())}</div></div>'
        '<span class="checked">✓ Data checked today</span>'
        '</div><div class="checker"></div>'
    )
    if USING_PLACEHOLDERS:
        html(f'<span class="tag">{esc(CONNECT_STATUS)}</span>')
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
        col.markdown(
            f'<div class="card"><span class="pill">Insight {i}</span>'
            f'<div style="font-size:20px;font-weight:700;margin:10px 0 4px">{esc(x["title"])}</div>'
            f'<div class="lbl">What happened</div><p>{esc(x["what"])}</p>'
            f'<div class="lbl">Why it matters</div><p>{esc(x["why"])}</p>'
            f'<div class="lbl">What to do</div><p>{esc(x["todo"])}</p></div>',
            unsafe_allow_html=True,
        )
    if flagged:
        section("Needs attention", f"{len(flagged)} alert types were triggered automatically.")
        for i in flagged:
            html(f'<div class="card" style="padding:14px 20px"><span class="sev {i["severity"]}">{esc(i["severity"])}</span>'
                 f'<b>{len(i["rows"])} {esc(i["name"])}</b> · <a href="?page=alerts" target="_self">Open alerts →</a></div>')

# ---------------- Data list ----------------
elif page == "data":
    df = get_data().copy()
    page_head("Data list", f"Every cleaned order, {len(df):,} rows. Filter and sort to explore.")
    c1, c2, c3, c4 = st.columns([2, 2, 1.4, 1])
    if "region" in df.columns:
        regions = sorted(df["region"].dropna().astype(str).unique())
        pick = c1.multiselect("Region", regions, placeholder="All regions")
        if pick:
            df = df[df["region"].astype(str).isin(pick)]
    q = c2.text_input("Search", placeholder="Customer, product, rep…")
    if q:
        df = df[df.astype(str).apply(lambda r: r.str.contains(q, case=False)).any(axis=1)]
    money = [c for c in ("amount", "revenue", "net_amount", "total") if c in df.columns]
    sort_col = c3.selectbox("Sort by", list(df.columns), index=list(df.columns).index(money[0]) if money else 0)
    order = c4.selectbox("Order", ["Biggest first", "Smallest first"])
    df = df.sort_values(sort_col, ascending=(order == "Smallest first"))
    shown = df.head(200)
    html(f'<div class="sub" style="margin-top:6px">Showing {len(shown):,} of {len(df):,} rows</div>')
    table(shown)
    st.download_button("Download these rows (CSV)", df.to_csv(index=False), "chrome_oak_orders.csv", "text/csv")

# ---------------- Insights ----------------
elif page == "insights":
    page_head("Insights", "The patterns, problems and opportunities we found. One chart per finding.")
    data = get_data()
    regions = sorted(data["region"].dropna().astype(str).unique()) if "region" in data.columns else []
    region = st.selectbox("Show charts for", ["All regions"] + regions) if regions else "All regions"
    takes_region = "region" in inspect.signature(get_charts).parameters
    charts = get_charts(region=None if region == "All regions" else region) if takes_region else get_charts()
    if region != "All regions" and not takes_region:
        html('<span class="tag">Region filter needs get_charts(region) in analysis.py</span>')
    for ch in charts:
        section(esc(ch["title"]), esc(ch.get("desc", ch.get("caption", ""))))
        html(f'<div class="chartbox">{bar_chart_svg(ch)}</div>')
    ins = get_insights()
    section("What it means", "Each insight: what happened, why it matters, and what Chrome & Oak should do.")
    for i, (col, x) in enumerate(zip(st.columns(len(ins)), ins), start=1):
        col.markdown(
            f'<div class="card"><span class="pill">Insight {i}</span>'
            f'<div style="font-size:20px;font-weight:700;margin:10px 0 4px">{esc(x["title"])}</div>'
            f'<div class="lbl">What happened</div><p>{esc(x["what"])}</p>'
            f'<div class="lbl">Why it matters</div><p>{esc(x["why"])}</p>'
            f'<div class="lbl">What to do</div><p>{esc(x["todo"])}</p></div>',
            unsafe_allow_html=True,
        )

# ---------------- Alerts ----------------
elif page == "alerts":
    page_head("Alerts", "Checks that run automatically. When a rule is met, Chrome flags it and Oak acts.")
    st.slider("Simulation: flag after (days late)", 15, 90, 30, 5, key="days")
    for n, issue in enumerate(issues):
        count = len(issue["rows"])
        section(f'<span class="sev {issue["severity"]}">{esc(issue["severity"])}</span>{count} {esc(issue["name"])}')
        if not count:
            html('<p style="color:#565B62">All clear, nothing to do.</p>')
            continue
        c1, c2, c3 = st.columns(3)
        c1.markdown(
            f'<div class="step3"><div class="who"><span style="flex:none">{mascot_svg("chrome", "worried", 58)}</span>'
            f'<div><div class="k">Step 1 · Chrome noticed</div><div class="h">{esc(issue["found"])}</div></div></div>'
            f'<p style="margin:8px 0 0;font-size:15px;color:#565B62">Rule: {esc(issue["rule"])}.</p></div>',
            unsafe_allow_html=True,
        )
        done = "".join(f'<div class="done">✓ {esc(a)}</div>' for a in issue["actions"])
        c2.markdown(
            f'<div class="step3 oak"><div class="who"><span style="flex:none">{mascot_svg("oak", "happy", 58)}</span>'
            f'<div><div class="k">Step 2 · Oak took care of it</div><div class="h">{len(issue["actions"])} things done</div></div></div>{done}</div>',
            unsafe_allow_html=True,
        )
        with c3:
            html('<div class="step3"><div class="k">Step 3 · Your turn</div><div class="h">Review and send?</div></div>')
            if st.button("Preview & send", key=f"send{n}"):
                st.toast(f"Sent ✓ {issue['notify']} notified")
            st.button("Not a problem, dismiss", key=f"dis{n}")
        table(issue["rows"])
    log = [{"condition": i["name"], "records": len(i["rows"]), "action": a, "sent to": i["notify"]}
           for i in flagged for a in i["actions"]]
    if log:
        section("Action log", "Everything the automation did, so a person can check it.")
        log_df = pd.DataFrame(log)
        table(log_df)
        st.download_button("Download action log (CSV)", log_df.to_csv(index=False), "action_log.csv", "text/csv")

# ---------------- Data prep ----------------
elif page == "prep":
    page_head("Data prep", "Every change we made before trusting a number, and why.")
    prep = "".join(
        f'<div class="prep"><div><div class="ttl" style="font-size:16px">✓ {esc(p["what"])}</div>'
        f'<p style="margin:2px 0 0"><b style="color:#8B5E3C">Why:</b> {esc(p["why"])}</p></div>'
        f'<span class="rows">{esc(p["rows"])}</span></div>'
        for p in get_prep_steps()
    )
    html(f'<div class="card" style="margin-top:14px">{prep}</div>')

# ---------------------------------------------------------------------------
# 4. Chrome & Oak floating in the bottom-right corner
# ---------------------------------------------------------------------------
if not flagged:
    mood, chrome_msg, oak_msg = "happy", "I checked every order, return and invoice. All clear!", "Great, nothing needs action right now."
else:
    top = max(flagged, key=lambda i: len(i["rows"]))
    mood = "worried" if len(flagged) == 1 else "sad"
    chrome_msg = f"I found {len(top['rows'])} {top['name']}."
    oak_msg = f"Done: {top['actions'][0].lower()}. {top['notify']} notified."
show_pets(mood, chrome_msg, oak_msg)
