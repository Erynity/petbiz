"""Welcome page: the hook, the two mascots, and the button into the dashboard."""

import streamlit as st

from chrome_oak.ui.components import html
from chrome_oak.ui.mascots import mascots_pair
from chrome_oak.ui.theme import DAISY, LEAF, SPARK


def render():
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
        ("Oak acts", "Drafts approvals, reminders and tickets, and tells the right person."),
    ]
    for col, (t, d) in zip(st.columns(3), steps):
        col.markdown(f'<div class="card"><div class="ttl">{t}</div><p>{d}</p></div>', unsafe_allow_html=True)
