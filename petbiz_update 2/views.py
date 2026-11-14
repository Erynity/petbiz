"""The six pages. Each one takes the look of its mockup (mockups/*.html) and fills it with real data from analysis.py.

Navigation uses plain links (?page=...), so the Let's go button and the sidebar always work.
Alerts you send or dismiss are saved in data/action_log.csv, so they survive page changes.
"""

import base64
import html
import re
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

import analysis

HERE = Path(__file__).parent
MOCK = HERE / "mockups"
LOG_FILE = HERE / "data" / "action_log.csv"
LOG_COLS = ["when", "what", "type", "by", "alert"]

PAGES = {"welcome": "1_welcome.html", "overview": "2_overview.html", "data": "3_data.html",
         "insights": "4_insights_chrome.html", "alerts": "5_alerts_oak.html", "log": "6_action_log.html"}
NAV_ORDER = ["welcome", "overview", "data", "insights", "alerts", "log"]

INK, MUT, LINE, OAK, OAKD, GRN, RED = "#2A2420", "#565B62", "#DDE0E4", "#8B5E3C", "#5E3B22", "#2F7D3E", "#B3261E"
CARD = f"background:#FFFFFF;border:3px solid {LINE};border-radius:24px;padding:18px 20px"
E = html.escape


# ---------------------------------------------------------------------------
# st.html strips every <svg>, so each drawing is shown as an <img> with the svg embedded.
# The page's animation css goes inside the svg, so the bears still move.
# ---------------------------------------------------------------------------
_SVG = re.compile(r"<svg\b([^>]*)>(.*?)</svg>", re.S)


def _svg_to_img(m, css):
    attrs, inner = m.group(1), m.group(2)
    keep = " ".join(re.findall(r'\b(?:width|height|style)="[^"]*"', attrs))
    svg_attrs = re.sub(r'\s(?:style|aria-hidden)="[^"]*"', "", attrs)
    style = f"<style>{css}</style>" if 'class="' in attrs + inner else ""
    svg = f'<svg xmlns="http://www.w3.org/2000/svg"{svg_attrs}>{style}{inner}</svg>'
    src = "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()
    return f'<img src="{src}" alt="" {keep}>'


def show(markup, target=st):
    """st.html, but with drawings kept."""
    css = mock_css("welcome")
    target.html(_SVG.sub(lambda m: _svg_to_img(m, css), markup))


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------
def money(x, sign=False):
    s = f"${abs(x) / 1e6:,.2f}M" if abs(x) >= 1e6 else f"${abs(x) / 1e3:,.0f}K" if abs(x) >= 1e4 else f"${abs(x):,.0f}"
    return ("−" if x < 0 else "+" if sign else "") + s


def number(s):
    return float(re.sub(r"[^\d.]", "", str(s)) or 0)


def mock(name):
    return (MOCK / PAGES[name]).read_text(encoding="utf-8")


def mock_css(name):
    return "\n".join(re.findall(r"<style>(.*?)</style>", mock(name), re.S))


def mascot(page, nth=0):
    """The big Chrome / Oak drawing from the right-hand column of a mockup page."""
    return re.findall(r'<div style="display: flex; justify-content: center"><svg.*?</svg></div>', mock(page), re.S)[nth]


@st.cache_data(show_spinner=False)
def orders():
    df = analysis.get_data().copy()
    df["order_date"] = pd.to_datetime(df["order_date"])
    df["net"] = df["amount"] - df["refund"]
    return df


# ---------------------------------------------------------------------------
# action log (a file, because a link click reloads the page)
# ---------------------------------------------------------------------------
def read_log():
    if LOG_FILE.exists():
        return pd.read_csv(LOG_FILE, dtype=str).fillna("")
    return pd.DataFrame(columns=LOG_COLS)


def write_log(rows):
    now = datetime.now().strftime("Today %H:%M")
    new = pd.DataFrame([{"when": now, "what": w, "type": t, "by": b, "alert": a} for w, t, b, a in rows])
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    pd.concat([read_log(), new], ignore_index=True).to_csv(LOG_FILE, index=False)


def handled(alert_id, log):
    """'Sent', 'Dismissed' or '' for one alert."""
    mine = log[log["alert"] == alert_id]
    for t, label in (("Dismissed", "Dismissed"), ("Notify", "Sent")):
        if (mine["type"] == t).any():
            return label
    return ""


def open_alert_count(days):
    log = read_log()
    return sum(1 for i in analysis.detect_issues(days) if len(i["rows"]) and not handled(i["id"], log))


# ---------------------------------------------------------------------------
# page frame: global css, sidebar, heading
# ---------------------------------------------------------------------------
def inject_css(full_bleed=False):
    pad = "0" if full_bleed else "26px 32px 60px 272px"
    st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Alfa+Slab+One&family=Nunito:wght@400;600;700;800&display=swap');
