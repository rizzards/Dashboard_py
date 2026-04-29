"""
Callback functions for the History feature
Handles all interactive behavior for the history tab
"""
from dash import callback, Input, Output, State, dcc
import dash_mantine_components as dmc
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime

from shared.data_loaders import sample_data, events_data
from shared.formatters import format_number
from features.history.charts import create_bar_chart, create_ratio_chart, create_income_diff_chart


# Entity → Division valid combinations (same mapping as comparison tab)
ENTITY_DIVISION_MAP = {
    "All": ["All"],
    "EU":  ["All", "France", "Stockholm"],
}


@callback(
    Output("division-selector", "data"),
    Output("division-selector", "value"),
    Input("entity-selector", "value"),
    State("division-selector", "value"),
)
def constrain_history_division_by_entity(entity, current_division):
    """Restrict Division options to those valid for the selected Entity."""
    allowed = ENTITY_DIVISION_MAP.get(entity, ["All"])
    options = [{"value": d, "label": d} for d in allowed]
    new_value = current_division if current_division in allowed else "All"
    return options, new_value


@callback(
    [Output("filter-values-selector", "data"),
     Output("filter-values-selector", "disabled"),
     Output("filter-values-selector", "value")],
    [Input("filter-selector", "value")]
)
def update_filter_values(filter_var):
    """
    Update the filter values dropdown based on selected filter variable.

    Args:
        filter_var: Selected filter variable (Division, Type, Item, Function, or 'none')

    Returns:
        Tuple of (options list, disabled state, default values)
    """
    if filter_var == "none":
        return [], True, []
    if filter_var in ['Division', 'Type', 'Item', 'Function']:
        unique_values = sample_data[filter_var].unique()
        options = [{"value": val, "label": val} for val in sorted(unique_values)]
        return options, False, list(unique_values)
    return [], True, []


@callback(
    [Output("history-summary-boxes", "children"),
     Output("amount-barchart", "figure"),
     Output("income-barchart", "figure"),
     Output("income-diff-chart", "figure"),
     Output("ratio-chart", "figure")],
    [Input("variable-selector", "value"),
     Input("entity-selector", "value"),
     Input("division-selector", "value"),
     Input("filter-selector", "value"),
     Input("filter-values-selector", "value"),
     Input("stack-selector", "value"),
     Input("group-selector", "value"),
     Input("year-range-slider", "value")]
)
def update_barcharts(selected_type, entity_filter, division_filter, filter_var,
                     filter_values, stack_var, group_var, year_range):
    """
    Update all history tab charts based on user selections.

    Args:
        selected_type: Variable type (Total, Best, Type1, Type2, Type3)
        entity_filter: Entity filter value
        division_filter: Division filter value
        filter_var: Additional filter variable
        filter_values: Values for additional filter
        stack_var: Variable to stack by
        group_var: Variable to group by
        year_range: [min_year, max_year] range

    Returns:
        Tuple of (summary_boxes, amount_chart, income_chart, income_diff_chart, ratio_chart)
    """
    # Determine column names based on selected type
    if selected_type == "Total":
        amount_col, income_col = "Amount_total", "Income_total"
    elif selected_type == "Best":
        # Best = Type1 + Type2
        amount_col, income_col = "Amount_Best", "Income_Best"
    elif selected_type == "Type1":
        amount_col, income_col = "Amount_1", "Income_1"
    elif selected_type == "Type2":
        amount_col, income_col = "Amount_2", "Income_2"
    else:
        amount_col, income_col = "Amount_3", "Income_3"

    df = sample_data.copy()

    # Create Best columns if needed
    if selected_type == "Best":
        df['Amount_Best'] = df['Amount_1'] + df['Amount_2']
        df['Income_Best'] = df['Income_1'] + df['Income_2']

    # Apply year range filter
    df = df[(df['date'].dt.year >= year_range[0]) & (df['date'].dt.year <= year_range[1])]

    # Apply Entity filter
    if entity_filter != "All":
        df = df[df['Entity'] == entity_filter]

    # Apply Division filter
    if division_filter != "All":
        df = df[df['Division'] == division_filter]

    # Apply additional filter
    if filter_var != "none" and filter_var in df.columns and filter_values:
        df = df[df[filter_var].isin(filter_values)]

    # Add month column for grouping
    df['month'] = df['date'].dt.to_period('M').astype(str)

    # Calculate summary metrics
    monthly_totals = df.groupby('month').agg({
        amount_col: 'sum',
        income_col: 'sum'
    }).reset_index()

    avg_amount = monthly_totals[amount_col].mean()
    avg_income = monthly_totals[income_col].mean()
    avg_ratio = (monthly_totals[income_col].sum() / monthly_totals[amount_col].sum()) \
                if monthly_totals[amount_col].sum() != 0 else 0

    # Create summary boxes
    summary_boxes = dmc.SimpleGrid([
        dmc.Card([
            dmc.Stack([
                dmc.Text(f"Average Amount - {selected_type}", size="sm", c="dimmed"),
                dmc.Text(format_number(avg_amount), size="xl", fw=700, c="blue"),
                dmc.Text("Monthly average", size="xs", c="dimmed")
            ], gap="xs")
        ], withBorder=True, shadow="sm", radius="md", p="md"),
        dmc.Card([
            dmc.Stack([
                dmc.Text(f"Average Income - {selected_type}", size="sm", c="dimmed"),
                dmc.Text(format_number(avg_income), size="xl", fw=700, c="orange"),
                dmc.Text("Monthly average", size="xs", c="dimmed")
            ], gap="xs")
        ], withBorder=True, shadow="sm", radius="md", p="md"),
        dmc.Card([
            dmc.Stack([
                dmc.Text(f"Return Ratio - {selected_type}", size="sm", c="dimmed"),
                dmc.Text(f"{avg_ratio*100:.2f}%", size="xl", fw=700, c="green"),
                dmc.Text("Income/Amount ratio", size="xs", c="dimmed")
            ], gap="xs")
        ], withBorder=True, shadow="sm", radius="md", p="md"),
    ], cols=3, spacing="sm", mb="lg")

    # Create charts
    amount_chart = create_bar_chart(df, amount_col, f"Amount - {selected_type}", stack_var, group_var)
    income_chart = create_bar_chart(df, income_col, f"Income - {selected_type}", stack_var, group_var)
    income_diff_chart = create_income_diff_chart(df, income_col, selected_type, stack_var, group_var)
    ratio_chart = create_ratio_chart(df, amount_col, income_col, group_var, selected_type)

    return summary_boxes, amount_chart, income_chart, income_diff_chart, ratio_chart


