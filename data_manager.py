"""
BlueRidge Life Sciences Dashboard - Data Manager
Handles data loading, Excel import/export, monthly aggregation, and formatting.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from io import BytesIO
from pathlib import Path
from config import (
    DIVISIONS, COMPANY_NAME, METRICS, CURRENCY_METRICS, PERCENT_METRICS,
    COUNT_METRICS, FLOW_METRICS,
)

ACTUALS_PATH = Path(__file__).parent / "data" / "actuals.csv"


def generate_sample_data():
    """Generate realistic sample data for all divisions and metrics."""
    np.random.seed(42)

    # Generate weekly dates for trailing 18 months
    end_date = datetime(2026, 3, 15)
    start_date = end_date - timedelta(days=18 * 30)
    weeks = pd.date_range(start=start_date, end=end_date, freq="W-SUN")

    records = []

    # Base values per division (annual scale, will be divided to weekly)
    division_profiles = {
        "Clintrex": {
            "Pipeline": 45_000_000, "Weighted Pipeline": 22_000_000,
            "Closed Sales": 18_000_000, "Win Rate": 42.0,
            "Revenue": 32_000_000, "EBITDA": 6_400_000,
            "Cash Collections": 30_000_000, "Utilization": 72.0,
            "Backlog": 38_000_000, "FTE": 145.0,
        },
        "ToxStrategies": {
            "Pipeline": 28_000_000, "Weighted Pipeline": 14_000_000,
            "Closed Sales": 11_000_000, "Win Rate": 38.0,
            "Revenue": 22_000_000, "EBITDA": 4_800_000,
            "Cash Collections": 20_500_000, "Utilization": 68.0,
            "Backlog": 25_000_000, "FTE": 95.0,
        },
        "Suttons Creek": {
            "Pipeline": 15_000_000, "Weighted Pipeline": 8_000_000,
            "Closed Sales": 6_500_000, "Win Rate": 45.0,
            "Revenue": 12_000_000, "EBITDA": 2_800_000,
            "Cash Collections": 11_200_000, "Utilization": 75.0,
            "Backlog": 14_000_000, "FTE": 52.0,
        },
        "Modality": {
            "Pipeline": 20_000_000, "Weighted Pipeline": 10_000_000,
            "Closed Sales": 8_500_000, "Win Rate": 40.0,
            "Revenue": 16_000_000, "EBITDA": 3_200_000,
            "Cash Collections": 14_800_000, "Utilization": 70.0,
            "Backlog": 18_000_000, "FTE": 78.0,
        },
        "Design Science": {
            "Pipeline": 12_000_000, "Weighted Pipeline": 6_500_000,
            "Closed Sales": 5_000_000, "Win Rate": 44.0,
            "Revenue": 10_000_000, "EBITDA": 2_200_000,
            "Cash Collections": 9_200_000, "Utilization": 74.0,
            "Backlog": 11_000_000, "FTE": 54.0,
        },
    }

    for week in weeks:
        # Seasonal multiplier (Q4 higher, Q1 lower)
        month = week.month
        if month in [10, 11, 12]:
            seasonal = 1.12
        elif month in [1, 2, 3]:
            seasonal = 0.90
        elif month in [4, 5, 6]:
            seasonal = 1.02
        else:
            seasonal = 0.98

        # Growth trend (5-10% annual growth)
        weeks_from_start = (week - weeks[0]).days / 7
        trend = 1.0 + (weeks_from_start / len(weeks)) * 0.08

        for division, base_values in division_profiles.items():
            row = {"Date": week, "Division": division}
            for metric, annual_base in base_values.items():
                if metric in CURRENCY_METRICS:
                    weekly_base = annual_base / 52
                    noise = np.random.normal(1.0, 0.12)
                    value = weekly_base * seasonal * trend * noise
                    row[metric] = max(0, round(value, 0))
                elif metric == "FTE":
                    # FTE is a point-in-time count, varies slowly
                    noise = np.random.normal(0, 1.5)
                    value = annual_base * trend + noise
                    row[metric] = round(max(10, value), 1)
                else:
                    # Percent metrics
                    noise = np.random.normal(0, 3.5)
                    value = annual_base * seasonal * trend * 0.98 + noise
                    row[metric] = round(min(max(value, 10), 95), 1)
            records.append(row)

    df = pd.DataFrame(records)
    df["Date"] = pd.to_datetime(df["Date"])
    return df


def aggregate_to_monthly(df):
    """Aggregate weekly data to monthly data.

    Flow metrics (Revenue, EBITDA, etc.) are summed within each month.
    Point-in-time metrics (Pipeline, Backlog, FTE, etc.) use the last value of the month.
    """
    monthly_records = []

    for division in df["Division"].unique():
        div_data = df[df["Division"] == division].sort_values("Date")
        # Group by year-month
        div_data = div_data.copy()
        div_data["YearMonth"] = div_data["Date"].dt.to_period("M")

        for period, group in div_data.groupby("YearMonth"):
            row = {
                "Date": period.to_timestamp(how="end").normalize(),  # last day of month
                "Division": division,
            }
            for metric in METRICS:
                if metric not in group.columns:
                    continue
                if metric in FLOW_METRICS:
                    row[metric] = group[metric].sum()
                else:
                    # Point-in-time: use last value in the month
                    row[metric] = group[metric].iloc[-1]
            monthly_records.append(row)

    result = pd.DataFrame(monthly_records)
    result["Date"] = pd.to_datetime(result["Date"])
    return result.sort_values(["Date", "Division"]).reset_index(drop=True)


def compute_company_totals(df):
    """Compute company-wide totals from division data."""
    company_rows = []
    for date in df["Date"].unique():
        date_data = df[df["Date"] == date]
        if COMPANY_NAME in date_data["Division"].values:
            continue
        row = {"Date": date, "Division": COMPANY_NAME}
        for metric in CURRENCY_METRICS:
            if metric in date_data.columns:
                row[metric] = date_data[metric].sum()
        for metric in PERCENT_METRICS:
            if metric in date_data.columns:
                row[metric] = round(date_data[metric].mean(), 1)
        for metric in COUNT_METRICS:
            if metric in date_data.columns:
                row[metric] = round(date_data[metric].sum(), 1)
        company_rows.append(row)
    company_df = pd.DataFrame(company_rows)
    return pd.concat([df, company_df], ignore_index=True)


def get_date_range_for_time_range(df, time_range, custom_start=None, custom_end=None):
    """Return (start_date, end_date) for the selected time range.

    All ranges are calendar-month aligned.
    """
    latest_date = pd.Timestamp(df["Date"].max())

    if time_range == "Month":
        # Current calendar month of the latest data
        start = latest_date.replace(day=1)
        end = latest_date
    elif time_range == "Quarter":
        # Current calendar quarter up to the latest data date
        q_start_month = ((latest_date.month - 1) // 3) * 3 + 1
        start = latest_date.replace(month=q_start_month, day=1)
        end = latest_date
    elif time_range == "Current Year":
        start = latest_date.replace(month=1, day=1)
        end = latest_date
    elif time_range == "Trailing 12 Months":
        start = latest_date - relativedelta(months=11)
        start = start.replace(day=1)
        end = latest_date
    elif time_range == "Custom Range" and custom_start and custom_end:
        start = pd.Timestamp(custom_start)
        end = pd.Timestamp(custom_end)
    else:
        # Default to current month
        start = latest_date.replace(day=1)
        end = latest_date

    return start, end


def filter_by_time_range(df, time_range, custom_start=None, custom_end=None):
    """Filter dataframe by selected time range using calendar-month boundaries."""
    if df.empty:
        return df

    start, end = get_date_range_for_time_range(df, time_range, custom_start, custom_end)
    return df[(df["Date"] >= start) & (df["Date"] <= end)].copy()


def get_prior_year_date_range(start, end):
    """Get the same date range shifted back one year."""
    prior_start = start - relativedelta(years=1)
    prior_end = end - relativedelta(years=1)
    return prior_start, prior_end


def aggregate_for_period(df, entity, time_range, custom_start=None, custom_end=None):
    """Aggregate data for a specific entity and time period.

    Flow metrics are summed. Point-in-time metrics use the latest month-end value.
    """
    filtered = filter_by_time_range(df, time_range, custom_start, custom_end)
    entity_data = filtered[filtered["Division"] == entity].sort_values("Date")

    if entity_data.empty:
        return {m: 0 for m in METRICS}

    result = {}
    for metric in METRICS:
        if metric not in entity_data.columns:
            result[metric] = 0
            continue
        if metric in FLOW_METRICS:
            result[metric] = entity_data[metric].sum()
        else:
            # Point-in-time: latest month-end value
            result[metric] = entity_data[metric].iloc[-1]
    return result


def get_prior_period_data(df, entity, time_range, custom_start=None, custom_end=None):
    """Get data from the same date range one year prior."""
    start, end = get_date_range_for_time_range(df, time_range, custom_start, custom_end)
    prior_start, prior_end = get_prior_year_date_range(start, end)

    entity_data = df[
        (df["Division"] == entity) &
        (df["Date"] >= prior_start) &
        (df["Date"] <= prior_end)
    ].sort_values("Date")

    if entity_data.empty:
        return {m: 0 for m in METRICS}

    result = {}
    for metric in METRICS:
        if metric not in entity_data.columns:
            result[metric] = 0
            continue
        if metric in FLOW_METRICS:
            result[metric] = entity_data[metric].sum()
        else:
            result[metric] = entity_data[metric].iloc[-1]
    return result


def get_trend_data(df, entity, metric, time_range, custom_start=None, custom_end=None):
    """Get time series data for trend charts."""
    filtered = filter_by_time_range(df, time_range, custom_start, custom_end)
    entity_data = filtered[filtered["Division"] == entity].sort_values("Date")
    if metric not in entity_data.columns:
        return pd.DataFrame(columns=["Date", metric])
    return entity_data[["Date", metric]].copy()


def get_comparison_data(df, metric, time_range, custom_start=None, custom_end=None):
    """Get comparison data across all divisions for a specific metric."""
    filtered = filter_by_time_range(df, time_range, custom_start, custom_end)
    result = {}
    for division in DIVISIONS:
        div_data = filtered[filtered["Division"] == division].sort_values("Date")
        if not div_data.empty:
            if metric not in div_data.columns:
                result[division] = 0
            elif metric in FLOW_METRICS:
                result[division] = div_data[metric].sum()
            else:
                result[division] = div_data[metric].iloc[-1]
    return result


def create_excel_template():
    """Create an Excel template for data entry."""
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # Instructions sheet
        instructions = pd.DataFrame({
            "Instructions": [
                "BlueRidge Life Sciences - Dashboard Data Entry Template",
                "",
                "1. Enter data in the 'Data Entry' sheet",
                "2. Each row represents one month of data for one division",
                "3. Date should be the month-end date",
                "4. Division must be one of: Clintrex, ToxStrategies, Suttons Creek, Modality, Design Science",
                "5. Currency values should be entered as whole numbers (no $ sign)",
                "6. Percentages should be entered as numbers (e.g., 75.5 for 75.5%)",
                "7. Upload the completed file to the dashboard",
                "",
                "Metric Definitions:",
                "Pipeline - Total value of all open opportunities (point-in-time)",
                "Weighted Pipeline - Pipeline adjusted by probability of close (point-in-time)",
                "Closed Sales - Value of deals won in the period (sum over period)",
                "Win Rate - Percentage of proposals won vs. total proposals (point-in-time)",
                "Revenue - Recognized revenue for the period (sum over period)",
                "EBITDA - Earnings before interest, taxes, depreciation, and amortization (sum over period)",
                "Cash Collections - Actual cash received in the period (sum over period)",
                "Utilization - Percentage of billable hours vs. available hours (point-in-time)",
                "Backlog - Total value of contracted but unrecognized revenue (point-in-time)",
                "FTE - Full-time equivalent headcount (point-in-time)",
            ]
        })
        instructions.to_excel(writer, sheet_name="Instructions", index=False)

        # Data entry sheet with sample row
        sample = pd.DataFrame([{
            "Date": "2026-03-31",
            "Division": "Clintrex",
            "Pipeline": 850000,
            "Weighted Pipeline": 425000,
            "Closed Sales": 340000,
            "Win Rate": 42.5,
            "Revenue": 615000,
            "EBITDA": 123000,
            "Cash Collections": 580000,
            "Utilization": 72.3,
            "Backlog": 730000,
            "FTE": 145.0,
        }])
        sample.to_excel(writer, sheet_name="Data Entry", index=False)

        # Division reference
        div_ref = pd.DataFrame({"Valid Divisions": DIVISIONS})
        div_ref.to_excel(writer, sheet_name="Reference", index=False)

    output.seek(0)
    return output


def load_actuals_data(path=ACTUALS_PATH):
    """Load real monthly actuals from data/actuals.csv.

    Produced by data/build_actuals.py from the BlueRidge dashboard Excel
    template. Rows are already one-per-division-per-month with month-end dates,
    so no further aggregation is needed. Missing cells stay as NaN so callers
    can distinguish 'no data reported' from a real zero.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Actuals CSV not found at {path}. "
            f"Run 'python data/build_actuals.py' to regenerate it from the Excel template."
        )
    df = pd.read_csv(path, parse_dates=["Date"])
    return df


