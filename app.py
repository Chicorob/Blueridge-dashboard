"""
BlueRidge Life Sciences - Board Performance Dashboard
Interactive Streamlit dashboard for tracking key business metrics across divisions.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import os
from datetime import datetime
from config import (
    COMPANY_NAME, DIVISIONS, ALL_ENTITIES, METRICS,
    CURRENCY_METRICS, PERCENT_METRICS, COUNT_METRICS,
    TIME_RANGES, COLORS, DIVISION_COLORS, DATA_SOURCES,
)
from data_manager import (
    generate_sample_data, aggregate_to_monthly, compute_company_totals,
    filter_by_time_range, aggregate_for_period,
    get_prior_period_data, get_trend_data,
    get_comparison_data, create_excel_template,
    load_from_excel, format_value, compute_delta,
    determine_display_unit, get_available_months,
    get_time_range_label, get_date_range_for_time_range,
)
from export_pptx import (
    export_full_dashboard, export_executive_summary,
    export_division_comparison, export_trend_chart,
    export_division_detail, export_single_division,
    create_presentation, save_presentation_to_bytes,
    ChartRenderError,
)

# ─── Page Configuration ───
st.set_page_config(
    page_title=f"{COMPANY_NAME} Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=EB+Garamond:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Times New Roman', 'EB Garamond', Times, serif !important;
    }}
    .stApp {{
        background-color: {COLORS['white']};
    }}

    /* Header bar */
    .header-bar {{
        background: linear-gradient(135deg, {COLORS['dark_blue']}, {COLORS['primary_blue']});
        padding: 18px 30px;
        border-radius: 0 0 12px 12px;
        margin: -1rem -1rem 1.5rem -1rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }}
    .header-title {{
        color: white;
        font-size: 30px;
        font-weight: 700;
        font-family: 'Times New Roman', Times, serif;
        letter-spacing: 0.5px;
    }}
    .header-subtitle {{
        color: {COLORS['light_blue']};
        font-size: 16px;
        font-family: 'Times New Roman', Times, serif;
    }}

    /* KPI Cards */
    .kpi-card {{
        background: linear-gradient(145deg, #FAFEFE, {COLORS['pale_blue']});
        border: 1px solid {COLORS['light_blue']};
        border-radius: 12px;
        padding: 20px 22px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,102,179,0.08);
        transition: transform 0.2s, box-shadow 0.2s;
        min-height: 160px;
    }}
    .kpi-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0,102,179,0.15);
    }}
    .kpi-label {{
        font-size: 15px;
        color: {COLORS['text_secondary']};
        font-family: 'Times New Roman', Times, serif;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-bottom: 8px;
    }}
    .kpi-value {{
        font-size: 30px;
        font-weight: 700;
        color: {COLORS['dark_blue']};
        font-family: 'Times New Roman', Times, serif;
        margin-bottom: 6px;
    }}
    .kpi-delta-positive {{
        font-size: 14px;
        color: {COLORS['positive']};
        font-family: 'Times New Roman', Times, serif;
        font-weight: 600;
    }}
    .kpi-delta-negative {{
        font-size: 14px;
        color: {COLORS['negative']};
        font-family: 'Times New Roman', Times, serif;
        font-weight: 600;
    }}
    .kpi-delta-neutral {{
        font-size: 14px;
        color: {COLORS['text_secondary']};
        font-family: 'Times New Roman', Times, serif;
        font-weight: 600;
    }}

    /* Section headers */
    .section-header {{
        font-size: 24px;
        font-weight: 700;
        color: {COLORS['dark_blue']};
        font-family: 'Times New Roman', Times, serif;
        border-bottom: 3px solid {COLORS['primary_green']};
        padding-bottom: 8px;
        margin: 30px 0 20px 0;
    }}

    /* Sidebar styling */
    section[data-testid="stSidebar"] {{
        background-color: {COLORS['dark_blue']};
    }}
    section[data-testid="stSidebar"] * {{
        color: white !important;
        font-family: 'Times New Roman', Times, serif !important;
    }}
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stRadio > label {{
        font-size: 16px !important;
        font-weight: 600 !important;
    }}
    section[data-testid="stSidebar"] [data-baseweb="select"] *,
    section[data-testid="stSidebar"] [data-baseweb="select"] span,
    section[data-testid="stSidebar"] [data-baseweb="select"] div {{
        color: black !important;
    }}

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
    }}
    .stTabs [data-baseweb="tab"] {{
        font-family: 'Times New Roman', Times, serif !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        color: {COLORS['dark_blue']} !important;
        padding: 10px 24px !important;
    }}
    .stTabs [aria-selected="true"] {{
        border-bottom-color: {COLORS['primary_green']} !important;
    }}

    /* Metric display */
    [data-testid="stMetricValue"] {{
        font-family: 'Times New Roman', Times, serif !important;
        font-size: 28px !important;
        color: {COLORS['dark_blue']} !important;
    }}
    [data-testid="stMetricLabel"] {{
        font-family: 'Times New Roman', Times, serif !important;
        font-size: 15px !important;
    }}

    /* Data table */
    .dataframe {{
        font-family: 'Times New Roman', Times, serif !important;
        font-size: 15px !important;
    }}

    /* Hide Streamlit branding */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}

    .divider {{
        height: 3px;
        background: linear-gradient(90deg, {COLORS['primary_blue']}, {COLORS['primary_green']}, transparent);
        margin: 10px 0 20px 0;
        border-radius: 2px;
    }}
</style>
""", unsafe_allow_html=True)


