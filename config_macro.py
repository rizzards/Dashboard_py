"""
Macroeconomic Configuration
Contains country-specific macroeconomic indicator definitions for the Prediction tab

This file can be easily modified to add/remove countries or indicators.
"""

# Macroeconomic indicators by country
# Structure: {Country: [list of macro indicators]}
MACRO_INDICATORS = {
    "United States": [
        "GDP Growth Rate",
        "Unemployment Rate",
        "Inflation Rate (CPI)",
        "Interest Rate (Federal Funds)",
        "Consumer Confidence Index",
        "Industrial Production Index",
        "Retail Sales Growth",
        "Housing Starts",
        "Trade Balance",
        "S&P 500 Index"
    ],
    "European Union": [
        "GDP Growth Rate",
        "Unemployment Rate",
        "Inflation Rate (HICP)",
        "ECB Interest Rate",
        "Consumer Confidence Index",
        "Industrial Production Index",
        "Retail Sales Growth",
        "PMI Composite",
        "Trade Balance",
        "Euro Stoxx 50 Index"
    ],
    "United Kingdom": [
        "GDP Growth Rate",
        "Unemployment Rate",
        "Inflation Rate (CPI)",
        "Bank of England Base Rate",
        "Consumer Confidence Index",
        "Industrial Production Index",
        "Retail Sales Growth",
        "PMI Composite",
        "Trade Balance",
        "FTSE 100 Index"
    ],
    "China": [
        "GDP Growth Rate",
        "Unemployment Rate",
        "Inflation Rate (CPI)",
        "Loan Prime Rate",
        "Consumer Confidence Index",
        "Industrial Production Index",
        "Retail Sales Growth",
        "PMI Manufacturing",
        "Trade Balance",
        "Shanghai Composite Index"
    ],
    "Japan": [
        "GDP Growth Rate",
        "Unemployment Rate",
        "Inflation Rate (CPI)",
        "Bank of Japan Policy Rate",
        "Consumer Confidence Index",
        "Industrial Production Index",
        "Retail Sales Growth",
        "Tankan Index",
        "Trade Balance",
        "Nikkei 225 Index"
    ],
    "Germany": [
        "GDP Growth Rate",
        "Unemployment Rate",
        "Inflation Rate (CPI)",
        "ECB Interest Rate",
        "IFO Business Climate Index",
        "Industrial Production Index",
        "Retail Sales Growth",
        "PMI Composite",
        "Trade Balance",
        "DAX Index"
    ],
    "Canada": [
        "GDP Growth Rate",
        "Unemployment Rate",
        "Inflation Rate (CPI)",
        "Bank of Canada Overnight Rate",
        "Consumer Confidence Index",
        "Industrial Production Index",
        "Retail Sales Growth",
        "Housing Starts",
        "Trade Balance",
        "TSX Composite Index"
    ],
    "Australia": [
        "GDP Growth Rate",
        "Unemployment Rate",
        "Inflation Rate (CPI)",
        "RBA Cash Rate",
        "Consumer Confidence Index",
        "Industrial Production Index",
        "Retail Sales Growth",
        "PMI Composite",
        "Trade Balance",
        "ASX 200 Index"
    ]
}

# Default selections
DEFAULT_COUNTRY = "United States"
DEFAULT_INDICATOR = "GDP Growth Rate"

# Chart configuration for prediction
PREDICTION_CHART_CONFIG = {
    'template': 'plotly_white',
    'height': 500,
    'show_historical_default': True  # Default state for historical toggle
}

def get_countries():
    """Returns list of available countries"""
    return list(MACRO_INDICATORS.keys())

def get_indicators(country):
    """Returns list of indicators for a specific country"""
    return MACRO_INDICATORS.get(country, [])

def get_all_unique_indicators():
    """Returns all unique indicators across all countries"""
    all_indicators = set()
    for indicators in MACRO_INDICATORS.values():
        all_indicators.update(indicators)
    return sorted(list(all_indicators))
