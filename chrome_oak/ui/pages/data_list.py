"""Data list: every cleaned order, filterable and sortable, with a download."""

import json

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from chrome_oak.analysis import get_customers, get_orders, get_returns
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
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,500;9..40,600;9..40,700&display=swap" rel="stylesheet">
<style>
body{{margin:0;font-family:'DM Sans',sans-serif;color:#2A2420;background:transparent}}
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


def _pick(df, col, label, key, container):
    """A multiselect filter on one column. Nothing picked = keep everything."""
    options = sorted(df[col].dropna().astype(str).unique())
    chosen = container.multiselect(label, options, placeholder=f"All {label.lower()}", key=key)
    return df[df[col].astype(str).isin(chosen)] if chosen else df


def _date_range(df, col, label, key, container):
    lo, hi = df[col].min(), df[col].max()
    picked = container.date_input(label, (lo, hi), min_value=lo, max_value=hi, key=key)
    if isinstance(picked, (tuple, list)) and len(picked) == 2:
        df = df[(df[col] >= picked[0]) & (df[col] <= picked[1])]
    return df


def _show(df, total, name):
    st.caption(f"{len(df):,} of {total:,} rows · click a column title to sort, click again to flip")
    sortable_table(df)
    st.download_button(f"Download these {name} (CSV)", df.to_csv(index=False), f"chrome_oak_{name}.csv", "text/csv",
                       key=f"dl_{name}")


def _orders_tab():
    df = get_orders()
    c = st.columns(4)
    out = _date_range(df, "order_date", "Order date", "o_date", c[0])
    out = _pick(out, "region", "Regions", "o_region", c[1])
    out = _pick(out, "segment", "Segments", "o_segment", c[2])
    out = _pick(out, "rep", "Reps", "o_rep", c[3])
    c = st.columns(4)
    out = _pick(out, "category", "Categories", "o_category", c[0])
    out = _pick(out, "product", "Products", "o_product", c[1])
    out = _pick(out, "sales_channel", "Channels", "o_channel", c[2])
    paid = c[3].selectbox("Payment", ["All", "Paid", "Unpaid"], key="o_paid")
    if paid != "All":
        out = out[out["payment_date"].isna() == (paid == "Unpaid")]
    _show(out, len(df), "orders")


def _customers_tab():
    df = get_customers()
    c = st.columns(4)
    out = _pick(df, "segment", "Segments", "c_segment", c[0])
    out = _pick(out, "region", "Regions", "c_region", c[1])
    out = _pick(out, "payment_terms", "Payment terms", "c_terms", c[2])
    out = _pick(out, "account_rep", "Account reps", "c_rep", c[3])
    if st.checkbox("Only customers who still owe money", key="c_owes"):
        out = out[out["unpaid"] > 0]
    _show(out, len(df), "customers")


def _returns_tab():
    df = get_returns()
    c = st.columns(4)
    out = _date_range(df, "return_date", "Return date", "r_date", c[0])
    out = _pick(out, "reason", "Reasons", "r_reason", c[1])
    out = _pick(out, "category", "Categories", "r_category", c[2])
    out = _pick(out, "product", "Products", "r_product", c[3])
    out = _pick(out, "region", "Regions", "r_region", st.columns(4)[0])
    _show(out, len(df), "returns")


def render(ctx):
    inject_page_css(__file__)
    page_head("Data list", "The three cleaned tables. Filter each one, sort by any column, and download what you see.")
    orders_tab, customers_tab, returns_tab = st.tabs(["Orders", "Customers", "Returns"])
    with orders_tab:
        _orders_tab()
    with customers_tab:
        _customers_tab()
    with returns_tab:
        _returns_tab()
