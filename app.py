"""Chrome & Oak – business health check (Hack2theFuture, Business track, Option B).

Run with:  streamlit run app.py

This file only routes: it sets up the page, draws the sidebar and calls one page module.
  Pages        chrome_oak/ui/pages/      one file per sidebar item
  Numbers      chrome_oak/analysis/      everything the pages show
  Data         chrome_oak/data/          cleaning + loading
  Actions      chrome_oak/actions/       the action log
"""

import streamlit as st

from chrome_oak.actions import action_log
from chrome_oak.analysis import detect_issues
from chrome_oak.ui.components import sidebar
from chrome_oak.ui.mascots import show_pets
from chrome_oak.ui.pages import action_log as log_page
from chrome_oak.ui.pages import alerts, data_list, insights, overview, welcome
from chrome_oak.ui.theme import inject_frame, inject_theme

st.set_page_config(page_title="Chrome & Oak · Health Check", page_icon="💼", layout="wide")
inject_theme()

# The one list of pages: (query-string id, sidebar icon, sidebar label, page module).
# To add a page: create chrome_oak/ui/pages/<name>.py (+ optional <name>.css) and add one line here.
PAGES = [
    ("overview", "home", "Overview", overview),
    ("data", "list", "Data list", data_list),
    ("insights", "chart", "Insights", insights),
    ("alerts", "bell", "Alerts", alerts),
    ("log", "log", "Action log", log_page),
]
ROUTES = {pid: module.render for pid, _, _, module in PAGES}

page = st.query_params.get("page", "welcome")
if page not in ROUTES:
    welcome.render()
    st.stop()

# Alerts at the default thresholds drive the sidebar badge, the overview and the mascots.
log = action_log.read_log()
issues = detect_issues()
open_issues = [i for i in issues if len(i["rows"]) and not action_log.is_dismissed(i["id"], log)]

inject_frame()
sidebar([(pid, ic, label) for pid, ic, label, _ in PAGES], page, len(open_issues))
ROUTES[page]({"issues": issues, "open_issues": open_issues})

# Chrome & Oak floating in the bottom-right corner, talking about the biggest open alert
if not open_issues:
    show_pets("happy", "I checked every order, return and invoice. All clear!", "Great, nothing needs action right now.")
else:
    top = max(open_issues, key=lambda i: i["impact"])
    show_pets(
        "worried" if len(open_issues) == 1 else "sad",
        f"{len(open_issues)} alerts are open. Biggest: {len(top['rows'])} {top['name']}.",
        f"I drafted the follow-ups. Open Alerts to send them to {top['notify']}.",
    )