# ─── Data Initialization ───
@st.cache_data
def load_data():
    df = generate_sample_data()
    df = aggregate_to_monthly(df)
    df = compute_company_totals(df)
    return df


def get_data():
    if "uploaded_data" in st.session_state and st.session_state.uploaded_data is not None:
        return st.session_state.uploaded_data
    return load_data()


# ─── Chart Helpers ───
def get_chart_layout(title="", height=420):
    return dict(
        title=dict(text=title, font=dict(family="Times New Roman", size=20, color=COLORS["dark_blue"])),
        font=dict(family="Times New Roman", size=14, color=COLORS["text_primary"]),
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=height,
        margin=dict(l=60, r=30, t=50, b=50),
        xaxis=dict(gridcolor="#ECECEC", linecolor="#CCCCCC"),
        yaxis=dict(gridcolor="#ECECEC", linecolor="#CCCCCC"),
        legend=dict(
            orientation="h", yanchor="bottom", y=-0.22,
            xanchor="center", x=0.5,
            font=dict(size=13, family="Times New Roman"),
        ),
        hoverlabel=dict(font_family="Times New Roman", font_size=14),
    )


def make_bar_chart(data_dict, metric, title="", unit=None):
    divisions = list(data_dict.keys())
    values = list(data_dict.values())
    colors = [DIVISION_COLORS.get(d, COLORS["primary_blue"]) for d in divisions]

    fig = go.Figure(data=[go.Bar(
        x=divisions, y=values,
        marker_color=colors,
        text=[format_value(v, metric, unit=unit) for v in values],
        textposition="outside",
        textfont=dict(size=15, family="Times New Roman", color=COLORS["dark_blue"]),
        hovertemplate="%{x}: %{text}<extra></extra>",
    )])
    fig.update_layout(**get_chart_layout(title, height=450))
    fig.update_yaxes(title_text="")
    return fig


def make_trend_chart(df, entities, metric, time_range, title="",
                     custom_start=None, custom_end=None):
    fig = go.Figure()
    for entity in entities:
        trend = get_trend_data(df, entity, metric, time_range,
                               custom_start=custom_start, custom_end=custom_end)
        if not trend.empty:
            color = DIVISION_COLORS.get(entity, COLORS["primary_blue"])
            fig.add_trace(go.Scatter(
                x=trend["Date"], y=trend[metric],
                name=entity, mode="lines+markers",
                line=dict(color=color, width=2.5),
                marker=dict(size=5),
                hovertemplate=f"{entity}<br>%{{x|%b %Y}}<br>{metric}: %{{y:,.0f}}<extra></extra>",
            ))
    fig.update_layout(**get_chart_layout(title, height=450))
    return fig


def make_pie_chart(data_dict, metric, title="", unit=None):
    divisions = list(data_dict.keys())
    values = list(data_dict.values())
    colors = [DIVISION_COLORS.get(d, COLORS["primary_blue"]) for d in divisions]

    fig = go.Figure(data=[go.Pie(
        labels=divisions, values=values,
        marker=dict(colors=colors),
        textinfo="label+percent",
        textfont=dict(size=14, family="Times New Roman"),
        hovertemplate="%{label}<br>%{value:,.0f}<br>%{percent}<extra></extra>",
        hole=0.4,
    )])
    fig.update_layout(**get_chart_layout(title, height=420))
    fig.update_layout(showlegend=True)
    return fig


