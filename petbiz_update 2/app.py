"""Chrome & Oak health check. Run with:  streamlit run app.py

Pages look like the approved mockups (mockups/*.html) but show real data:
  views.py     one function per page (Welcome, Overview, Data, Insights, Alerts, Action log)
  analysis.py  cleaning + every number, read from data/raw/
Links use ?page=..., so the Let's go button and the sidebar switch pages.
"""

import streamlit as st

import views

st.set_page_config(page_title="Chrome & Oak · Health Check", page_icon="💼", layout="wide")

page = st.query_params.get("page", "welcome")
if page not in views.PAGES:
    page = "welcome"

if page == "welcome":
    views.welcome()
    st.stop()

views.inject_css()
days = st.session_state.get("days", 30)  # the "N days late" slider on the Alerts page
views.sidebar(page, views.open_alert_count(days))

if page == "overview":
    views.overview()
elif page == "data":
    views.data_page()
elif page == "insights":
    views.insights(days)
elif page == "alerts":
    views.alerts(days)
else:
    views.action_log()
