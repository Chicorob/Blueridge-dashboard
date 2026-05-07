# BlueRidge Life Sciences — Board Performance Dashboard

Streamlit dashboard for tracking KPIs (Revenue, EBITDA, Pipeline, Win Rate,
Utilization, Backlog, FTE, etc.) across BlueRidge Life Sciences and its five
divisions: Clintrex, ToxStrategies, Suttons Creek, Modality, Design Science.

Features:
- Executive summary, division detail, comparison, trend, and data-source pages
- Calendar-aligned time ranges (Month / Quarter / Current Year / Trailing 12 Months / Custom Range)
- Prior-year comparisons (same date range, shifted back one year)
- Excel template upload for manual data entry
- One-click PowerPoint export using the BRLS branded template

## Quickstart

Prereqs: Python 3.9+

Windows:

```
setup_and_run.bat
```

macOS / Linux:

```
chmod +x setup_and_run.sh
./setup_and_run.sh
```

Or manually:

```
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # macOS/Linux
pip install -r requirements.txt
streamlit run app.py
```

The app opens at <http://localhost:8501>.

## Project layout

```
app.py              Streamlit UI and page routing
config.py           Divisions, metrics, colors, data-source map
data_manager.py     Sample-data generation, aggregation, Excel I/O
export_pptx.py      PowerPoint export (python-pptx + kaleido)
assets/             BRLS PowerPoint template + brand assets
archive/            One-off HTML patcher scripts (historical)
*.html              Standalone single-file HTML dashboards (precursor versions)
plotly.min.js, xlsx.full.min.js, pptxgen.bundle.js   bundled JS for the offline HTML
```

## PowerPoint export

`export_pptx.py` renders Plotly charts to PNG via `kaleido`, which is pinned in
`requirements.txt`. If kaleido is unavailable at runtime, the export falls back
to a KPI-only deck and a warning is shown.

## Data

By default the dashboard generates 18 months of synthetic weekly data and
aggregates it to monthly. To use real data, download the Excel template from
the sidebar, fill in monthly rows, and upload.