# ─── Month Picker Helpers ───
def _month_options(df):
    """Build month options from the data for custom range pickers."""
    available = get_available_months(df)
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    options = []
    for y, m in available:
        label = f"{month_names[m - 1]} {y}"
        options.append((label, y, m))
    return options


# ─── Sidebar ───
def render_sidebar(df):
    with st.sidebar:
        logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
        if os.path.exists(logo_path):
            st.image(logo_path, width=220)
        else:
            st.markdown(f"### {COMPANY_NAME}")

        st.markdown("---")
        st.markdown("#### Navigation")
        page = st.radio(
            "Select View",
            ["Executive Summary", "Division Detail", "Metric Deep Dive",
             "Division Comparison", "Data Management", "Integration Setup"],
            label_visibility="collapsed",
        )

        st.markdown("---")
        st.markdown("#### Filters")
        time_range = st.selectbox("Time Range", TIME_RANGES, index=1)

        # Custom range month pickers
        custom_start = None
        custom_end = None
        if time_range == "Custom Range":
            month_opts = _month_options(df)
            if month_opts:
                labels = [o[0] for o in month_opts]
                start_idx = st.selectbox("Start Month", range(len(labels)),
                                         format_func=lambda i: labels[i],
                                         index=0, key="custom_start_month")
                end_idx = st.selectbox("End Month", range(len(labels)),
                                       format_func=lambda i: labels[i],
                                       index=len(labels) - 1, key="custom_end_month")
                # Ensure start <= end
                if start_idx > end_idx:
                    start_idx, end_idx = end_idx, start_idx
                _, sy, sm = month_opts[start_idx]
                _, ey, em = month_opts[end_idx]
                custom_start = pd.Timestamp(year=sy, month=sm, day=1)
                # End of month
                custom_end = pd.Timestamp(year=ey, month=em, day=1) + pd.offsets.MonthEnd(0)

        if page in ["Executive Summary", "Metric Deep Dive"]:
            entity = st.selectbox("Entity", ALL_ENTITIES, index=0)
        elif page == "Division Detail":
            entity = st.selectbox("Division", DIVISIONS, index=0)
        else:
            entity = COMPANY_NAME

        st.markdown("---")
        st.markdown("#### Export")

        return page, time_range, entity, custom_start, custom_end


