"""Data prep: every change we made before trusting a number, and the rows we removed."""

import streamlit as st

from chrome_oak.analysis import get_prep_steps, get_removed_rows
from chrome_oak.ui.components import esc, html, page_head, section, table


def render(ctx):
    page_head("Data prep", "Every change we made before trusting a number, and why. The raw exports are never edited.")
    prep = "".join(
        f'<div class="prep"><div><div class="ttl" style="font-size:16px">✓ {esc(p["what"])}</div>'
        f'<p style="margin:2px 0 0"><b style="color:#8B5E3C">Why:</b> {esc(p["why"])}</p></div>'
        f'<span class="rows">{esc(p["rows"])}</span></div>'
        for p in get_prep_steps()
    )
    html(f'<div class="card" style="margin-top:14px">{prep}</div>')

    removed = get_removed_rows()
    section("Rows we removed", f"All {len(removed)} of them, with the line each one came from in the raw file.")
    table(removed)
    st.download_button("Download removed rows (CSV)", removed.to_csv(index=False), "removed_rows.csv", "text/csv")
