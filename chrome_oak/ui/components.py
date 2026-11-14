"""Reusable building blocks for the pages: tables, page headings, sidebar, chat bubbles."""

import html as _html

import pandas as pd
import streamlit as st

from chrome_oak.ui.theme import LEAF, MUT, OAK, icon

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



def sidebar(pages, active, alert_count):
    """pages: list of (query-string id, icon, label), in sidebar order."""
    links = "".join(
        f'<a class="navi{" on" if p == active else ""}" href="?page={p}" target="_self">'
        f'{icon(ic, OAK if p == active else MUT)}<span>{label}</span>'
        + (f'<span class="badge">{alert_count}</span>' if p == "alerts" and alert_count else "") + "</a>"
        for p, ic, label in pages
    )
    html(f'<div class="side"><a class="home" href="?page=welcome" target="_self" title="Back to the main page">{LEAF} Chrome &amp; Oak</a>'
         f'<div class="navlbl">Workspace</div>{links}</div>')


def page_head(title, sub):
    html(f'<div class="pagehead"><div><h2>{title}</h2><p>{sub}</p></div></div>')


def section(title, desc=""):
    html(f'<div class="section"><h3>{title}</h3>' + (f"<p>{desc}</p>" if desc else "") + "</div>")