# ─── KPI Display ───
def render_kpi_cards(current_data, prior_data):
    metrics_list = list(METRICS.keys())

    # Determine consistent display unit for all currency values
    currency_values = [current_data.get(m, 0) for m in CURRENCY_METRICS if m in current_data]
    unit = determine_display_unit(currency_values)

    # Render in rows of 5
    row_size = 5
    for row_start in range(0, len(metrics_list), row_size):
        row_metrics = metrics_list[row_start:row_start + row_size]
        cols = st.columns(len(row_metrics))
        for col, metric in zip(cols, row_metrics):
            with col:
                val = current_data.get(metric, 0)
                prior_val = prior_data.get(metric, 0)
                delta = compute_delta(val, prior_val)
                if metric in CURRENCY_METRICS:
                    formatted = format_value(val, metric, unit=unit)
                else:
                    formatted = format_value(val, metric)
                if delta is None:
                    delta_class = "kpi-delta-neutral"
                    delta_html = "n/a vs prior year"
                else:
                    delta_class = "kpi-delta-positive" if delta >= 0 else "kpi-delta-negative"
                    arrow = "▲" if delta >= 0 else "▼"
                    delta_html = f"{arrow} {abs(delta):.1f}% vs prior year"
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">{metric}</div>
                    <div class="kpi-value">{formatted}</div>
                    <div class="{delta_class}">{delta_html}</div>
                </div>
                """, unsafe_allow_html=True)
        if row_start + row_size < len(metrics_list):
            st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)


# ─── Pages ───
def page_executive_summary(df, time_range, entity, custom_start=None, custom_end=None):
    label = get_time_range_label(time_range, df, custom_start, custom_end)
    st.markdown(f'<div class="header-bar"><div><div class="header-title">Executive Summary</div>'
                f'<div class="header-subtitle">{entity} | {label}</div></div></div>',
                unsafe_allow_html=True)
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    current = aggregate_for_period(df, entity, time_range, custom_start, custom_end)
    prior = get_prior_period_data(df, entity, time_range, custom_start, custom_end)
    render_kpi_cards(current, prior)

    st.markdown('<div class="section-header">Revenue & Profitability Trends</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if entity == COMPANY_NAME:
            fig = make_trend_chart(df, DIVISIONS, "Revenue", time_range, "Revenue by Division",
                                   custom_start=custom_start, custom_end=custom_end)
        else:
            fig = make_trend_chart(df, [entity], "Revenue", time_range, f"Revenue - {entity}",
                                   custom_start=custom_start, custom_end=custom_end)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        if entity == COMPANY_NAME:
            fig = make_trend_chart(df, DIVISIONS, "EBITDA", time_range, "EBITDA by Division",
                                   custom_start=custom_start, custom_end=custom_end)
        else:
            fig = make_trend_chart(df, [entity], "EBITDA", time_range, f"EBITDA - {entity}",
                                   custom_start=custom_start, custom_end=custom_end)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-header">Sales Performance</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if entity == COMPANY_NAME:
            fig = make_trend_chart(df, DIVISIONS, "Pipeline", time_range, "Pipeline by Division",
                                   custom_start=custom_start, custom_end=custom_end)
        else:
            fig = make_trend_chart(df, [entity], "Pipeline", time_range, f"Pipeline - {entity}",
                                   custom_start=custom_start, custom_end=custom_end)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        if entity == COMPANY_NAME:
            fig = make_trend_chart(df, DIVISIONS, "Win Rate", time_range, "Win Rate by Division",
                                   custom_start=custom_start, custom_end=custom_end)
        else:
            fig = make_trend_chart(df, [entity], "Win Rate", time_range, f"Win Rate - {entity}",
                                   custom_start=custom_start, custom_end=custom_end)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-header">Operational Metrics</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        if entity == COMPANY_NAME:
            fig = make_trend_chart(df, DIVISIONS, "Cash Collections", time_range,
                                   "Cash Collections by Division",
                                   custom_start=custom_start, custom_end=custom_end)
        else:
            fig = make_trend_chart(df, [entity], "Cash Collections", time_range,
                                   f"Cash Collections - {entity}",
                                   custom_start=custom_start, custom_end=custom_end)
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        if entity == COMPANY_NAME:
            fig = make_trend_chart(df, DIVISIONS, "Utilization", time_range,
                                   "Utilization by Division",
                                   custom_start=custom_start, custom_end=custom_end)
        else:
            fig = make_trend_chart(df, [entity], "Utilization", time_range,
                                   f"Utilization - {entity}",
                                   custom_start=custom_start, custom_end=custom_end)
        st.plotly_chart(fig, use_container_width=True)


def page_division_detail(df, time_range, division, custom_start=None, custom_end=None):
    label = get_time_range_label(time_range, df, custom_start, custom_end)
    st.markdown(f'<div class="header-bar"><div><div class="header-title">{division} - Division Detail</div>'
                f'<div class="header-subtitle">{label} Performance Overview</div></div></div>',
                unsafe_allow_html=True)
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    current = aggregate_for_period(df, division, time_range, custom_start, custom_end)
    prior = get_prior_period_data(df, division, time_range, custom_start, custom_end)
    render_kpi_cards(current, prior)

    st.markdown('<div class="section-header">Metric Trends</div>', unsafe_allow_html=True)

    tab_labels = list(METRICS.keys())
    tabs = st.tabs(tab_labels)

    # Consistent unit for comparison rankings
    for tab, metric in zip(tabs, tab_labels):
        with tab:
            col1, col2 = st.columns([2, 1])
            with col1:
                fig = make_trend_chart(df, [division], metric, time_range,
                                       f"{metric} - {division}",
                                       custom_start=custom_start, custom_end=custom_end)
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                comparison = get_comparison_data(df, metric, time_range,
                                                custom_start=custom_start, custom_end=custom_end)
                # Determine unit for this metric's comparison values
                comp_unit = None
                if metric in CURRENCY_METRICS:
                    comp_unit = determine_display_unit(list(comparison.values()))

                st.markdown(f"**Division Ranking: {metric}**")
                sorted_comp = sorted(comparison.items(), key=lambda x: x[1], reverse=True)
                for rank, (div, val) in enumerate(sorted_comp, 1):
                    indicator = " ◀" if div == division else ""
                    formatted = format_value(val, metric, unit=comp_unit)
                    color = COLORS["primary_blue"] if div == division else COLORS["text_secondary"]
                    st.markdown(
                        f"<div style='padding:8px 12px; margin:4px 0; border-radius:6px; "
                        f"background:{'#E8F4FD' if div == division else '#F8F9FA'}; "
                        f"font-family:Times New Roman; font-size:16px; color:{color};'>"
                        f"<b>{rank}.</b> {div}: {formatted}{indicator}</div>",
                        unsafe_allow_html=True,
                    )


def page_metric_deep_dive(df, time_range, entity, custom_start=None, custom_end=None):
    label = get_time_range_label(time_range, df, custom_start, custom_end)
    st.markdown(f'<div class="header-bar"><div><div class="header-title">Metric Deep Dive</div>'
                f'<div class="header-subtitle">{entity} | {label}</div></div></div>',
                unsafe_allow_html=True)
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    selected_metric = st.selectbox("Select Metric", list(METRICS.keys()), index=0)

    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown(f'<div class="section-header">{selected_metric} Trend</div>', unsafe_allow_html=True)
        if entity == COMPANY_NAME:
            fig = make_trend_chart(df, DIVISIONS + [COMPANY_NAME], selected_metric, time_range,
                                   custom_start=custom_start, custom_end=custom_end)
        else:
            fig = make_trend_chart(df, [entity, COMPANY_NAME], selected_metric, time_range,
                                   custom_start=custom_start, custom_end=custom_end)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown(f'<div class="section-header">Division Breakdown</div>', unsafe_allow_html=True)
        comparison = get_comparison_data(df, selected_metric, time_range,
                                        custom_start=custom_start, custom_end=custom_end)
        comp_unit = None
        if selected_metric in CURRENCY_METRICS:
            comp_unit = determine_display_unit(list(comparison.values()))

        if selected_metric in CURRENCY_METRICS:
            fig = make_pie_chart(comparison, selected_metric, "Share by Division", unit=comp_unit)
        else:
            fig = make_bar_chart(comparison, selected_metric, "By Division", unit=comp_unit)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown(f'<div class="section-header">{selected_metric} - All Divisions Comparison</div>',
                unsafe_allow_html=True)
    fig = make_bar_chart(comparison, selected_metric, unit=comp_unit)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(f'<div class="section-header">Data Table</div>', unsafe_allow_html=True)
    filtered = filter_by_time_range(df, time_range, custom_start, custom_end)
    table_data = filtered[filtered["Division"] != COMPANY_NAME].copy()
    if not table_data.empty and selected_metric in table_data.columns:
        pivot = table_data.pivot_table(
            index="Date", columns="Division", values=selected_metric, aggfunc="sum"
        ).sort_index(ascending=False)
        pivot.index = pivot.index.strftime("%b %Y")

        if selected_metric in CURRENCY_METRICS:
            styled = pivot.style.format("${:,.0f}")
        elif selected_metric in PERCENT_METRICS:
            styled = pivot.style.format("{:.1f}%")
        elif selected_metric in COUNT_METRICS:
            styled = pivot.style.format("{:.1f}")
        else:
            styled = pivot

        st.dataframe(styled, use_container_width=True, height=350)


def page_division_comparison(df, time_range, custom_start=None, custom_end=None):
    label = get_time_range_label(time_range, df, custom_start, custom_end)
    st.markdown(f'<div class="header-bar"><div><div class="header-title">Division Comparison</div>'
                f'<div class="header-subtitle">All Divisions | {label}</div></div></div>',
                unsafe_allow_html=True)
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Summary table
    st.markdown('<div class="section-header">Performance Summary</div>', unsafe_allow_html=True)

    # Determine consistent unit across all divisions
    all_currency_vals = []
    division_data = {}
    for division in DIVISIONS:
        current = aggregate_for_period(df, division, time_range, custom_start, custom_end)
        division_data[division] = current
        for m in CURRENCY_METRICS:
            all_currency_vals.append(current.get(m, 0))
    unit = determine_display_unit(all_currency_vals)

    summary_rows = []
    for division in DIVISIONS:
        current = division_data[division]
        row = {"Division": division}
        for metric in METRICS:
            if metric in CURRENCY_METRICS:
                row[metric] = format_value(current.get(metric, 0), metric, unit=unit)
            else:
                row[metric] = format_value(current.get(metric, 0), metric)
        summary_rows.append(row)

    summary_df = pd.DataFrame(summary_rows).set_index("Division")
    st.dataframe(summary_df, use_container_width=True)

    # Charts grid
    st.markdown('<div class="section-header">Visual Comparison</div>', unsafe_allow_html=True)

    metrics_pairs = [
        ("Revenue", "EBITDA"),
        ("Pipeline", "Weighted Pipeline"),
        ("Closed Sales", "Win Rate"),
        ("Cash Collections", "Utilization"),
        ("Backlog", "FTE"),
    ]

    for m1, m2 in metrics_pairs:
        col1, col2 = st.columns(2)
        with col1:
            comp = get_comparison_data(df, m1, time_range, custom_start=custom_start, custom_end=custom_end)
            chart_unit = determine_display_unit(list(comp.values())) if m1 in CURRENCY_METRICS else None
            fig = make_bar_chart(comp, m1, m1, unit=chart_unit)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            comp = get_comparison_data(df, m2, time_range, custom_start=custom_start, custom_end=custom_end)
            chart_unit = determine_display_unit(list(comp.values())) if m2 in CURRENCY_METRICS else None
            fig = make_bar_chart(comp, m2, m2, unit=chart_unit)
            st.plotly_chart(fig, use_container_width=True)


def page_data_management(df, time_range, custom_start=None, custom_end=None):
    st.markdown(f'<div class="header-bar"><div><div class="header-title">Data Management</div>'
                f'<div class="header-subtitle">Import, export, and manage dashboard data</div></div></div>',
                unsafe_allow_html=True)
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Upload Data", "Download Template", "Current Data"])

    with tab1:
        st.markdown('<div class="section-header">Upload Excel Data</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="font-family: Times New Roman; font-size: 16px; color: #2C3E50; padding: 16px;
             background: #F0F7FC; border-radius: 8px; border-left: 4px solid #0066B3; margin-bottom: 20px;">
            <b>Instructions:</b><br>
            1. Download the Excel template from the "Download Template" tab<br>
            2. Fill in your data following the template format (monthly data)<br>
            3. Upload the completed file below<br>
            4. Data will replace the current sample data for this session
        </div>
        """, unsafe_allow_html=True)

        uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "xls"])
        if uploaded_file is not None:
            data, error = load_from_excel(uploaded_file)
            if error:
                st.error(f"Error: {error}")
            else:
                data = compute_company_totals(data)
                st.session_state.uploaded_data = data
                st.success(f"Successfully loaded {len(data)} records from {uploaded_file.name}")
                st.dataframe(data.head(20), use_container_width=True)

    with tab2:
        st.markdown('<div class="section-header">Download Data Entry Template</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="font-family: Times New Roman; font-size: 16px; color: #2C3E50; padding: 16px;
             background: #D5F5E3; border-radius: 8px; border-left: 4px solid #7AB648; margin-bottom: 20px;">
            Download the template, fill in your monthly data, then upload it in the "Upload Data" tab.
            The template includes instructions and a sample row.
        </div>
        """, unsafe_allow_html=True)

        template = create_excel_template()
        st.download_button(
            label="Download Excel Template",
            data=template,
            file_name="BlueRidge_Dashboard_Template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    with tab3:
        st.markdown('<div class="section-header">Current Dataset</div>', unsafe_allow_html=True)

        source_label = "Uploaded Data" if "uploaded_data" in st.session_state else "Sample Data"
        st.info(f"Currently using: **{source_label}**")

        display_df = df[df["Division"] != COMPANY_NAME].copy()
        display_df["Date"] = display_df["Date"].dt.strftime("%b %Y")

        col1, col2 = st.columns(2)
        with col1:
            div_filter = st.multiselect("Filter by Division", DIVISIONS, default=DIVISIONS)
        with col2:
            metric_filter = st.multiselect("Show Metrics", list(METRICS.keys()), default=list(METRICS.keys()))

        filtered = display_df[display_df["Division"].isin(div_filter)]
        cols_to_show = ["Date", "Division"] + [m for m in metric_filter if m in filtered.columns]
        st.dataframe(filtered[cols_to_show].sort_values("Date", ascending=False),
                     use_container_width=True, height=500)

        if st.button("Reset to Sample Data"):
            if "uploaded_data" in st.session_state:
                del st.session_state.uploaded_data
            st.rerun()


def page_integration_setup():
    st.markdown(f'<div class="header-bar"><div><div class="header-title">Integration Setup</div>'
                f'<div class="header-subtitle">Configure data source connections</div></div></div>',
                unsafe_allow_html=True)
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    st.markdown("""
    <div style="font-family: Times New Roman; font-size: 16px; color: #2C3E50; padding: 20px;
         background: #FFF8E1; border-radius: 8px; border-left: 4px solid #F39C12; margin-bottom: 20px;">
        <b>Integration Configuration</b><br>
        Direct API connections to Salesforce, Kantata, and NetSuite can be configured below.
        Once connected, data will flow automatically into the dashboard.
        Contact your IT administrator for API credentials.
    </div>
    """, unsafe_allow_html=True)

    for source, config in DATA_SOURCES.items():
        if source == "Excel Upload":
            continue

        with st.expander(f"{source} - {config['description']}", expanded=False):
            st.markdown(f"**Metrics provided:** {', '.join(config['metrics'])}")

            col1, col2 = st.columns(2)
            with col1:
                st.text_input(f"{source} Instance URL", key=f"{source}_url",
                              placeholder=f"https://your-instance.{source.lower()}.com")
                st.text_input(f"{source} API Key / Client ID", key=f"{source}_key",
                              type="password", placeholder="Enter API key")
            with col2:
                st.text_input(f"{source} API Secret / Client Secret", key=f"{source}_secret",
                              type="password", placeholder="Enter API secret")
                st.selectbox(f"{source} Sync Frequency", ["Hourly", "Daily", "Weekly"],
                             key=f"{source}_freq")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.button(f"Test Connection", key=f"{source}_test")
            with col2:
                st.button(f"Save Configuration", key=f"{source}_save")
            with col3:
                st.button(f"Sync Now", key=f"{source}_sync")

    st.markdown('<div class="section-header">Data Flow Architecture</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-family: Times New Roman; font-size: 16px; color: #2C3E50; padding: 20px;
         background: #F0F7FC; border-radius: 8px; margin-bottom: 20px;">
        <table style="width:100%; border-collapse:collapse; font-family: Times New Roman;">
            <tr style="background: #003D6B; color: white;">
                <th style="padding:12px; text-align:left;">Source System</th>
                <th style="padding:12px; text-align:left;">Metrics</th>
                <th style="padding:12px; text-align:left;">Frequency</th>
                <th style="padding:12px; text-align:left;">Method</th>
            </tr>
            <tr style="border-bottom:1px solid #ddd;">
                <td style="padding:12px;"><b>Salesforce</b></td>
                <td style="padding:12px;">Pipeline, Weighted Pipeline, Closed Sales, Win Rate</td>
                <td style="padding:12px;">Daily</td>
                <td style="padding:12px;">REST API / Reports API</td>
            </tr>
            <tr style="border-bottom:1px solid #ddd; background:#F8F9FA;">
                <td style="padding:12px;"><b>Kantata</b></td>
                <td style="padding:12px;">Utilization, Revenue, Backlog, FTE</td>
                <td style="padding:12px;">Daily</td>
                <td style="padding:12px;">REST API</td>
            </tr>
            <tr style="border-bottom:1px solid #ddd;">
                <td style="padding:12px;"><b>NetSuite</b></td>
                <td style="padding:12px;">Revenue, EBITDA, Cash Collections</td>
                <td style="padding:12px;">Daily</td>
                <td style="padding:12px;">SuiteTalk REST / SuiteQL</td>
            </tr>
            <tr style="background:#F8F9FA;">
                <td style="padding:12px;"><b>Excel Upload</b></td>
                <td style="padding:12px;">All Metrics</td>
                <td style="padding:12px;">Manual</td>
                <td style="padding:12px;">File Upload</td>
            </tr>
        </table>
    </div>
    """, unsafe_allow_html=True)


