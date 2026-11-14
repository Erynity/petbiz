"""Reusable building blocks for the pages: tables, page headings, sidebar, chat bubbles."""

import html as _html
import json

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from chrome_oak.ui.mascots import mascot_svg
from chrome_oak.ui.theme import LEAF, MUT, OAK, icon

# (query-string id, icon, label) for every page in the sidebar, in order
PAGES = [
    ("overview", "home", "Overview"),
    ("data", "list", "Data list"),
    ("insights", "chart", "Insights"),
    ("alerts", "bell", "Alerts"),
    ("log", "log", "Action log"),
]


def html(s):
    st.markdown(s, unsafe_allow_html=True)


def esc(x):
    return _html.escape(str(x))


def pretty(col, v):
    """Easy-to-read cell values: $ for money, % for rates, clean dates."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "—"
    c = str(col).lower()
    try:
        if any(k in c for k in ("price", "amount", "revenue", "cost", "owe", "total", "balance", "limit")) and not isinstance(v, str):
            return f"${float(v):,.2f}"
        if any(k in c for k in ("discount", "margin", "rate", "pct")) and not isinstance(v, str):
            return f"{float(v) * 100:.1f}%" if abs(float(v)) <= 1.5 else f"{float(v):.1f}%"
        if isinstance(v, pd.Timestamp):
            return v.strftime("%Y-%m-%d")
        if isinstance(v, float):
            return f"{v:,.0f}" if v.is_integer() else f"{v:,.2f}"
    except (TypeError, ValueError):
        pass
    return str(v)



def sortable_table(df, height=620, max_rows=300):
    """Data list table: click a column title to sort A→Z / low→high, click again to flip.
    Sorting happens in the browser, so the page never reloads."""
    cols = list(df.columns)
    raw = df.astype(object).where(df.notna(), None)
    rows = [[(v.isoformat() if hasattr(v, "isoformat") else v) for v in r] for r in raw.values.tolist()]
    shown = [[pretty(c, v) for c, v in zip(cols, r)] for r in raw.values.tolist()]
    nums = [pd.api.types.is_numeric_dtype(df[c]) for c in cols]
    payload = json.dumps({"cols": [str(c).replace("_", " ") for c in cols], "raw": rows, "shown": shown, "nums": nums},
                         default=str)
    components.html(f"""
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@600;700;800&display=swap" rel="stylesheet">
<style>
body{{margin:0;font-family:'Nunito',sans-serif;color:#2A2420;background:transparent}}
.wrap{{background:#FFFFFF;border:3px solid #DDE0E4;border-radius:18px;overflow:auto;height:{height - 40}px}}
table{{width:100%;border-collapse:collapse;font-size:15px}}
th{{position:sticky;top:0;background:#F4F5F7;text-align:left;padding:0;z-index:1}}
th button{{all:unset;cursor:pointer;display:flex;gap:6px;align-items:center;width:100%;box-sizing:border-box;padding:12px 14px;
  font-size:12px;font-weight:800;letter-spacing:1px;text-transform:uppercase;color:#565B62;white-space:nowrap}}
th button:hover,th button:focus-visible{{color:#8B5E3C;background:#ECEEF1}}
th button span{{color:#8B5E3C;font-size:13px}}
td{{padding:11px 14px;border-top:2px solid #EEF0F2;white-space:nowrap}}
td.num{{text-align:right;font-variant-numeric:tabular-nums}}
tr:nth-child(even) td{{background:#FBF8F4}}
.note{{font-size:13px;color:#565B62;margin:8px 4px 0;font-weight:600}}
</style>
<div class="wrap"><table><thead><tr id="h"></tr></thead><tbody id="b"></tbody></table></div>
<div class="note" id="n"></div>
<script>
const D = {payload};
const MAX = {max_rows};
let order = D.raw.map((_, i) => i), col = -1, asc = true;
function draw() {{
  document.getElementById('h').innerHTML = D.cols.map((c, i) =>
    `<th><button onclick="sortBy(${{i}})" aria-label="Sort by ${{c}}">${{c}} <span>${{i === col ? (asc ? '▲' : '▼') : '↕'}}</span></button></th>`).join('');
  document.getElementById('b').innerHTML = order.slice(0, MAX).map(r =>
    '<tr>' + D.shown[r].map((v, i) => `<td class="${{D.nums[i] ? 'num' : ''}}">${{String(v).replace(/</g, '&lt;')}}</td>`).join('') + '</tr>').join('');
  document.getElementById('n').textContent = `Showing ${{Math.min(MAX, order.length)}} of ${{order.length}} rows` +
    (col >= 0 ? ` · sorted by ${{D.cols[col]}} (${{asc ? (D.nums[col] ? 'low → high' : 'A → Z') : (D.nums[col] ? 'high → low' : 'Z → A')}})` : ' · click a column title to sort');
}}
function sortBy(i) {{
  asc = (col === i) ? !asc : true; col = i;
  order.sort((x, y) => {{
    let a = D.raw[x][i], b = D.raw[y][i];
    if (a === null) return 1; if (b === null) return -1;
    const r = D.nums[i] ? a - b : String(a).localeCompare(String(b), undefined, {{numeric: true}});
    return asc ? r : -r;
  }});
  draw();
}}
draw();
</script>""", height=height, scrolling=False)



def table(df, sort_links=None, highlight=None):
    """Plain, styled HTML table. sort_links: {column: url} makes headers clickable.
    highlight: a value in the first column whose row is shaded."""
    def th(c):
        label = str(c).replace("_", " ")
        if sort_links and c in sort_links:
            url, arrow = sort_links[c]
            return f'<th><a class="sorth" href="{url}" target="_self">{label} <span>{arrow}</span></a></th>'
        return f"<th>{label}</th>"
    head = "".join(th(c) for c in df.columns)
    rows = []
    for _, r in df.iterrows():
        hl = highlight is not None and str(r.iloc[0]) == str(highlight)
        cells = "".join(f'<td class="{"num" if not isinstance(v, str) else ""}">{esc(pretty(c, v))}</td>' for c, v in r.items())
        rows.append(f'<tr class="{"hl" if hl else ""}">{cells}</tr>')
    html(f'<div class="tbl"><table><thead><tr>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>')



def sidebar(active, alert_count):
    links = "".join(
        f'<a class="navi{" on" if p == active else ""}" href="?page={p}" target="_self">'
        f'{icon(ic, OAK if p == active else MUT)}<span>{label}</span>'
        + (f'<span class="badge">{alert_count}</span>' if p == "alerts" and alert_count else "") + "</a>"
        for p, ic, label in PAGES
    )
    html(f'<div class="side"><a class="home" href="?page=welcome" target="_self" title="Back to the main page">{LEAF} Chrome &amp; Oak</a>'
         f'<div class="navlbl">Workspace</div>{links}</div>')


def page_head(title, sub):
    html(f'<div class="pagehead"><div><h2>{title}</h2><p>{sub}</p></div></div>')


def section(title, desc=""):
    html(f'<div class="section"><h3>{title}</h3>' + (f"<p>{desc}</p>" if desc else "") + "</div>")


def talk(who, mood, label, text):
    """A mascot with a speech bubble. who: "chrome" (analyst) or "oak" (advisor)."""
    side = "oak" if who == "oak" else "chrome"
    return (f'<div class="talk {side}"><span class="av">{mascot_svg(who, mood, 74)}</span>'
            f'<div class="bubble"><div class="k">{label}</div>{text}</div></div>')


def insight_card(n, x):
    return (f'<div class="card"><span class="pill">Insight {n}</span>'
            f'<div style="font-size:20px;font-weight:700;margin:10px 0 4px">{esc(x["title"])}</div>'
            f'<div class="lbl">What happened</div><p>{esc(x["what"])}</p>'
            f'<div class="lbl">Why it matters</div><p>{esc(x["why"])}</p>'
            f'<div class="lbl">What to do</div><p>{esc(x["todo"])}</p></div>')