@callback(
    Output("download-history-data", "data"),
    Input("history-export-btn", "n_clicks"),
    [State("variable-selector", "value"),
     State("year-range-slider", "value"),
     State("filter-selector", "value"),
     State("filter-values-selector", "value"),
     State("stack-selector", "value"),
     State("group-selector", "value")],
    prevent_initial_call=True
)
def export_history_data(n_clicks, selected_type, year_range, filter_var,
                       filter_values, stack_var, group_var):
    """
    Export all History tab chart data to multi-sheet Excel.

    Args:
        n_clicks: Number of button clicks
        selected_type: Variable type (Total, Best, Type1, Type2, Type3)
        year_range: [min_year, max_year] range
        filter_var: Additional filter variable
        filter_values: Values for additional filter
        stack_var: Variable to stack by
        group_var: Variable to group by

    Returns:
        Excel file download
    """
    if n_clicks:
        import io

        df = sample_data.copy()

        # Create Best columns if needed
        if selected_type == "Best":
            df['Amount_Best'] = df['Amount_1'] + df['Amount_2']
            df['Income_Best'] = df['Income_1'] + df['Income_2']

        # Apply filters
        df = df[(df['date'].dt.year >= year_range[0]) & (df['date'].dt.year <= year_range[1])]
        if filter_var != "none" and filter_var in df.columns and filter_values:
            df = df[df[filter_var].isin(filter_values)]

        # Determine column names
        amount_col = f'Amount_{selected_type}' if selected_type not in ['Total', 'Best'] \
                     else f'Amount_{selected_type.lower()}'
        income_col = f'Income_{selected_type}' if selected_type not in ['Total', 'Best'] \
                     else f'Income_{selected_type.lower()}'

        # Determine grouping column for export
        group_col = None
        if stack_var != "none" and stack_var in ['Division', 'Type', 'Item', 'Function']:
            group_col = stack_var
        elif group_var != "none" and group_var in ['Division', 'Type', 'Item', 'Function']:
            group_col = group_var

        # Create Excel with multiple sheets
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Sheet 1: Amount chart data
            if group_col:
                amount_data = df.groupby([df['date'].dt.to_period('M'), group_col])[amount_col].sum().reset_index()
                amount_data.columns = ['Month', group_col, 'Amount']
            else:
                amount_data = df.groupby(df['date'].dt.to_period('M'))[amount_col].sum().reset_index()
                amount_data.columns = ['Month', 'Amount']
            amount_data['Month'] = amount_data['Month'].astype(str)
            amount_data.to_excel(writer, sheet_name='Amount Chart', index=False)

            # Sheet 2: Income chart data
            if group_col:
                income_data = df.groupby([df['date'].dt.to_period('M'), group_col])[income_col].sum().reset_index()
                income_data.columns = ['Month', group_col, 'Income']
            else:
                income_data = df.groupby(df['date'].dt.to_period('M'))[income_col].sum().reset_index()
                income_data.columns = ['Month', 'Income']
            income_data['Month'] = income_data['Month'].astype(str)
            income_data.to_excel(writer, sheet_name='Income Chart', index=False)

            # Sheet 3: Ratio chart data
            if group_col:
                ratio_data = df.groupby([df['date'].dt.to_period('M'), group_col]).agg({
                    amount_col: 'sum',
                    income_col: 'sum'
                }).reset_index()
                ratio_data['Ratio'] = (ratio_data[income_col] / ratio_data[amount_col].replace(0, np.nan)) * 100
                ratio_data.columns = ['Month', group_col, 'Amount', 'Income', 'Ratio (%)']
            else:
                ratio_data = df.groupby(df['date'].dt.to_period('M')).agg({
                    amount_col: 'sum',
                    income_col: 'sum'
                }).reset_index()
                ratio_data['Ratio'] = (ratio_data[income_col] / ratio_data[amount_col].replace(0, np.nan)) * 100
                ratio_data.columns = ['Month', 'Amount', 'Income', 'Ratio (%)']
            ratio_data['Month'] = ratio_data['Month'].astype(str)
            ratio_data.to_excel(writer, sheet_name='Ratio Chart', index=False)

        output.seek(0)
        return dcc.send_bytes(
            output.getvalue(),
            f"history_data_{selected_type}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        )


@callback(
    Output("download-history-png", "data"),
    Input("history-png-btn", "n_clicks"),
    [State("amount-barchart", "figure"),
     State("income-barchart", "figure"),
     State("income-diff-chart", "figure"),
     State("ratio-chart", "figure"),
     State("variable-selector", "value")],
    prevent_initial_call=True
)
def export_history_png(n_clicks, amount_fig, income_fig, income_diff_fig,
                       ratio_fig, selected_type):
    """
    Export all History tab charts as PNG files in a ZIP.

    Args:
        n_clicks: Number of button clicks
        amount_fig: Amount chart figure
        income_fig: Income chart figure
        income_diff_fig: Income difference chart figure
        ratio_fig: Ratio chart figure
        selected_type: Variable type (Total, Best, Type1, Type2, Type3)

    Returns:
        ZIP file download containing PNG images
    """
    if n_clicks:
        import io
        import zipfile

        try:
            # Create ZIP file in memory
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Convert each figure to PNG
                for fig_data, name in [(amount_fig, 'amount_chart'),
                                      (income_fig, 'income_chart'),
                                      (income_diff_fig, 'income_diff_chart'),
                                      (ratio_fig, 'ratio_chart')]:
                    fig = go.Figure(fig_data)
                    img_bytes = fig.to_image(format="png", width=1200, height=600, engine="kaleido")
                    zip_file.writestr(f"{name}_{selected_type}.png", img_bytes)

            zip_buffer.seek(0)
            return dcc.send_bytes(
                zip_buffer.getvalue(),
                f"history_charts_{selected_type}_{datetime.now().strftime('%Y%m%d')}.zip"
            )
        except Exception as e:
            # If kaleido fails, return error message as text file
            error_msg = f"""PNG Export Error
The kaleido package is not properly installed.
Error details: {str(e)}
"""
            error_buffer = io.BytesIO(error_msg.encode())
            return dcc.send_bytes(error_buffer.getvalue(), f"PNG_EXPORT_ERROR.txt")


@callback(
    [Output("events-date-selector", "data"),
     Output("events-division-selector", "data"),
     Output("events-metric-selector", "data")],
    Input("main-tabs", "value")
)
def populate_events_filters(active_tab):
    """
    Populate events filter dropdowns when history tab is active.

    Args:
        active_tab: Current active tab value

    Returns:
        Tuple of (date_options, division_options, metric_options)
    """
    if active_tab == "history" and not events_data.empty:
        # Get unique dates from events_data
        dates = sorted(events_data['Date'].dt.to_period('M').astype(str).unique(), reverse=True)
        date_options = [{"value": date, "label": date} for date in dates]

        # Get unique divisions from events_data
        divisions = sorted(events_data['Division'].unique()) if 'Division' in events_data.columns else []
        division_options = [{"value": div, "label": div} for div in divisions]

        # Get unique metrics from events_data
        metrics = sorted(events_data['Metric'].unique()) if 'Metric' in events_data.columns else []
        metric_options = [{"value": metric, "label": metric} for metric in metrics]

        return date_options, division_options, metric_options
    return [], [], []


@callback(
    Output("events-textbox", "value"),
    [Input("events-date-selector", "value"),
     Input("events-division-selector", "value"),
     Input("events-metric-selector", "value"),
     Input("events-details-toggle", "checked")]
)
def update_events_summary(selected_date, selected_division, selected_metric, include_details):
    """
    Update events summary textbox based on selected filters.

    Args:
        selected_date: Selected date (YYYY-MM format)
        selected_division: Selected division
        selected_metric: Selected metric
        include_details: Whether to include additional details

    Returns:
        Summary text string
    """
    if not selected_date or not selected_division or not selected_metric:
        return "Select date, division, and metric to view summary..."

    # Convert selected_date to datetime for filtering
    date_obj = pd.to_datetime(selected_date + '-01')

    # Filter events data
    filtered = events_data[
        (events_data['Date'] == date_obj) &
        (events_data['Division'] == selected_division) &
        (events_data['Metric'] == selected_metric)
    ]

    if filtered.empty:
        return f"No summary available for {selected_metric} in {selected_division} for {selected_date}."

    # Get the summary text
    row = filtered.iloc[0]
    summary_text = row['Summary']

    # Add additional details if toggle is on
    if include_details and pd.notna(row['Additional_Details']):
        summary_text += f"\n\n{row['Additional_Details']}"

    return summary_text
