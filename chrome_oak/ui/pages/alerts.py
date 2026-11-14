"""Alerts: the three rules, each with its own slider, the drafted follow-ups, and Send / Dismiss.

Chrome (step 1) is the detection, Oak (step 2) is what was prepared automatically,
and step 3 is the human decision. Sent and dismissed alerts are written to the action log.
"""

import pandas as pd
import streamlit as st

from chrome_oak.actions import action_log
from chrome_oak.analysis import ALERT_RULES, run_rule
from chrome_oak.ui.components import esc, html, page_head, section, table
from chrome_oak.ui.mascots import mascot_svg


def _drafts_html(drafts):
    return "".join(
        f'<div class="draft"><div class="to">To: {esc(d["to"])}</div><div class="subj">{esc(d["subject"])}</div>{esc(d["message"])}'
        + (f'<div class="note">Internal: {esc(d["internal note"])}</div>' if d.get("internal note") else "")
        + "</div>"
        for d in drafts.fillna("").to_dict("records")
    )


def _steps(issue, sent):
    c1, c2, c3 = st.columns(3)
    c1.markdown(
        f'<div class="step3"><div class="who"><span style="flex:none">{mascot_svg("chrome", "worried", 58)}</span>'
        f'<div><div class="k">Step 1 · Chrome noticed</div><div class="h">{esc(issue["found"])}</div></div></div>'
        f'<p style="margin:8px 0 0;font-size:15px;color:#565B62">Rule: {esc(issue["rule"])}.</p></div>',
        unsafe_allow_html=True,
    )
    done = "".join(f'<div class="done">✓ {esc(a)}</div>' for a in issue["actions"])
    c2.markdown(
        f'<div class="step3 oak"><div class="who"><span style="flex:none">{mascot_svg("oak", "happy", 58)}</span>'
        f'<div><div class="k">Step 2 · Oak prepared</div><div class="h">{len(issue["actions"])} things ready</div></div></div>{done}</div>',
        unsafe_allow_html=True,
    )
    with c3:
        if sent:
            html(f'<div class="step3"><div class="k">Step 3 · Done</div><div class="sentok">✓ Sent to {esc(issue["notify"])}</div>'
                 f'<p style="margin:4px 0 0;color:#565B62">{esc(sent)}</p></div>')
            return
        n = len(issue["drafts"])
        html(f'<div class="step3"><div class="k">Step 3 · Your turn</div><div class="h">Send to {esc(issue["notify"])}?</div></div>')
        if st.button(f"Send {n} drafted message{'s' if n != 1 else ''}", key=f"send_{issue['id']}", type="primary"):
            action_log.record_sent(issue)
            st.session_state.flash = f"Sent ✓ {issue['notify']} notified"
            st.rerun()
        if st.button("Not a problem, dismiss", key=f"dismiss_{issue['id']}", type="secondary"):
            action_log.record_dismissed(issue)
            st.session_state.flash = "Alert dismissed"
            st.rerun()


def render(ctx):
    if "flash" in st.session_state:
        st.toast(st.session_state.pop("flash"))
    page_head("Alerts", "Checks that run automatically. When a rule is met, Chrome flags it and Oak drafts the follow-up. You decide what gets sent.")
    log = action_log.read_log()

    for rule in ALERT_RULES:
        rid = rule["id"]
        issue = run_rule(rid, st.session_state.get(f"rule_{rid}", rule["default"]))
        count = len(issue["rows"])
        section(f'<span class="sev {issue["severity"]}">{esc(issue["severity"])}</span>{count} {esc(issue["name"])}')

        if action_log.is_dismissed(rid, log):
            html('<p style="color:#565B62">Dismissed by a reviewer. It stays in the action log.</p>')
            if st.button("Restore this alert", key=f"restore_{rid}", type="secondary"):
                action_log.record_restored(issue)
                st.rerun()
            continue

        st.slider(rule["slider"], rule["min"], rule["max"], rule["default"], rule["step"], key=f"rule_{rid}",
                  help="Simulation: move it to see what a stricter or looser rule would catch.")
        html(f'<div class="impact">At this setting: <b>{count}</b> flagged · <b>${issue["impact"]:,.0f}</b> involved</div>')
        if not count:
            html('<p style="color:#565B62">All clear at this setting, nothing to do.</p>')
            continue

        _steps(issue, action_log.sent_at(rid, issue["setting"], log))
        table(issue["rows"])
        n = len(issue["drafts"])
        with st.expander(f"Preview the {n} drafted message{'s' if n != 1 else ''}"):
            html(_drafts_html(issue["drafts"]))
        st.download_button("Download drafts (CSV)", issue["drafts"].to_csv(index=False), f"drafts_{rid}.csv", "text/csv",
                           key=f"dl_{rid}")
