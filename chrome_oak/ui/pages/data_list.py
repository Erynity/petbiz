"""Data list: every cleaned order, filterable and sortable, with a download."""

import json

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from chrome_oak.analysis import get_data
from chrome_oak.ui.components import page_head, pretty
from chrome_oak.ui.theme import inject_page_css


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


def render(ctx):
    inject_page_css(__file__)
    df = get_data().copy()
    page_head("Data list", f"Every cleaned order, {len(df):,} rows. Click a column title to sort; click again to flip.")
    c1, c2 = st.columns([2, 2])
    regions = sorted(df["region"].dropna().astype(str).unique())
    pick = c1.multiselect("Region", regions, placeholder="All regions")
    if pick:
        df = df[df["region"].astype(str).isin(pick)]
    q = c2.text_input("Search", placeholder="Customer, product, rep…")
    if q:
        df = df[df.astype(str).apply(lambda r: r.str.contains(q, case=False, regex=False)).any(axis=1)]
    sortable_table(df)
    st.download_button("Download these rows (CSV)", df.to_csv(index=False), "chrome_oak_orders.csv", "text/csv")
