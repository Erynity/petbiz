"""Action log: everything sent or dismissed from the Alerts page, newest first."""

import streamlit as st

from chrome_oak.actions import action_log
from chrome_oak.ui.components import html, page_head, table
from chrome_oak.ui.theme import inject_page_css


def render(ctx):
    inject_page_css(__file__)
    page_head("Action log", "Everything the team sent or dismissed, so a person can check it. Nothing is emailed for real in this prototype.")
    log = action_log.read_log()
    if log.empty:
        html('<div class="card"><p>No actions yet. Open <a href="?page=alerts" target="_self">Alerts</a>, '
             'review a drafted follow-up and send or dismiss it.</p></div>')
        return
    shown = log.iloc[::-1][["time", "condition", "setting", "records", "action", "sent_to", "status"]]
    table(shown)
    c1, c2, _ = st.columns([1, 1, 3])
    c1.download_button("Download log (CSV)", log.to_csv(index=False), "action_log.csv", "text/csv")
    if c2.button("Clear the log", type="secondary"):
        action_log.clear_log()
        st.rerun()