header[data-testid="stHeader"], section[data-testid="stSidebar"], [data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"], [data-testid="stToolbar"], footer {{display:none !important}}
.stApp{{background:#F4F5F7;font-family:'Nunito',sans-serif;color:{INK}}}
.block-container{{max-width:none !important;padding:{pad} !important}}
[data-testid="stVerticalBlock"]{{gap:14px}}
div[data-baseweb="select"] > div, div[data-baseweb="input"] > div{{border-radius:999px !important;border:3px solid {LINE} !important;background:#FFFFFF !important;min-height:44px}}
.stButton button, .stDownloadButton button{{font-family:inherit;font-weight:800;border:none;border-radius:999px;min-height:42px;padding:0 18px;
  background:{OAK};color:#FFFFFF;box-shadow:0 3px 0 {OAKD}}}
.stButton button p, .stDownloadButton button p{{color:#FFFFFF !important;font-weight:800}}
.stButton button:hover, .stDownloadButton button:hover{{background:{OAKD};border:none;color:#FFFFFF}}
.stButton button[kind="secondary"]{{background:#FFFFFF;box-shadow:none;border:3px solid {LINE}}}
.stButton button[kind="secondary"] p{{color:{INK} !important}}
label p{{font-weight:700;color:{MUT}}}
</style>""", unsafe_allow_html=True)


def sidebar(active, badge):
    aside = re.search(r"<aside.*?</aside>", mock(active), re.S).group(0)
    links = iter(NAV_ORDER)
    aside = re.sub(r'href="#"', lambda m: f'href="?page={next(links)}"', aside)
    if badge:
        aside = re.sub(r'(<span style="flex: 1">Alerts</span><span[^>]*>)\d+(</span>)', rf"\g<1>{badge}\2", aside)
    else:
        aside = re.sub(r'(<span style="flex: 1">Alerts</span>)<span[^>]*>\d+</span>', r"\1", aside)
    show(f'<div style="position:fixed;left:0;top:0;bottom:0;width:240px;z-index:50;display:flex">{aside}</div>')


def heading(title, sub):
    show(
        f'<div style="font-family:Nunito,sans-serif"><h1 style="margin:0;font-family:\'Alfa Slab One\',serif;font-weight:400;font-size:34px;color:{INK}">{title}</h1>'
        f'<p style="margin:4px 0 0;font-size:16px;color:{MUT}">{sub}</p></div>')


def card_row(items, cols=3):
    return f'<div style="display:grid;grid-template-columns:repeat({cols},1fr);gap:14px;font-family:Nunito,sans-serif">{"".join(items)}</div>'


def pill(text, good):
    c, bg = (GRN, "#E6F2E8") if good else (RED, "#FBE9E7")
    return (f'<span style="display:inline-flex;align-items:center;gap:4px;font-size:13px;font-weight:800;color:{c};'
            f'background:{bg};border-radius:999px;padding:2px 9px">{text}</span>')


# ---------------------------------------------------------------------------
# charts (inline svg / div bars in the mockup's style)
# ---------------------------------------------------------------------------
def line_chart(months, series, forecast=None, w=900, h=300):
    """series: {name: (values, colour)}; forecast: (values for the next months, colour) drawn dashed from the last point."""
    n_fc = len(forecast[0]) if forecast else 0
    n = len(months) + n_fc
    top = max([max(v) for v, _ in series.values()] + (list(forecast[0]) if forecast else []) + [1]) * 1.1
    pl, pr, pt, pb = 60, 16, 14, 34
    x = lambda i: pl + (w - pl - pr) * i / max(n - 1, 1)
    y = lambda v: pt + (h - pt - pb) * (1 - v / top)
    out = [f'<svg viewBox="0 0 {w} {h}" width="100%" style="display:block;margin-top:10px" role="img">']
    for k in range(5):
        v = top * k / 4
        out.append(f'<line x1="{pl}" x2="{w - pr}" y1="{y(v):.1f}" y2="{y(v):.1f}" stroke="#EEF0F2" stroke-width="2"/>'
                   f'<text x="{pl - 8}" y="{y(v) + 4:.1f}" text-anchor="end" font-size="12" fill="{MUT}" font-family="Nunito">{money(v)}</text>')
    labels = list(months) + [f"{m} (est.)" for m in (forecast[2] if forecast else [])]
    step = max(1, len(labels) // 8)
    for i, lab in enumerate(labels):
        if i % step == 0:
            out.append(f'<text x="{x(i):.1f}" y="{h - 10}" text-anchor="middle" font-size="12" fill="{MUT}" font-family="Nunito">{lab.replace(" (est.)", "*")}</text>')
    for name, (vals, colour) in series.items():
        pts = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(vals))
        out.append(f'<polyline points="{pts}" fill="none" stroke="{colour}" stroke-width="4" stroke-linejoin="round" stroke-linecap="round"/>')
    if forecast:
        base = list(series.values())[0][0][-1]
        pts = " ".join(f"{x(len(months) - 1 + i):.1f},{y(v):.1f}" for i, v in enumerate([base] + list(forecast[0])))
        out.append(f'<polyline points="{pts}" fill="none" stroke="{forecast[1]}" stroke-width="4" stroke-dasharray="8 8" stroke-linecap="round"/>')
    out.append("</svg>")
    return "".join(out)


def bars(labels, values, fmt, highlight=0):
    top = max(values) or 1
    rows = []
    for i, (lab, v) in enumerate(zip(labels, values)):
        hot = i == highlight
        rows.append(
            f'<div style="display:grid;grid-template-columns:130px 1fr 70px;gap:10px;align-items:center;font-size:14px;padding:5px 0">'
            f'<span style="font-weight:{800 if hot else 600};color:{OAKD if hot else INK};overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{E(str(lab))}</span>'
            f'<span style="display:block;height:12px;border-radius:999px;background:#EEF0F2"><span style="display:block;height:12px;width:{max(v / top * 100, 2):.0f}%;border-radius:999px;background:{"#D9692B" if hot else "#C9CDD2"}"></span></span>'
            f'<span style="text-align:right;font-weight:800;color:{OAKD if hot else INK}">{fmt(v)}</span></div>')
    return "".join(rows)


def trend_forecast(values, ahead=3, last=6):
    """Straight line through the last `last` points, extended `ahead` points."""
    v = np.array(values[-last:], dtype=float)
    k = np.polyfit(np.arange(len(v)), v, 1)
    return [max(float(np.polyval(k, len(v) - 1 + i)), 0) for i in range(1, ahead + 1)]


def month_labels(periods):
    return [p.strftime("%b %y") for p in periods]


# ---------------------------------------------------------------------------
# 1. Welcome
# ---------------------------------------------------------------------------
def welcome():
    inject_css(full_bleed=True)
    page = mock("welcome")
    body = page.split("<body>")[1].split("</body>")[0]
    body = re.sub(r"<button style=\"([^\"]*)\">Let's go →</button>",
                  r'<a href="?page=overview" style="\1;text-decoration:none;display:inline-flex;align-items:center;justify-content:center;box-sizing:border-box">Let\'s go →</a>',
                  body)
    show(f"<style>{mock_css('welcome')}</style>{body}")


# ---------------------------------------------------------------------------
# 2. Overview
# ---------------------------------------------------------------------------
def overview():
    df = orders()
    heading("Overview", "The big picture. Pick a region and a time range; everything updates.")
    c1, c2, c3 = st.columns([1, 1.3, 2])
    region = c1.selectbox("Region", ["All regions"] + sorted(df["region"].unique()))
    rng = c2.segmented_control("Time range", ["3M", "6M", "12M", "All"], default="6M") or "6M"
    latest = df["order_date"].max()
    c3.markdown(f"<div style='padding-top:30px;text-align:right;font-weight:700;color:{MUT}'>Latest data: {latest:%b %d, %Y}</div>", unsafe_allow_html=True)

    if region != "All regions":
        df = df[df["region"] == region]
    months = {"3M": 3, "6M": 6, "12M": 12, "All": None}[rng]
    if months:
        start = latest - pd.DateOffset(months=months)
        cur = df[df["order_date"] > start]
        prev = df[(df["order_date"] <= start) & (df["order_date"] > start - pd.DateOffset(months=months))]
    else:
        cur, prev = df, df.iloc[0:0]

    def stats(d):
        known = d[d["margin"].notna()]
        return {"rev": d["net"].sum(), "cash": d.loc[d["paid"] == "Yes", "net"].sum(),
                "margin": known["margin"].sum() / known["amount"].sum() * 100 if len(known) else 0}
    S, P = stats(cur), stats(prev)

    def tile(label, value, delta, good, note):
        d = pill(delta, good) if delta else ""
        return (f'<div style="{CARD};padding:20px 22px"><div style="font-size:14px;font-weight:700;color:{MUT}">{label}</div>'
                f'<div style="font-size:34px;font-weight:700;margin:4px 0 6px;white-space:nowrap">{value}</div>{d}'
                f'<div style="font-size:13px;color:{MUT};margin-top:8px">{note}</div></div>')

    pct = lambda k: (S[k] / P[k] - 1) * 100 if P[k] else None
    tiles = [
        tile("Net revenue", money(S["rev"]), f"{'▲' if (pct('rev') or 0) >= 0 else '▼'} {abs(pct('rev')):.0f}% vs previous period" if pct("rev") is not None else "", (pct("rev") or 0) >= 0,
             "Money from sales after discounts and returns"),
        tile("Gross margin", f"{S['margin']:.1f}%", f"{'▲' if S['margin'] >= P['margin'] else '▼'} {abs(S['margin'] - P['margin']):.1f} pts vs previous period" if P["margin"] else "",
             S["margin"] >= P["margin"], "Share of each sale kept as profit"),
        tile("Cash collected", money(S["cash"]), f"{'▲' if (pct('cash') or 0) >= 0 else '▼'} {abs(pct('cash')):.0f}% vs previous period" if pct("cash") is not None else "", (pct("cash") or 0) >= 0,
             "Money that actually came in"),
    ]
    show(card_row(tiles))

    # revenue vs cash, month by month, with a 3-month estimate
    m = df.assign(m=df["order_date"].dt.to_period("M")).groupby("m").agg(rev=("net", "sum"))
    m["cash"] = df[df["paid"] == "Yes"].assign(m=lambda d: d["order_date"].dt.to_period("M")).groupby("m")["net"].sum()
    m = m.fillna(0)
    shown = m.tail(months) if months else m
    shown = shown if len(shown) >= 4 else m.tail(4)
    fc_idx = [(m.index[-1] + k).strftime("%b %y") for k in (1, 2, 3)]
    fc = trend_forecast(m["rev"].tolist())
    gap = 1 - shown["cash"].sum() / shown["rev"].sum() if shown["rev"].sum() else 0
    prev_gap = 1 - m["cash"].iloc[:-len(shown)].tail(len(shown)).sum() / m["rev"].iloc[:-len(shown)].tail(len(shown)).sum() if len(m) > len(shown) * 1.5 else gap
    chart = line_chart(month_labels(shown.index), {"Revenue": (shown["rev"].tolist(), GRN), "Cash": (shown["cash"].tolist(), "#9AA0A8")},
                       (fc, "#565B62", fc_idx))
    legend = (f'<span><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:{GRN}"></span> Revenue</span>'
              f'<span><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#9AA0A8"></span> Cash collected</span>'
              f'<span><span style="display:inline-block;width:18px;border-top:3px dashed {MUT};vertical-align:middle"></span> Forecast</span>')
    show(
        f'<div style="{CARD};padding:22px 24px;font-family:Nunito,sans-serif"><div style="display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap">'
        f'<div><div style="font-size:14px;font-weight:700;color:{MUT}">Revenue vs. cash collected</div>'
        f'<div style="font-size:30px;font-weight:700">The gap is {"growing" if gap > prev_gap else "shrinking"} {pill(f"{gap:.0%} not collected yet", gap <= prev_gap)}</div></div>'
        f'<div style="display:flex;gap:16px;font-size:13px;font-weight:700;color:{MUT};flex-wrap:wrap">{legend}</div></div>{chart}'
        f'<div style="font-size:14px;color:{MUT};margin-top:6px">The space between the lines is money sold but not collected yet. The dashed part (*) is a 3-month estimate. '
        f'See <a href="?page=insights" style="font-weight:800;color:{OAKD}">Insights</a> for why.</div></div>')


# ---------------------------------------------------------------------------
# 3. Data
# ---------------------------------------------------------------------------
COLS = [("order_id", "Order ID", "left"), ("order_date", "Date", "left"), ("customer_id", "Customer", "left"), ("region", "Region", "left"),
        ("rep", "Rep", "left"), ("product", "Product", "left"), ("quantity", "Qty", "right"), ("unit_price", "Unit price", "right"),
        ("discount", "Discount", "right"), ("amount", "Amount", "right"), ("paid", "Paid", "left")]


def data_page():
    df = orders()
    heading("Data", "The raw, cleaned orders. Sort, filter and search everything.")
    q, r, rp, pr, pd_, so = st.columns([2.2, 1, 1, 1.4, 0.8, 1.2])
    text = q.text_input("Search", placeholder="Search order, customer, product…")
    region = r.selectbox("Region", ["All"] + sorted(df["region"].unique()))
    rep = rp.selectbox("Rep", ["All"] + sorted(df["rep"].unique()))
    product = pr.selectbox("Product", ["All"] + sorted(df["product"].unique()))
    paid = pd_.selectbox("Paid", ["All", "Yes", "No"])
    sort = so.selectbox("Sort by", [c[1] for c in COLS], index=[c[1] for c in COLS].index("Amount"))
    desc = st.toggle("High → low", value=True)

    if region != "All":
        df = df[df["region"] == region]
    if rep != "All":
        df = df[df["rep"] == rep]
    if product != "All":
        df = df[df["product"] == product]
    if paid != "All":
        df = df[df["paid"] == paid]
    if text:
        blob = df[["order_id", "customer_id", "product", "region", "rep"]].astype(str).agg(" ".join, axis=1).str.lower()
        df = df[blob.str.contains(text.lower(), regex=False)]
    key = next(c[0] for c in COLS if c[1] == sort)
    df = df.sort_values(key, ascending=not desc)

    LIMIT = 200
    head = "".join(
        f'<th style="text-align:{al};padding:12px 14px;font-size:12px;font-weight:800;letter-spacing:1px;text-transform:uppercase;color:{OAKD if name == sort else MUT};white-space:nowrap">'
        f'{name}{" ▼" if name == sort and desc else " ▲" if name == sort else ""}</th>' for _, name, al in COLS)
    body = []
    for r_ in df.head(LIMIT).itertuples():
        cells = {"order_id": r_.order_id, "order_date": f"{r_.order_date:%Y-%m-%d}", "customer_id": r_.customer_id, "region": r_.region,
                 "rep": r_.rep, "product": r_.product, "quantity": f"{r_.quantity:,}", "unit_price": f"${r_.unit_price:,.2f}",
                 "discount": f"{r_.discount:.1%}", "amount": f"${r_.amount:,.2f}", "paid": r_.paid}
        tds = ""
        for k, _, al in COLS:
            col = (GRN if r_.paid == "Yes" else RED) if k == "paid" else INK
            tds += (f'<td style="padding:11px 14px;border-top:2px solid #EEF0F2;white-space:nowrap;text-align:{al};'
                    f'font-weight:{800 if k == "amount" else 400};color:{col}">{E(str(cells[k]))}</td>')
        body.append(f"<tr>{tds}</tr>")
    empty = f'<tr><td colspan="11" style="padding:24px;text-align:center;color:{MUT}">No orders match these filters.</td></tr>' if not body else ""
    n = len(df)
    shown = f" · showing the first {LIMIT}" if n > LIMIT else ""
    show(
        f'<div style="font-family:Nunito,sans-serif"><div style="font-size:14px;color:{MUT};font-weight:700;margin-bottom:10px">{n:,} orders · sorted by '
        f'<b style="color:{INK}">{sort}, {"high → low" if desc else "low → high"}</b>{shown}</div>'
        f'<div style="{CARD};padding:0;overflow:auto"><table style="width:100%;border-collapse:collapse;font-size:15px"><thead style="background:#F4F5F7"><tr>{head}</tr></thead>'
        f'<tbody>{"".join(body)}{empty}</tbody></table></div></div>')
    st.download_button("Download these rows (CSV)", df.drop(columns=["net"]).to_csv(index=False), "chrome_oak_orders.csv", "text/csv")


# ---------------------------------------------------------------------------
# 4. Insights (Chrome)
# ---------------------------------------------------------------------------
BAR_SOURCE = {  # alert id -> (label column, value column, chart title, formatter)
    "overdue": ("customer", "owes", "Biggest overdue customers", lambda v: money(v)),
    "discount": ("Sales rep", "Avg discount", "Average discount by rep (over the cap)", lambda v: f"{v:.0f}%"),
    "returns": ("Product", "Refund rate", "Refund rate by product", lambda v: f"{v:.0f}%"),
}


def insights(days):
    df = orders()
    heading("Insights", "Chrome’s analysis: where things are heading, then every problem ranked by how much money it costs.")
    issues = sorted([i for i in analysis.detect_issues(days) if len(i["rows"])], key=lambda i: i["cost"])
    total = sum(i["cost"] for i in issues)

    # forecast box
    m = df.assign(m=df["order_date"].dt.to_period("M")).groupby("m").agg(rev=("net", "sum"), unpaid=("net", lambda s: s[df.loc[s.index, "paid"] == "No"].sum()))
    known = df[df["margin"].notna()].assign(m=lambda d: d["order_date"].dt.to_period("M")).groupby("m").apply(lambda d: d["margin"].sum() / d["amount"].sum() * 100, include_groups=False)
    f_rev, f_unpaid, f_margin = trend_forecast(m["rev"].tolist())[-1], trend_forecast(m["unpaid"].tolist())[-1], trend_forecast(known.tolist())[-1]
    now_rev, now_unpaid, now_margin = m["rev"].iloc[-1], m["unpaid"].iloc[-1], known.iloc[-1]
    arrow = lambda a, b: "▲" if a > b else "▼"
    box = lambda label, val, bad: (f'<div style="background:#F4F5F7;border-radius:16px;padding:12px 14px"><div style="font-size:13px;font-weight:700;color:{MUT}">{label}</div>'
                                    f'<div style="font-size:22px;font-weight:800;color:{RED if bad else GRN}">{val}</div></div>')
    boxes = (box("Unpaid orders per month", money(f_unpaid) + " " + arrow(f_unpaid, now_unpaid), f_unpaid > now_unpaid)
             + box("Gross margin", f"{f_margin:.1f}% " + arrow(f_margin, now_margin), f_margin < now_margin)
             + box("Revenue per month", money(f_rev) + " " + arrow(f_rev, now_rev), f_rev < now_rev))
    fc_chart = line_chart(month_labels(m.index[-6:]), {"Revenue": (m["rev"].tail(6).tolist(), GRN), "Unpaid": (m["unpaid"].tail(6).tolist(), RED)},
                          (trend_forecast(m["rev"].tolist()), "#565B62", [(m.index[-1] + k).strftime("%b %y") for k in (1, 2, 3)]), h=240)
    forecast = (
        f'<div style="{CARD}"><div style="display:flex;align-items:center;gap:10px"><span style="font-size:12px;font-weight:800;letter-spacing:1px;text-transform:uppercase;color:#FFFFFF;background:{INK};border-radius:999px;padding:3px 12px">Forecast</span>'
        f'<div style="font-size:19px;font-weight:800">If nothing changes, in 3 months…</div></div>'
        f'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:14px 0">'
        f'{boxes}</div>'
        f'<details style="border-top:2px solid #EEF0F2;padding-top:10px"><summary style="cursor:pointer;font-size:14px;font-weight:800;color:{OAKD}">Show the chart: next 3 months</summary>'
        f'<div style="margin-top:10px;background:#F4F5F7;border-radius:16px;padding:14px 16px">{fc_chart}</div></details>'
        f'<div style="font-size:13px;color:{MUT};background:#F4F5F7;border-radius:12px;padding:8px 12px;margin-top:12px"><b style="color:{INK}">How we got this:</b> '
        f'a straight trend line through the last 6 months, extended 3 months ahead. It assumes things keep going the way they are.</div></div>')

    # one card per problem
    cards = []
    for n, i in enumerate(issues, 1):
        lab, val, title, fmt = BAR_SOURCE[i["id"]]
        rows = i["rows"].head(6)
        chart = bars(rows[lab].tolist(), [number(v) for v in rows[val]], fmt)
        first = n == 1
        cards.append(
            f'<div style="{CARD};{"border-color:#F2C4BE;" if first else ""}">'
            f'<div style="display:grid;grid-template-columns:44px 1fr auto;gap:16px;align-items:start">'
            f'<span style="width:44px;height:44px;border-radius:50%;background:{"#FBE9E7" if first else "#F4F5F7"};color:{RED if first else INK};font-family:\'Alfa Slab One\',serif;font-size:20px;display:flex;align-items:center;justify-content:center">{n}</span>'
            f'<div><div style="font-size:19px;font-weight:800">{E(i["name"].capitalize())}</div>'
            f'<p style="margin:6px 0 8px;font-size:15px;line-height:1.55;color:{MUT}">{E(i["what"])}</p>'
            f'<div style="font-size:13px;color:{MUT};background:#F4F5F7;border-radius:12px;padding:8px 12px"><b style="color:{INK}">How we got this:</b> {E(i["how"])}</div>'
            f'<div style="font-size:13px;font-weight:700;color:{MUT};margin-top:8px">Found: {E(i["found"])} · Rule: {E(i["rule"])}</div></div>'
            f'<div style="text-align:right"><div style="font-size:12px;font-weight:800;letter-spacing:1px;text-transform:uppercase;color:{MUT}">Cost</div>'
            f'<div style="font-family:\'Alfa Slab One\',serif;font-size:30px;color:{RED}">{money(i["cost"])}</div>'
            f'<a href="?page=alerts" style="font-size:14px;font-weight:800;text-decoration:none;color:{OAKD}">Oak’s fix →</a></div></div>'
            f'<details {"open" if first else ""} style="margin:14px 0 0 60px;border-top:2px solid #EEF0F2;padding-top:10px"><summary style="cursor:pointer;font-size:14px;font-weight:800;color:{OAKD}">Show the chart: {title}</summary>'
            f'<div style="margin-top:10px;background:#F4F5F7;border-radius:16px;padding:14px 16px">{chart}</div></details></div>')

    # the two bar charts + headline from analysis.py
    extra = "".join(
        f'<div style="{CARD}"><div style="font-size:19px;font-weight:800">{E(c["title"])}</div><div style="font-size:14px;color:{MUT};margin:2px 0 10px">{E(c["desc"])}</div>'
        f'{bars(list(c["data"].index), [float(v) * 100 for v in c["data"].iloc[:, 0]], lambda v: f"{v:.0f}%", highlight=list(c["data"].index).index(c["highlight"]) if c["highlight"] in c["data"].index else -1)}</div>'
        for c in analysis.get_charts())
    insight_text = "".join(
        f'<div style="{CARD}"><div style="font-size:18px;font-weight:800">{E(x["title"])}</div>'
        f'<p style="margin:6px 0 0;color:{MUT};line-height:1.55">{E(x["what"])} {E(x["why"])}</p>'
        f'<p style="margin:6px 0 0;font-weight:700">Do: {E(x["todo"])}</p></div>' for x in analysis.get_insights())
    side = (
        f'<div style="position:sticky;top:20px;display:flex;flex-direction:column;gap:12px">{mascot("insights")}'
        f'<div style="background:#FFFFFF;border:3px solid {LINE};border-radius:22px;padding:16px 18px;font-size:15.5px;line-height:1.55"><div style="font-size:12px;font-weight:800;letter-spacing:1px;text-transform:uppercase;color:{MUT};margin-bottom:4px">Chrome · analyst</div>'
        f'I found <b>{len(issues)} problems</b> costing about <b style="color:{RED}">{money(total)}</b>. They’re ranked by money lost, biggest first. Click <b>Show the chart</b> on any of them to see the proof.<br><br>{E(analysis.get_focus())}</div>'
        f'<div style="{CARD};padding:14px 16px;border-radius:24px"><div style="font-size:13px;font-weight:700;color:{MUT}">Total estimated loss</div><div style="font-family:\'Alfa Slab One\',serif;font-size:34px;color:{RED}">{money(total)}</div></div></div>')
    show(
        f"<style>{mock_css('insights')}</style>"
        f'<div style="display:grid;grid-template-columns:1fr 300px;gap:18px;align-items:start;font-family:Nunito,sans-serif">'
        f'<div style="display:flex;flex-direction:column;gap:14px">{forecast}'
        f'<div style="font-size:14px;font-weight:800;letter-spacing:1px;text-transform:uppercase;color:{MUT};margin-top:6px">The problems, biggest loss first</div>{"".join(cards)}'
        f'<div style="font-size:14px;font-weight:800;letter-spacing:1px;text-transform:uppercase;color:{MUT};margin-top:6px">More from the data</div>{extra}'
        f'{insight_text}'
        f"</div>{side}</div>")


# ---------------------------------------------------------------------------
# 5. Alerts (Oak)
# ---------------------------------------------------------------------------
def alerts(days):
    heading("Alerts", "Oak’s fixes: one action per problem, in the same order as Chrome’s list.")
    log = read_log()
    issues = sorted([i for i in analysis.detect_issues(days) if len(i["rows"])], key=lambda i: i["cost"])
    recover = -sum(i["cost"] for i in issues)

    cards = []
    for n, i in enumerate(issues, 1):
        status = handled(i["id"], log)
        done = "".join(
            f'<div style="display:flex;align-items:center;gap:8px;font-size:15px;margin-top:6px"><span style="color:{GRN};font-weight:800">✓</span> {E(a)}</div>' for a in i["actions"])
        tag = f'<span style="font-size:12px;font-weight:800;color:{GRN};background:#E6F2E8;border-radius:999px;padding:3px 10px;margin-left:8px">{status}</span>' if status else ""
        cards.append(
            f'<div style="background:#FFFFFF;border:3px solid #E6CDAE;border-radius:24px;padding:18px 20px;display:grid;grid-template-columns:1fr 1fr;gap:18px;align-items:start;{"opacity:.6;" if status else ""}">'
            f'<div><div style="display:flex;align-items:center;gap:8px"><span style="font-size:12px;font-weight:800;color:{RED};background:#FBE9E7;border-radius:999px;padding:3px 10px">{money(i["cost"])}</span>'
            f'<span style="font-size:13px;font-weight:700;color:{MUT}">#{n}</span>{tag}</div>'
            f'<div style="font-size:18px;font-weight:800;margin-top:6px">{E(i["name"].capitalize())} · {len(i["rows"])} found</div>'
            f'<div style="font-size:12px;font-weight:800;letter-spacing:1px;text-transform:uppercase;color:{OAK};margin-top:10px">Oak’s fix</div>'
            f'<p style="margin:2px 0 0;font-size:15px;line-height:1.5">{E(i["fix"])}</p></div>'
            f'<div><div style="font-size:12px;font-weight:800;letter-spacing:1px;text-transform:uppercase;color:{GRN}">Done automatically</div>{done}'
            f'<div style="font-size:13px;color:{MUT};margin-top:8px">Sent to: <b style="color:{INK}">{E(i["notify"])}</b></div></div></div>')

    side = (
        f'<div style="position:sticky;top:20px;display:flex;flex-direction:column;gap:12px">{mascot("alerts")}'
        f'<div style="background:#FFFBF6;border:3px solid #E6CDAE;border-radius:22px;padding:16px 18px;font-size:15.5px;line-height:1.55"><div style="font-size:12px;font-weight:800;letter-spacing:1px;text-transform:uppercase;color:{OAK};margin-bottom:4px">Oak · advisor</div>'
        f'Same order as Chrome’s list. For each problem I’ve <b>already taken the first step</b>. You just approve and send.</div>'
        f'<div style="{CARD};padding:14px 16px"><div style="font-size:13px;font-weight:700;color:{MUT}">Money we can recover</div><div style="font-family:\'Alfa Slab One\',serif;font-size:34px;color:{GRN}">{money(recover, sign=True)}</div><div style="font-size:13px;color:{MUT}">if every fix works</div></div></div>')

    left, right = st.columns([3.2, 1])
    with left:
        st.slider("Flag invoices more than N days late", 0, 90, days, 5, key="days")
        for i, card in zip(issues, cards):
            show(f"<style>{mock_css('alerts')}</style>{card}")
            if not handled(i["id"], log):
                b1, b2, _ = st.columns([1.3, 1, 3])
                if b1.button(i["button"], key=f"send_{i['id']}"):
                    write_log([(f"{len(i['rows'])} found: {i['name']} ({i['rule']})", "Rule", "Chrome", i["id"])]
                              + [(a, "Action", "Oak", i["id"]) for a in i["actions"]]
                              + [(f"{i['notify']} notified", "Notify", "Oak", i["id"])])
                    st.rerun()
                if b2.button("Dismiss", key=f"dismiss_{i['id']}", type="secondary"):
                    write_log([(f"Alert dismissed by user: {i['name']}", "Dismissed", "You", i["id"])])
                    st.rerun()
        if not issues:
            st.success("All clear. Nothing needs action right now.")
    show(side, right)


# ---------------------------------------------------------------------------
# 6. Action log
# ---------------------------------------------------------------------------
TYPE_STYLE = {"Rule": (MUT, "#F4F5F7"), "Action": (OAKD, "#F5E9DA"), "Notify": (GRN, "#E6F2E8"), "Dismissed": (RED, "#FBE9E7")}


def action_log():
    heading("Action log", "Everything Chrome detected and Oak did, so a person can check it.")
    log = read_log()
    kind = st.segmented_control("Show", ["All", "Rule", "Action", "Notify", "Dismissed"], default="All") or "All"
    n = lambda t: int((log["type"] == t).sum())
    tile = lambda label, v: f'<div style="{CARD};padding:14px 18px"><div style="font-size:13px;font-weight:700;color:{MUT}">{label}</div><div style="font-size:26px;font-weight:700">{v}</div></div>'
    show(card_row([tile("Rules triggered", n("Rule")), tile("Actions taken", n("Action")), tile("People notified", n("Notify")), tile("Dismissed", n("Dismissed"))], 4))
    shown = log if kind == "All" else log[log["type"] == kind]
    rows = []
    for k, r_ in enumerate(shown.iloc[::-1].itertuples()):
        c, bg = TYPE_STYLE.get(r_.type, (MUT, "#F4F5F7"))
        rows.append(
            f'<tr style="background:{"#FFFFFF" if k % 2 == 0 else "#FBF8F4"}"><td style="padding:12px 16px;font-weight:800;color:{MUT};white-space:nowrap">{E(r_.when)}</td>'
            f'<td style="padding:12px 16px">{E(r_.what)}</td><td style="padding:12px 16px"><span style="font-size:12px;font-weight:800;color:{c};background:{bg};border-radius:999px;padding:3px 10px">{E(r_.type)}</span></td>'
            f'<td style="padding:12px 16px;font-weight:800">{E(r_.by)}</td></tr>')
    empty = f'<tr><td colspan="4" style="padding:28px;text-align:center;color:{MUT}">Nothing here yet. Send or dismiss an alert on the Alerts page and it shows up here.</td></tr>' if not rows else ""
    show(
        f'<div style="{CARD};padding:0;overflow:hidden;font-family:Nunito,sans-serif"><table style="width:100%;border-collapse:collapse;font-size:15px"><thead><tr style="background:#F4F5F7;text-align:left;font-size:12px;letter-spacing:1px;text-transform:uppercase;color:{MUT}">'
        f'<th style="padding:12px 16px">When</th><th style="padding:12px 16px">What happened</th><th style="padding:12px 16px">Type</th><th style="padding:12px 16px">By</th></tr></thead>'
        f'<tbody>{"".join(rows)}{empty}</tbody></table></div>')
    st.download_button("Download log (CSV)", log.to_csv(index=False), "action_log.csv", "text/csv")
