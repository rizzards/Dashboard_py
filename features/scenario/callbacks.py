"""
Callback functions for the Scenario feature
Handles chart updates and data exports for scenario weight analysis and predictions
"""
from dash import callback, Input, Output, State, dcc
import pandas as pd
from datetime import datetime

from shared.data_loaders import scenw_sample
from features.scenario.charts import create_scenario_weight_chart, create_prediction_chart
from config_macro import get_indicators


@callback(
    Output("scenario-weight-chart", "figure"),
    [Input("scenario-year-range-slider", "value")]
)
def update_scenario_weight_chart(year_range):
    """
    Update the scenario weight chart based on year range selection.

    Args:
        year_range: list - [min_year, max_year] or None

    Returns:
        plotly.graph_objects.Figure - Updated scenario weight distribution chart
    """
    return create_scenario_weight_chart(scenw_sample, year_range)


@callback(Output("download-scenario-data", "data"), Input("scenario-export-btn", "n_clicks"),
    [State("scenario-year-range-slider", "value")], prevent_initial_call=True)
def export_scenario_data(n_clicks, year_range):
    """
    Export scenario weight data to Excel file with pivot and raw data sheets.

    Args:
        n_clicks: int - Number of button clicks
        year_range: list - [min_year, max_year]

    Returns:
        dcc.send_bytes - Excel file download
    """
    if n_clicks:
        import io

        df = scenw_sample.copy()
        df = df[(df['date'].dt.year >= year_range[0]) & (df['date'].dt.year <= year_range[1])]
        df['month'] = df['date'].dt.to_period('M').astype(str)

        # Create pivot table for easier reading
        pivot_data = df.pivot_table(index='month', columns='ScenName',
                                     values='Weight', aggfunc='sum', fill_value=0)
        pivot_data = pivot_data * 100  # Convert to percentage

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Sheet 1: Pivot table
            pivot_data.to_excel(writer, sheet_name='Weight Distribution')

            # Sheet 2: Raw data
            df[['month', 'ScenName', 'Weight']].to_excel(writer, sheet_name='Raw Data', index=False)

        output.seek(0)
        return dcc.send_bytes(output.getvalue(), f"scenario_weights_{datetime.now().strftime('%Y%m%d')}.xlsx")


@callback(Output("download-scenario-png", "data"), Input("scenario-png-btn", "n_clicks"),
    [State("scenario-weight-chart", "figure")], prevent_initial_call=True)
def export_scenario_png(n_clicks, fig_data):
    """
    Export scenario weight chart as PNG in a ZIP archive.

    Args:
        n_clicks: int - Number of button clicks
        fig_data: dict - Chart figure data

    Returns:
        dcc.send_bytes - ZIP file containing PNG download
    """
    if n_clicks:
        import io
        import zipfile
        import plotly.graph_objects as go

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            fig = go.Figure(fig_data)
            img_bytes = fig.to_image(format="png", width=1200, height=700)
            zip_file.writestr(f"scenario_weights_chart.png", img_bytes)

        zip_buffer.seek(0)
        return dcc.send_bytes(zip_buffer.getvalue(), f"scenario_chart_{datetime.now().strftime('%Y%m%d')}.zip")


# ============================================================================
# PREDICTION TAB CALLBACKS
# ============================================================================

@callback(
    Output("prediction-indicator-selector", "data"),
    Input("prediction-country-selector", "value")
)
def update_prediction_indicators(country):
    """
    Update the indicator dropdown based on selected country.

    Args:
        country: str - Selected country name

    Returns:
        list - Indicator options for the selected country
    """
    if country is None:
        return []

    indicators = get_indicators(country)
    return [{"value": ind, "label": ind} for ind in indicators]


