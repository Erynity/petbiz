# Chrome & Oak · Business health check

Hack2theFuture, Business track, Option B (Chrome & Oak Office Supply).
A Streamlit tool that cleans the company's exports, shows what is really driving
the gap between revenue and profit, and turns three detected conditions into
drafted follow-ups the team can send.

## Run locally

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

## Project structure

```text
petbiz/
├── app.py                      # entry point: page setup, sidebar, routing (no logic)
├── chrome_oak/
│   ├── config.py               # paths, extraction date (ASOF), payment terms
│   ├── data/
│   │   ├── cleaning.py         # clean_all(): raw CSVs -> data/clean/ + docs/CLEANING_LOG.md
│   │   └── loader.py           # load_data() joins the 3 files; get_data() for the Data list
│   ├── analysis/               # every number the pages show
│   │   ├── metrics.py          # small helpers (margin %, money format)
│   │   ├── overview.py         # get_focus(), get_kpis()
│   │   ├── insights.py         # get_charts(), get_insights()
│   │   └── detections.py       # the 3 alert rules + ALERT_RULES (slider settings)
│   ├── actions/
│   │   └── action_log.py       # sent / dismissed alerts -> data/action_log.csv
│   └── ui/
│       ├── theme.py            # colours, CSS, icons
│       ├── components.py       # tables, sidebar, headings, chat bubbles
│       ├── charts.py           # SVG bar chart + sparklines
│       ├── mascots.py          # Chrome & Oak (animated SVG)
│       └── pages/              # one file per sidebar item
│           ├── welcome.py
│           ├── overview.py
│           ├── data_list.py
│           ├── insights.py
│           ├── alerts.py
│           └── action_log.py
├── data/
│   ├── raw/                    # exports exactly as received (never edited)
│   └── clean/                  # written by cleaning.py
└── docs/
    └── CLEANING_LOG.md         # data prep: every cleaning step and dropped row
```

## Where to change things

| I want to… | Edit |
|---|---|
| Change a cleaning rule | `chrome_oak/data/cleaning.py` (re-run: `python -m chrome_oak.data.cleaning`) |
| Change a KPI, chart or insight | `chrome_oak/analysis/overview.py` or `insights.py` |
| Change an alert rule or its slider range | `chrome_oak/analysis/detections.py` (`detect_*` and `ALERT_RULES`) |
| Change how a page looks | `chrome_oak/ui/pages/<page>.py` |
| Add a page | new file in `chrome_oak/ui/pages/`, then add it to `PAGES` (components.py) and `ROUTES` (app.py) |
