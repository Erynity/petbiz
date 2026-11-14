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
│       ├── theme.py            # colours, icons, CSS loaders
│       ├── styles/
│       │   ├── base.css        # universal CSS (every page)
│       │   ├── frame.css       # sidebar + page headings (every page except Welcome)
│       │   └── pages/          # one .css per page, same name as the page's .py
│       │       ├── welcome.css
│       │       ├── overview.css
│       │       ├── insights.css
│       │       └── alerts.css
│       ├── components.py       # shared pieces: tables, sidebar, headings
│       ├── charts.py           # SVG bar chart + sparklines
│       ├── mascots.py          # Chrome & Oak (animated SVG)
│       └── pages/              # one .py per sidebar item
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
| Change how a page looks | `chrome_oak/ui/pages/<page>.py` and `chrome_oak/ui/styles/pages/<page>.css` (only that page changes) |
| Change something on every page | `chrome_oak/ui/styles/base.css` or `chrome_oak/ui/components.py` |
| Add a page | `chrome_oak/ui/pages/<name>.py` with a `render(ctx)` function (+ optional `styles/pages/<name>.css`), then one line in `PAGES` in `app.py` |

Each page's `render()` starts with `inject_page_css(__file__)`, which loads the CSS file
with the same name from `styles/pages/`. Pages never import each other, so two people can work on two pages without conflicts.
