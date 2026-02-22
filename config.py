"""
Configuration module for Dashboard_py
Contains all application settings, color schemes, and constants
"""
import os

# ============================================================================
# APPLICATION CONFIGURATION
# ============================================================================
APP_CONFIG = {
    'debug': True,
    'port': 8050,
    'host': '0.0.0.0',
    'title': 'Financial Dashboard - Dashboard_py'
}

# ============================================================================
# DATA PATHS
# ============================================================================
DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

DATA_FILES = {
    'main': os.path.join(DATA_DIR, 'Example_df.csv'),
    'correction': os.path.join(DATA_DIR, 'Example_correction.csv'),
    'scenario': os.path.join(DATA_DIR, 'Example_scenw.csv'),
    'type_detail': os.path.join(DATA_DIR, 'Type_detail.csv'),
    'events': os.path.join(DATA_DIR, 'Events.xlsx')
}

# ============================================================================
# COLOR CONFIGURATION
# ============================================================================
CHART_COLORS = {
    # Comparison colors
    'comparison_colors': ['#718096', '#E53E3E'],  # Gray (baseline), Red (new)

    # Series color sequences based on number of series
    'sequence_8plus': ['#dbdbdb', '#adadad', '#838281', '#5b5958', '#373332', '#364a7c', '#556ea3', '#7794c2', '#9abddc', '#bde9f1'],
    'sequence_6plus': ['#dbdbdb', '#a3a2a2', '#6f6d6d', '#403c3b', '#3d5387', '#6681b4', '#92b3d6', '#bde9f1'],
    'sequence_4plus': ['#dbdbdb', '#919090', '#4f4c4b', '#4a6198', '#83a2cb', '#bde9f1'],
    'sequence_2plus': ['#dbdbdb', '#6f6d6d', '#6681b4', '#bde9f1'],
}

def get_color_sequence(chart_type, n_colors=1, is_comparison=False):
    """
    Returns appropriate color sequence based on chart type and context.

    Args:
        chart_type: str - 'bar', 'line', 'stacked', 'grouped'
        n_colors: int - number of colors needed
        is_comparison: bool - True for comparison charts (2 dates)

    Returns:
        list - color code(s)
    """
    if is_comparison:
        return CHART_COLORS['comparison_colors']

    # Select sequence based on number of colors needed
    if n_colors > 8:
        return CHART_COLORS['sequence_8plus'][:n_colors]
    elif n_colors > 6:
        return CHART_COLORS['sequence_6plus'][:n_colors]
    elif n_colors > 4:
        return CHART_COLORS['sequence_4plus'][:n_colors]
    elif n_colors > 2:
        return CHART_COLORS['sequence_2plus'][:n_colors]
    elif n_colors == 2:
        return CHART_COLORS['sequence_2plus'][:2]
    else:
        return [CHART_COLORS['sequence_2plus'][1]]  # Single color - use second from 2plus sequence

# ============================================================================
# DATA SCALING FACTOR
# ============================================================================
DATA_SCALE_FACTOR = 1000000  # Multiply all numeric columns by this factor
