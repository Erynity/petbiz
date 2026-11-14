"""Alerts: one collapsible box per rule. A slider to tune the rule, what it found, and a button to send the drafted follow-ups.

Sent and dismissed alerts are written to the action log.
"""

import streamlit as st

from chrome_oak.actions import action_log
from chrome_oak.analysis import ALERT_RULES, run_rule
from chrome_oak.ui.components import esc, html, page_head, table
from chrome_oak.ui.theme import inject_page_css

SEV_DOT = {"High": "🟠", "Medium": "🟡", "Low": "⚪"}


def _drafts_html(drafts):
    return "".join(
        f'<div class="draft"><div class="to">To: {esc(d["to"])}</div><div class="subj">{esc(d["subject"])}</div>{esc(d["message"])}'
        + (f'<div class="note">Internal: {esc(d["internal note"])}</div>' if d.get("internal note") else "")
        + "</div>"
        for d in drafts.fillna("").to_dict("records")
    )


def _alert(rule, issue, log, first):
    rid, count = rule["id"], len(issue["rows"])
    dismissed = action_log.is_dismissed(rid, log)
    sent = action_log.sent_at(rid, issue["setting"], log)
    status = "dismissed" if dismissed else "sent ✓" if sent else "to review" if count else "all clear"
    # The label must not change when the slider moves, or the box would close by itself.
    label = f"{SEV_DOT.get(issue['severity'], '')} {issue['name'][0].upper()}{issue['name'][1:]} · {status}"

    with st.expander(label, expanded=first):
        if dismissed:
            html('<p class="muted">Dismissed by a reviewer. It stays in the action log.</p>')
            if st.button("Restore this alert", key=f"restore_{rid}", type="secondary"):
                action_log.record_restored(issue)
                st.rerun()
            return

        st.slider(rule["slider"], rule["min"], rule["max"], rule["default"], rule["step"], key=f"rule_{rid}",
                  help="Simulation: move it to see what a stricter or looser rule would catch.")
        html(f'<div class="impact"><b>{count}</b> flagged · <b>${issue["impact"]:,.0f}</b> involved · goes to <b>{esc(issue["notify"])}</b>'
             f'<div class="rule">Rule: {esc(issue["rule"])}.</div></div>')
        if not count:
            html('<p class="muted">All clear at this setting, nothing to send.</p>')
            return

        table(issue["rows"])

        n = len(issue["drafts"])
        c1, c2, c3 = st.columns([1.3, 1, 1])
        if sent:
            c1.markdown(f'<div class="sentok">✓ Sent to {esc(issue["notify"])} · {esc(sent)}</div>', unsafe_allow_html=True)
        elif c1.button(f"Send {n} message{'s' if n != 1 else ''} to {issue['notify']}", key=f"send_{rid}", type="primary"):
            action_log.record_sent(issue)
            st.session_state.flash = f"Sent ✓ {issue['notify']} notified"
            st.rerun()
        if not sent and c2.button("Dismiss", key=f"dismiss_{rid}", type="secondary"):
            action_log.record_dismissed(issue)
            st.session_state.flash = "Alert dismissed"
            st.rerun()
        c3.download_button("Download drafts", issue["drafts"].to_csv(index=False), f"drafts_{rid}.csv", "text/csv", key=f"dl_{rid}")
        if st.toggle("Preview the messages", key=f"preview_{rid}"):
            html(_drafts_html(issue["drafts"]))


def render(ctx):
    inject_page_css(__file__)
    if "flash" in st.session_state:
        st.toast(st.session_state.pop("flash"))
    page_head("Alerts", "Checks that run automatically. Each one drafts the follow-up; you decide what gets sent.")
    log = action_log.read_log()
    for n, rule in enumerate(ALERT_RULES):
        issue = run_rule(rule["id"], st.session_state.get(f"rule_{rule['id']}", rule["default"]))
        _alert(rule, issue, log, first=(n == 0))