# ─── Export Handler ───
def generate_export(df, time_range, page=None, division=None,
                    custom_start=None, custom_end=None):
    """Generate PowerPoint export."""

    # Single division export
    if page == "Division Detail" and division and division in DIVISIONS:
        try:
            current = aggregate_for_period(df, division, time_range, custom_start, custom_end)
            prior = get_prior_period_data(df, division, time_range, custom_start, custom_end)

            # Determine consistent unit
            currency_vals = [current.get(m, 0) for m in CURRENCY_METRICS]
            unit = determine_display_unit(currency_vals)

            trend_by_metric = {}
            for metric in METRICS:
                trend_by_metric[metric] = get_trend_data(df, division, metric, time_range,
                                                         custom_start=custom_start, custom_end=custom_end)
            prs = export_single_division(
                division, current, prior, trend_by_metric, time_range, unit=unit
            )
            pptx_bytes = save_presentation_to_bytes(prs)
            label = get_time_range_label(time_range, df, custom_start, custom_end).replace(" ", "_")
            return pptx_bytes, None, f"BlueRidge_{division.replace(' ', '_')}_{label}_{datetime.now().strftime('%Y%m%d')}.pptx"
        except Exception as e:
            return None, f"Division export failed: {e}", None

    # Full dashboard export
    current_by_entity = {}
    prior_by_entity = {}
    for ent in ALL_ENTITIES:
        current_by_entity[ent] = aggregate_for_period(df, ent, time_range, custom_start, custom_end)
        prior_by_entity[ent] = get_prior_period_data(df, ent, time_range, custom_start, custom_end)

    # Determine consistent unit across all entities
    all_currency_vals = []
    for ent_data in current_by_entity.values():
        for m in CURRENCY_METRICS:
            all_currency_vals.append(ent_data.get(m, 0))
    unit = determine_display_unit(all_currency_vals)

    comparison_by_metric = {}
    trend_by_metric = {}
    for metric in METRICS:
        comparison_by_metric[metric] = get_comparison_data(df, metric, time_range,
                                                           custom_start=custom_start, custom_end=custom_end)
        trend_by_metric[metric] = {}
        for div in DIVISIONS:
            trend_by_metric[metric][div] = get_trend_data(df, div, metric, time_range,
                                                          custom_start=custom_start, custom_end=custom_end)

    label = get_time_range_label(time_range, df, custom_start, custom_end).replace(" ", "_")
    filename = f"BlueRidge_Dashboard_{label}_{datetime.now().strftime('%Y%m%d')}.pptx"

    try:
        prs = export_full_dashboard(
            current_by_entity, prior_by_entity,
            comparison_by_metric, trend_by_metric,
            time_range, df, unit=unit
        )
        pptx_bytes = save_presentation_to_bytes(prs)
        return pptx_bytes, None, filename
    except ChartRenderError as e:
        # Chart renderer (kaleido) missing or failed: produce KPI-only deck
        prs = create_presentation()
        for ent in ALL_ENTITIES:
            export_executive_summary(
                prs, current_by_entity[ent],
                prior_by_entity.get(ent, {}),
                time_range, ent, unit=unit
            )
        pptx_bytes = save_presentation_to_bytes(prs)
        return pptx_bytes, f"Charts excluded (install kaleido for full export): {e}", filename


