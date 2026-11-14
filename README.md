# Pet Insights

A Streamlit application for exploring the hackathon challenge dataset and
turning its findings into a conversational pet experience.

## Project structure

```text
business/
├── data/
│   └── dataset.csv       # Add the challenge data here
├── app.py                # Streamlit page, layout, and styling
├── analysis.py           # Data loading and analysis helpers
├── requirements.txt      # Python dependencies
└── .gitignore
```

The virtual environment is local-only and should not be committed.

## Run locally

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```
