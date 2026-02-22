"""
Formatting utilities for Dashboard_py
Handles number and value formatting for display and hover text
"""

def format_number(value):
    """
    Format numbers to billions, millions, or thousands

    Args:
        value: Numeric value to format

    Returns:
        Formatted string with appropriate suffix (B, M, K)
    """
    if abs(value) >= 1e8:
        return f"{value/1e9:.2f}B"
    elif abs(value) >= 1e5:
        return f"{value/1e6:.2f}M"
    elif abs(value) >= 1e2:
        return f"{value/1e3:.2f}K"
    else:
        return f"{value:.2f}"

def format_hover_value(value):
    """
    Format hover values with one extra decimal compared to axis

    Args:
        value: Numeric value to format

    Returns:
        Formatted string for hover text with extra precision
    """
    if abs(value) >= 1e8:
        return f"{value/1e9:.3f}B"
    elif abs(value) >= 1e5:
        return f"{value/1e6:.3f}M"
    elif abs(value) >= 1e2:
        return f"{value/1e3:.3f}K"
    else:
        return f"{value:.3f}"
