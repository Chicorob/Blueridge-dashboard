"""
BlueRidge Life Sciences Dashboard Configuration
"""

# Company and Division Setup
COMPANY_NAME = "BlueRidge Life Sciences"
DIVISIONS = ["Clintrex", "ToxStrategies", "Suttons Creek", "Modality", "Design Science"]
ALL_ENTITIES = [COMPANY_NAME] + DIVISIONS

# Metrics Configuration
METRICS = {
    "Pipeline": {"format": "currency", "prefix": "$", "suffix": "", "decimals": 0},
    "Weighted Pipeline": {"format": "currency", "prefix": "$", "suffix": "", "decimals": 0},
    "Closed Sales": {"format": "currency", "prefix": "$", "suffix": "", "decimals": 0},
    "Win Rate": {"format": "percent", "prefix": "", "suffix": "%", "decimals": 1},
    "Revenue": {"format": "currency", "prefix": "$", "suffix": "", "decimals": 0},
    "EBITDA": {"format": "currency", "prefix": "$", "suffix": "", "decimals": 0},
    "Cash Collections": {"format": "currency", "prefix": "$", "suffix": "", "decimals": 0},
    "Utilization": {"format": "percent", "prefix": "", "suffix": "%", "decimals": 1},
    "Backlog": {"format": "currency", "prefix": "$", "suffix": "", "decimals": 0},
    "FTE": {"format": "count", "prefix": "", "suffix": "", "decimals": 1},
}

CURRENCY_METRICS = ["Pipeline", "Weighted Pipeline", "Closed Sales", "Revenue", "EBITDA", "Cash Collections", "Backlog"]
PERCENT_METRICS = ["Win Rate", "Utilization"]
COUNT_METRICS = ["FTE"]

# Aggregation classification:
# FLOW_METRICS are summed over a period (income-statement style)
# POINT_IN_TIME_METRICS use the latest month-end value (balance-sheet style)
FLOW_METRICS = ["Closed Sales", "Revenue", "EBITDA", "Cash Collections"]
POINT_IN_TIME_METRICS = ["Pipeline", "Weighted Pipeline", "Win Rate", "Utilization", "Backlog", "FTE"]

# Time Range Options
TIME_RANGES = ["Month", "Quarter", "Current Year", "Trailing 12 Months", "Custom Range"]

# Color Palette - Blue and Green with White Background
COLORS = {
    "primary_blue": "#0066B3",
    "dark_blue": "#003D6B",
    "medium_blue": "#2E86C1",
    "light_blue": "#AED6F1",
    "pale_blue": "#D6EAF8",
    "primary_green": "#7AB648",
    "dark_green": "#4A7A2E",
    "medium_green": "#5DAE3B",
    "light_green": "#ABEBC6",
    "pale_green": "#D5F5E3",
    "white": "#FFFFFF",
    "light_gray": "#F8F9FA",
    "medium_gray": "#BDC3C7",
    "dark_gray": "#2C3E50",
    "text_primary": "#1A1A2E",
    "text_secondary": "#566573",
    "positive": "#27AE60",
    "negative": "#E74C3C",
    "neutral": "#7F8C8D",
}

# Division Colors for Charts
DIVISION_COLORS = {
    "Clintrex": "#0066B3",
    "ToxStrategies": "#7AB648",
    "Suttons Creek": "#2E86C1",
    "Modality": "#003D6B",
    "Design Science": "#5DAE3B",
    COMPANY_NAME: "#1A1A2E",
}

# Font Configuration
FONT_FAMILY = "Times New Roman, Times, serif"
FONT_SIZE_TITLE = 28
FONT_SIZE_HEADER = 22
FONT_SIZE_SUBHEADER = 18
FONT_SIZE_BODY = 16
FONT_SIZE_SMALL = 14

# Data Source Configuration
DATA_SOURCES = {
    "Salesforce": {
        "metrics": ["Pipeline", "Weighted Pipeline", "Closed Sales", "Win Rate"],
        "description": "CRM data for sales pipeline and win rates",
    },
    "Kantata": {
        "metrics": ["Utilization", "Revenue", "Backlog", "FTE"],
        "description": "Professional services automation for utilization, project revenue, backlog, and headcount",
    },
    "NetSuite": {
        "metrics": ["Revenue", "EBITDA", "Cash Collections"],
        "description": "ERP/Financial data for revenue, EBITDA, and collections",
    },
    "Excel Upload": {
        "metrics": list(METRICS.keys()),
        "description": "Manual data entry via Excel template upload",
    },
}