# ─── Main App ───
def main():
    df = get_data()
    page, time_range, entity, custom_start, custom_end = render_sidebar(df)

    # Export: generate on button click, cache in session state, show download button
    with st.sidebar:
        if page == "Division Detail" and entity in DIVISIONS:
            export_label = f"Export {entity}"
        else:
            export_label = "Export Full Dashboard"

        if st.button(export_label, use_container_width=True):
            with st.spinner("Generating..."):
                pptx_bytes, warning, filename = generate_export(
                    df, time_range, page, entity, custom_start, custom_end
                )
                if pptx_bytes is not None:
                    st.session_state["pptx_export"] = pptx_bytes
                    st.session_state["pptx_filename"] = filename or "BlueRidge_Dashboard.pptx"
                    if warning:
                        st.warning(warning)
                else:
                    st.error(warning or "Export failed.")

        if "pptx_export" in st.session_state:
            st.download_button(
                label="Download PPTX",
                data=st.session_state["pptx_export"],
                file_name=st.session_state.get("pptx_filename", "BlueRidge_Dashboard.pptx"),
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                use_container_width=True,
            )

        st.markdown("---")
        st.markdown(
            f"<div style='text-align:center; color:#AED6F1; font-size:12px; font-family:Times New Roman;'>"
            f"v2.0 | {datetime.now().strftime('%B %Y')}</div>",
            unsafe_allow_html=True,
        )

    if page == "Executive Summary":
        page_executive_summary(df, time_range, entity, custom_start, custom_end)
    elif page == "Division Detail":
        page_division_detail(df, time_range, entity, custom_start, custom_end)
    elif page == "Metric Deep Dive":
        page_metric_deep_dive(df, time_range, entity, custom_start, custom_end)
    elif page == "Division Comparison":
        page_division_comparison(df, time_range, custom_start, custom_end)
    elif page == "Data Management":
        page_data_management(df, time_range, custom_start, custom_end)
    elif page == "Integration Setup":
        page_integration_setup()


if __name__ == "__main__":
    main()