def load_from_excel(uploaded_file):
    """Load data from uploaded Excel file."""
    try:
        df = pd.read_excel(uploaded_file, sheet_name="Data Entry", engine="openpyxl")
        df["Date"] = pd.to_datetime(df["Date"])

        required_cols = ["Date", "Division"] + list(METRICS.keys())
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            return None, f"Missing columns: {', '.join(missing)}"

        invalid_divs = set(df["Division"].unique()) - set(DIVISIONS)
        if invalid_divs:
            return None, f"Invalid divisions found: {', '.join(invalid_divs)}"

        return df, None
    except Exception as e:
        return None, f"Error reading file: {str(e)}"


def determine_display_unit(values):
    """Determine a consistent display unit for a list of currency values.

    Returns 'M' if any value >= 1,000,000, otherwise 'K'.
    """
    if not values:
        return "K"
    max_abs = max(abs(v) for v in values if v != 0) if any(v != 0 for v in values) else 0
    if max_abs >= 1_000_000:
        return "M"
    return "K"


def format_value(value, metric, unit=None):
    """Format a metric value for display.

    If unit is provided for currency metrics, forces that unit for consistency.
    """
    cfg = METRICS[metric]
    if cfg["format"] == "currency":
        if unit == "M":
            return f"${value / 1_000_000:,.1f}M"
        elif unit == "K":
            return f"${value / 1_000:,.0f}K"
        else:
            # Auto-detect (fallback)
            if abs(value) >= 1_000_000:
                return f"${value / 1_000_000:,.1f}M"
            elif abs(value) >= 1_000:
                return f"${value / 1_000:,.0f}K"
            else:
                return f"${value:,.0f}"
    elif cfg["format"] == "percent":
        return f"{value:.1f}%"
    elif cfg["format"] == "count":
        return f"{value:,.1f}"
    return str(value)