@callback(
    Output("prediction-chart", "figure"),
    [Input("prediction-country-selector", "value"),
     Input("prediction-indicator-selector", "value"),
     Input("prediction-historical-toggle", "checked")]
)
def update_prediction_chart(country, indicator, include_historical):
    """
    Update the prediction chart based on country, indicator, and historical toggle.

    Args:
        country: str - Selected country name
        indicator: str - Selected macroeconomic indicator
        include_historical: bool - Whether to include historical time series

    Returns:
        plotly.graph_objects.Figure - Updated prediction chart

    Note:
        This callback calls create_prediction_chart() which is currently a placeholder.
        Replace the chart function in features/scenario/charts.py with your custom implementation.
    """
    if country is None or indicator is None:
        # Return empty figure if no selection
        import plotly.graph_objects as go
        fig = go.Figure()
        fig.add_annotation(
            text="Please select a country and indicator",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            xanchor='center',
            yanchor='middle',
            showarrow=False,
            font=dict(size=14, color="#718096")
        )
        fig.update_layout(template="plotly_white", height=500)
        return fig

    return create_prediction_chart(country, indicator, include_historical)


@callback(
    Output("download-prediction-data", "data"),
    Input("prediction-export-btn", "n_clicks"),
    [State("prediction-country-selector", "value"),
     State("prediction-indicator-selector", "value"),
     State("prediction-historical-toggle", "checked")],
    prevent_initial_call=True
)
def export_prediction_data(n_clicks, country, indicator, include_historical):
    """
    Export prediction data to Excel file.

    ⚠️ PLACEHOLDER FUNCTION ⚠️
    Replace this with your actual data export logic when you implement your custom chart.

    Args:
        n_clicks: int - Number of button clicks
        country: str - Selected country name
        indicator: str - Selected macroeconomic indicator
        include_historical: bool - Whether historical data was included

    Returns:
        dcc.send_bytes - Excel file download

    Usage:
        When you replace the prediction chart function, update this callback to:
        1. Load your actual prediction data
        2. Load historical data (if include_historical is True)
        3. Export to Excel with appropriate sheets
    """
    if n_clicks:
        import io

        # PLACEHOLDER: Replace with your actual data loading logic
        # Example structure:
        # prediction_data = load_prediction_data(country, indicator)
        # historical_data = load_historical_data(country, indicator) if include_historical else None

        # Create placeholder data
        dates = pd.date_range(start='2024-01-01', periods=12, freq='M')
        placeholder_data = pd.DataFrame({
            'Date': dates,
            'Country': country,
            'Indicator': indicator,
            'Forecast': [100 + i * 2 for i in range(12)],
            'Note': 'Placeholder data - replace with actual predictions'
        })

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Sheet 1: Prediction data
            placeholder_data.to_excel(writer, sheet_name='Predictions', index=False)

            # Sheet 2: Metadata
            metadata = pd.DataFrame({
                'Parameter': ['Country', 'Indicator', 'Historical Data Included', 'Export Date'],
                'Value': [country, indicator, str(include_historical), datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
            })
            metadata.to_excel(writer, sheet_name='Metadata', index=False)

        output.seek(0)
        filename = f"prediction_{country.replace(' ', '_')}_{indicator.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        return dcc.send_bytes(output.getvalue(), filename)


@callback(
    Output("download-prediction-png", "data"),
    Input("prediction-png-btn", "n_clicks"),
    [State("prediction-chart", "figure")],
    prevent_initial_call=True
)
def export_prediction_png(n_clicks, fig_data):
    """
    Export prediction chart as PNG in a ZIP archive.

    Args:
        n_clicks: int - Number of button clicks
        fig_data: dict - Chart figure data

    Returns:
        dcc.send_bytes - ZIP file containing PNG download
    """
    if n_clicks:
        import io
        import zipfile
        import plotly.graph_objects as go

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            fig = go.Figure(fig_data)
            img_bytes = fig.to_image(format="png", width=1200, height=700)
            zip_file.writestr("prediction_chart.png", img_bytes)

        zip_buffer.seek(0)
        return dcc.send_bytes(zip_buffer.getvalue(), f"prediction_chart_{datetime.now().strftime('%Y%m%d')}.zip")
