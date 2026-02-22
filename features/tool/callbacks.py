"""
Callback functions for the Tool feature
Handles chart updates and data exports
"""
from dash import callback, Input, Output, State, dcc
import pandas as pd
from datetime import datetime

from shared.data_loaders import sample_data, tool_sample
from features.tool.charts import create_tool_income_chart


@callback(
    Output("tool-income-chart", "figure"),
    [Input("tool-division-filter", "value"), Input("tool-item-filter", "value"),
     Input("tool-function-filter", "value"), Input("tool-year-range-slider", "value")]
)
def update_tool_chart(division_filter, item_filter, function_filter, year_range):
    """
    Update the tool income chart based on filter selections.

    Args:
        division_filter: str - Selected division or "none"
        item_filter: str - Selected item or "none"
        function_filter: str - Selected function or "none"
        year_range: list - [min_year, max_year]

    Returns:
        plotly.graph_objects.Figure - Updated chart
    """
    return create_tool_income_chart(sample_data, tool_sample, division_filter,
                                   item_filter, function_filter, year_range)


@callback(Output("download-tool-data", "data"), Input("tool-export-btn", "n_clicks"),
    [State("tool-division-filter", "value"), State("tool-item-filter", "value"),
     State("tool-function-filter", "value"), State("tool-year-range-slider", "value")],
    prevent_initial_call=True)
def export_tool_data(n_clicks, division_filter, item_filter, function_filter, year_range):
    """
    Export Tool tab data to multi-sheet Excel file.

    Args:
        n_clicks: int - Number of button clicks
        division_filter: str - Selected division or "none"
        item_filter: str - Selected item or "none"
        function_filter: str - Selected function or "none"
        year_range: list - [min_year, max_year]

    Returns:
        dcc.send_bytes - Excel file download
    """
    if n_clicks:
        import io

        # Filter main data
        df_main = sample_data.copy()
        df_main = df_main[(df_main['date'].dt.year >= year_range[0]) & (df_main['date'].dt.year <= year_range[1])]
        if division_filter != "none":
            df_main = df_main[df_main['Division'] == division_filter]
        if item_filter != "none":
            df_main = df_main[df_main['Item'] == item_filter]
        if function_filter != "none":
            df_main = df_main[df_main['Function'] == function_filter]

        # Filter tool data
        df_corr = tool_sample.copy()
        df_corr = df_corr[(df_corr['date'].dt.year >= year_range[0]) & (df_corr['date'].dt.year <= year_range[1])]
        if division_filter != "none":
            df_corr = df_corr[df_corr['Division'] == division_filter]
        if item_filter != "none":
            df_corr = df_corr[df_corr['Item'] == item_filter]
        if function_filter != "none":
            df_corr = df_corr[df_corr['Function'] == function_filter]

        # Create Excel with multiple sheets
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Sheet 1: Original Income
            main_agg = df_main.groupby('date')['Income_total'].sum().reset_index()
            main_agg['month'] = main_agg['date'].dt.to_period('M').astype(str)
            main_agg[['month', 'Income_total']].to_excel(writer, sheet_name='Original Income', index=False)

            # Sheet 2: Income Corrections
            corr_agg = df_corr.groupby('date')['Income_corr'].sum().reset_index()
            corr_agg['month'] = corr_agg['date'].dt.to_period('M').astype(str)
            corr_agg[['month', 'Income_corr']].to_excel(writer, sheet_name='Income Corrections', index=False)

            # Sheet 3: Combined view
            merged = pd.merge(main_agg[['month', 'Income_total']], corr_agg[['month', 'Income_corr']],
                             on='month', how='outer').fillna(0)
            merged['Total_with_Correction'] = merged['Income_total'] + merged['Income_corr']
            merged.to_excel(writer, sheet_name='Combined', index=False)


        output.seek(0)
        return dcc.send_bytes(output.getvalue(), f"tool_data_{datetime.now().strftime('%Y%m%d')}.xlsx")


@callback(Output("download-tool-png", "data"), Input("tool-png-btn", "n_clicks"),
    [State("tool-income-chart", "figure")], prevent_initial_call=True)
def export_tool_png(n_clicks, tool_fig):
    """
    Export Tool tab chart as PNG in a ZIP archive.

    Args:
        n_clicks: int - Number of button clicks
        tool_fig: dict - Chart figure data

    Returns:
        dcc.send_bytes - ZIP file containing PNG download
    """
    if n_clicks:
        import io
        import zipfile
        import plotly.graph_objects as go

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            fig = go.Figure(tool_fig)
            img_bytes = fig.to_image(format="png", width=1200, height=700)
            zip_file.writestr(f"tool_income_chart.png", img_bytes)

        zip_buffer.seek(0)
        return dcc.send_bytes(zip_buffer.getvalue(), f"tool_chart_{datetime.now().strftime('%Y%m%d')}.zip")
