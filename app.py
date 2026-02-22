"""
Dashboard_py - Main Application Entry Point
Feature-Based Architecture

This is the main entry point for the Dashboard_py application.
All features are modularized into separate packages for better organization and maintainability.

Architecture:
- features/history: Time-series analysis with filtering
- features/comparison: Two-date comparison with LLM analysis
- features/tool: Income correction analysis
- features/scenario: Scenario weight distribution
- shared/: Common utilities (formatters, data loaders, components)
- layouts/: Application layout and navigation
- config: Centralized configuration and color schemes
"""

import dash
from layouts import create_app_layout

# Import feature callbacks to register them with Dash
# The imports trigger callback registration via decorators
import features.history.callbacks
import features.comparison.callbacks
import features.tool.callbacks
import features.scenario.callbacks

# Import navigation callback from layouts
import layouts.main_layout  # Contains navigation toggle callback

# Initialize Dash application
app = dash.Dash(__name__)
server = app.server  # For deployment

# Set application layout
app.layout = create_app_layout()

# Run the application
if __name__ == '__main__':
    from config import APP_CONFIG
    app.run(
        debug=APP_CONFIG['debug'],
        host=APP_CONFIG['host'],
        port=APP_CONFIG['port']
    )