def compute_delta(current, prior):
    """Compute percentage change between current and prior period.

    Returns None when prior is 0 (no comparable baseline) so callers can
    display 'n/a' rather than a misleading 0%.
    """
    if prior == 0:
        return None
    return round(((current - prior) / abs(prior)) * 100, 1)


def get_available_months(df):
    """Return a sorted list of (year, month) tuples available in the data."""
    dates = pd.to_datetime(df["Date"])
    periods = sorted(dates.dt.to_period("M").unique())
    return [(p.year, p.month) for p in periods]


def get_time_range_label(time_range, df, custom_start=None, custom_end=None):
    """Generate a descriptive label for the selected time range."""
    if df is None or df.empty:
        return time_range

    latest = pd.Timestamp(df["Date"].max())
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    if time_range == "Month":
        return f"{month_names[latest.month - 1]} {latest.year}"
    elif time_range == "Quarter":
        q = (latest.month - 1) // 3 + 1
        return f"Q{q} {latest.year}"
    elif time_range == "Current Year":
        return f"YTD {latest.year}"
    elif time_range == "Trailing 12 Months":
        start = latest - relativedelta(months=11)
        return f"{month_names[start.month - 1]} {start.year} \u2013 {month_names[latest.month - 1]} {latest.year}"
    elif time_range == "Custom Range" and custom_start and custom_end:
        s = pd.Timestamp(custom_start)
        e = pd.Timestamp(custom_end)
        return f"{month_names[s.month - 1]} {s.year} \u2013 {month_names[e.month - 1]} {e.year}"
    return time_range
