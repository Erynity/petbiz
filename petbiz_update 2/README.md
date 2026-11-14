# Chrome & Oak · Health Check (petbiz)

Run from this folder:

    ../venv/bin/streamlit run app.py

| Path | What it is |
|---|---|
| `app.py` | Entry point: picks the page from `?page=...` |
| `views.py` | One function per page. Looks like the mockups, shows real data |
| `analysis.py` | Cleaning, joining and every number. Reads `data/raw/` |
| `mockups/` | The approved HTML designs (`views.py` copies their look, sidebar and mascots) |
| `data/raw/` | `customers.csv`, `orders.csv`, `returns.csv`, exactly as received |
| `data/action_log.csv` | Created when you send or dismiss an alert |
| `.streamlit/config.toml` | Theme |
| `ui/` | Old helper files from the previous UI, no longer used |
