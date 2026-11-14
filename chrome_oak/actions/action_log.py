"""ACT: the action log. Every alert sent or dismissed is written to data/action_log.csv.

It is a file (not session memory) because the sidebar links reload the page:
the log, and whether an alert was already sent or dismissed, must survive that.
Nothing is emailed for real in this prototype.
"""

import pandas as pd

from chrome_oak.config import ACTION_LOG

COLUMNS = ["time", "alert_id", "setting", "condition", "records", "action", "sent_to", "status"]


def read_log():
    if not ACTION_LOG.exists():
        return pd.DataFrame(columns=COLUMNS)
    return pd.read_csv(ACTION_LOG, dtype={"setting": "Int64"})


def _write(df):
    ACTION_LOG.parent.mkdir(parents=True, exist_ok=True)
    df[COLUMNS].to_csv(ACTION_LOG, index=False)


def _entry(issue, action, status):
    return {
        "time": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "alert_id": issue["id"], "setting": issue["setting"], "condition": issue["name"],
        "records": len(issue["rows"]), "action": action, "sent_to": issue["notify"], "status": status,
    }


def record_sent(issue):
    """One log line per action Oak prepared for this alert."""
    new = pd.DataFrame([_entry(issue, a, "sent") for a in issue["actions"]])
    _write(pd.concat([read_log(), new], ignore_index=True))


def record_dismissed(issue):
    _write(pd.concat([read_log(), pd.DataFrame([_entry(issue, "Dismissed by reviewer", "dismissed")])], ignore_index=True))


def record_restored(issue):
    _write(pd.concat([read_log(), pd.DataFrame([_entry(issue, "Restored by reviewer", "restored")])], ignore_index=True))


def clear_log():
    if ACTION_LOG.exists():
        ACTION_LOG.unlink()


def is_dismissed(alert_id, log=None):
    """Dismissed if the latest dismiss/restore entry for this alert is a dismiss."""
    log = read_log() if log is None else log
    marks = log[(log["alert_id"] == alert_id) & log["status"].isin(["dismissed", "restored"])]
    return len(marks) > 0 and marks.iloc[-1]["status"] == "dismissed"


def sent_at(alert_id, setting, log=None):
    """When this alert was sent at this exact slider setting, or None."""
    log = read_log() if log is None else log
    hits = log[(log["alert_id"] == alert_id) & (log["setting"] == setting) & (log["status"] == "sent")]
    return hits.iloc[-1]["time"] if len(hits) else None
