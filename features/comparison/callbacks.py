"""
Comparison Feature - Callbacks
Handles all callback functions for the comparison tab
"""

import io
import zipfile
from datetime import datetime
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import dash_mantine_components as dmc
from dash import callback, Input, Output, State, dcc
from dash_iconify import DashIconify

from shared.data_loaders import sample_data, tool_sample
from shared.formatters import format_number
from features.comparison.logic import generate_enhanced_comparison_text_updated
from features.comparison.charts import (
    create_dumbbell_chart_updated,
    create_comparison_heatmap,
    create_division_stacked_chart,
    create_type2_breakdown_charts,
    create_comparison_chart,
    create_ratio_comparison_chart
)
from features.comparison.llm_financial_analyst import analyze_comparison_with_llm


@callback(Output("comparison-date-selector", "data"), Input("main-tabs", "value"))
def populate_comparison_dates(active_tab):
    """
    Populate comparison date selector when comparison tab is activated

    Args:
        active_tab: Currently active tab value

    Returns:
        list: List of date options for the selector
    """
    if active_tab == "comparison":
        unique_dates = sorted(sample_data['date'].dt.to_period('M').unique())
        return [{"value": str(date), "label": str(date)} for date in unique_dates]
    return []


@callback(
    [Output("comparison-filter-values-selector", "data"),
     Output("comparison-filter-values-selector", "disabled"),
     Output("comparison-filter-values-selector", "value")],
    [Input("comparison-filter-selector", "value")]
)
def update_comparison_filter_values(filter_var):
    """
    Update filter values selector based on selected filter variable

    Args:
        filter_var: Selected filter variable ('none', 'Division', 'Type', 'Item', 'Function')

    Returns:
        tuple: (options, disabled_state, selected_values)
    """
    if filter_var == "none":
        return [], True, []
    if filter_var in ['Division', 'Type', 'Item', 'Function']:
        unique_values = sample_data[filter_var].unique()
        options = [{"value": val, "label": val} for val in sorted(unique_values)]
        return options, False, list(unique_values)
    return [], True, []


@callback(
    [Output("comparison-value-boxes", "children"),
     Output("comparison-var1-chart", "figure"),
     Output("comparison-var2-chart", "figure"),
     Output("ratio-comparison-chart", "figure"),
     Output("amount-heatmap-chart", "figure"),
     Output("income-heatmap-chart", "figure"),
     Output("var1-dumbbell-chart", "figure"),
     Output("var2-dumbbell-chart", "figure"),
     Output("amount-division-chart", "figure"),
     Output("income-division-chart", "figure"),
     Output("type2-amount-chart", "figure"),
     Output("type2-income-chart", "figure"),
     Output("comparison-textbox", "value")],
    [Input("comparison-type-selector", "value"),
     Input("comparison-date-selector", "value"),
     Input("comparison-entity-selector", "value"),
     Input("comparison-division-selector", "value"),
     Input("comparison-filter-selector", "value"),
     Input("comparison-filter-values-selector", "value"),
     Input("comparison-stack-selector", "value"),
     Input("comparison-group-selector", "value"),
     Input("financial-analyst-toggle", "checked")]
)
def update_enhanced_comparison_content(selected_type, selected_dates, entity_filter, division_filter,
                                     filter_var, filter_values, stack_var, group_var, enable_llm):
    """
    Main callback to update all comparison content

    Args:
        selected_type: Type of data to display (Total, Best, Type1, Type2, Type3)
        selected_dates: List of selected dates (should be exactly 2)
        entity_filter: Entity filter value
        division_filter: Division filter value
        filter_var: Additional filter variable
        filter_values: Additional filter values
        stack_var: Variable to stack by
        group_var: Variable to group by
        enable_llm: Whether to enable LLM analysis

    Returns:
        tuple: All comparison outputs (value boxes, charts, comparison text)
    """
    if selected_type == "Total":
        amount_col, income_col = "Amount_total", "Income_total"
    elif selected_type == "Best":
        amount_col, income_col = "Amount_Best", "Income_Best"
    elif selected_type == "Type1":
        amount_col, income_col = "Amount_1", "Income_1"
    elif selected_type == "Type2":
        amount_col, income_col = "Amount_2", "Income_2"
    else:
        amount_col, income_col = "Amount_3", "Income_3"

    empty_fig = go.Figure()
    empty_fig.update_layout(title="Select 2 dates to compare", template="plotly_white", height=300, showlegend=False)
    empty_fig.add_annotation(text="Please select exactly 2 dates for comparison", xref="paper", yref="paper",
        x=0.5, y=0.5, xanchor='center', yanchor='middle', showarrow=False, font=dict(size=14, color="gray"))

    if not selected_dates or len(selected_dates) != 2:
        empty_boxes = dmc.Center([dmc.Text("Please select exactly 2 dates to see comparison metrics", c="dimmed", size="sm")], style={"padding": "20px"})
        default_text = "Comparison Analysis:\n\n• Select exactly 2 dates to compare data\n• Use filters and grouping to focus analysis"
        return (empty_boxes, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig,
                empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, default_text)

    date1, date2 = sorted([pd.to_datetime(date + '-01') for date in selected_dates])
    df = sample_data.copy()

    # Create Best columns if needed
    if selected_type == "Best":
        df['Amount_Best'] = df['Amount_1'] + df['Amount_2']
        df['Income_Best'] = df['Income_1'] + df['Income_2']

    df_date1 = df[df['date'].dt.to_period('M') == date1.to_period('M')]
    df_date2 = df[df['date'].dt.to_period('M') == date2.to_period('M')]

    # Apply Entity filter
    if entity_filter != "All":
        df_date1 = df_date1[df_date1['Entity'] == entity_filter]
        df_date2 = df_date2[df_date2['Entity'] == entity_filter]

    # Apply Division filter
    if division_filter != "All":
        df_date1 = df_date1[df_date1['Division'] == division_filter]
        df_date2 = df_date2[df_date2['Division'] == division_filter]

    if filter_var != "none" and filter_var in df.columns and filter_values:
        df_date1 = df_date1[df_date1[filter_var].isin(filter_values)]
        df_date2 = df_date2[df_date2[filter_var].isin(filter_values)]

    amount_old = df_date1[amount_col].sum() if not df_date1.empty else 0
    amount_new = df_date2[amount_col].sum() if not df_date2.empty else 0
    income_old = df_date1[income_col].sum() if not df_date1.empty else 0
    income_new = df_date2[income_col].sum() if not df_date2.empty else 0

    amount_change = ((amount_new - amount_old) / amount_old * 100) if amount_old != 0 else 0
    income_change = ((income_new - income_old) / income_old * 100) if income_old != 0 else 0
    ratio_old = (income_old / amount_old) * 100 if amount_old != 0 else 0
    ratio_new = (income_new / amount_new) * 100 if amount_new != 0 else 0
    ratio_difference = ratio_new - ratio_old

    comparison_text = generate_enhanced_comparison_text_updated(amount_old, amount_new, income_old, income_new, date1, date2,
        filter_var, filter_values, group_var, df_date1, df_date2, selected_type, amount_col, income_col)

    # ========== LLM FINANCIAL ANALYSIS ==========
    # Enable/disable via the "AI Financial Analyst" toggle in the dashboard
    if enable_llm:
        try:
            llm_analysis = analyze_comparison_with_llm(comparison_text)
            comparison_text = comparison_text + "\n\n" + "="*60 + "\n"
            comparison_text = comparison_text + "AI FINANCIAL ANALYSIS:\n" + "="*60 + "\n\n"
            comparison_text = comparison_text + llm_analysis
        except Exception as e:
            comparison_text = comparison_text + "\n\n" + "="*60 + "\n"
            comparison_text = comparison_text + f"AI FINANCIAL ANALYSIS:\n" + "="*60 + "\n\n"
            comparison_text = comparison_text + f"Error: {str(e)}\n\nPlease ensure Azure OpenAI credentials are configured (AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY environment variables)."
    # ========================================================

    value_boxes = dmc.SimpleGrid([
        dmc.Card([dmc.Stack([dmc.Text(f"Amount Change - {selected_type}", size="sm", c="dimmed"),
            dmc.Group([dmc.Text(f"{amount_change:+.1f}%", size="xl", fw=700, c="green" if amount_change >= 0 else "red"),
                DashIconify(icon="material-symbols:trending-up" if amount_change >= 0 else "material-symbols:trending-down", width=24, color="green" if amount_change >= 0 else "red")],
                justify="space-between", align="center"),
            dmc.Text(f"{format_number(amount_old)} → {format_number(amount_new)}", size="xs", c="dimmed")], gap="xs")], withBorder=True, shadow="sm", radius="md", p="md"),
        dmc.Card([dmc.Stack([dmc.Text(f"Income Change - {selected_type}", size="sm", c="dimmed"),
            dmc.Group([dmc.Text(f"{income_change:+.1f}%", size="xl", fw=700, c="green" if income_change >= 0 else "red"),
                DashIconify(icon="material-symbols:trending-up" if income_change >= 0 else "material-symbols:trending-down", width=24, color="green" if income_change >= 0 else "red")],
                justify="space-between", align="center"),
            dmc.Text(f"{format_number(income_old)} → {format_number(income_new)}", size="xs", c="dimmed")], gap="xs")], withBorder=True, shadow="sm", radius="md", p="md"),
        dmc.Card([dmc.Stack([dmc.Text(f"Return Ratio Change - {selected_type}", size="sm", c="dimmed"),
            dmc.Group([dmc.Text(f"{ratio_difference:+.2f}%", size="xl", fw=700, c="green" if ratio_difference >= 0 else "red"),
                DashIconify(icon="material-symbols:trending-up" if ratio_difference >= 0 else "material-symbols:trending-down", width=24, color="green" if ratio_difference >= 0 else "red")],
                justify="space-between", align="center"),
            dmc.Text(f"{ratio_old:.2f}% → {ratio_new:.2f}%", size="xs", c="dimmed")], gap="xs")], withBorder=True, shadow="sm", radius="md", p="md"),
    ], cols=3, spacing="sm", mb="lg")

    amount_chart = create_comparison_chart(df_date1, df_date2, amount_col, "Amount", date1, date2, selected_type, group_var, stack_var, df)
    income_chart = create_comparison_chart(df_date1, df_date2, income_col, "Income", date1, date2, selected_type, group_var, stack_var, df)
    amount_dumbbell = create_dumbbell_chart_updated(df_date1, df_date2, amount_col, date1, date2, group_var, selected_type, "Amount")
    income_dumbbell = create_dumbbell_chart_updated(df_date1, df_date2, income_col, date1, date2, group_var, selected_type, "Income")
    amount_heatmap = create_comparison_heatmap(df_date1, df_date2, amount_col, date1, date2, group_var, selected_type, "Amount")
    income_heatmap = create_comparison_heatmap(df_date1, df_date2, income_col, date1, date2, group_var, selected_type, "Income")
    amount_division = create_division_stacked_chart(df_date1, df_date2, amount_col, "Amount", date1, date2, selected_type, division_filter, entity_filter, filter_var, filter_values, df)
    income_division = create_division_stacked_chart(df_date1, df_date2, income_col, "Income", date1, date2, selected_type, division_filter, entity_filter, filter_var, filter_values, df)

    # Create Type2 breakdown charts (WW, DP, PP)
    type2_amount_chart, type2_income_chart = create_type2_breakdown_charts(date1, date2, filter_var, filter_values, group_var, selected_type)

    # Create ratio comparison chart
    ratio_comparison_fig = create_ratio_comparison_chart(df_date1, df_date2, amount_col, income_col, date1, date2, selected_type, group_var, amount_old, amount_new, income_old, income_new)

    # Add ratio analysis to comparison text
    ratio_text_parts = []
    if group_var != "none" and group_var in ['Type', 'Item', 'Function']:
        groups_date1 = df_date1.groupby(group_var).agg({amount_col: 'sum', income_col: 'sum'}).reset_index()
        groups_date2 = df_date2.groupby(group_var).agg({amount_col: 'sum', income_col: 'sum'}).reset_index()

        groups_date1['ratio'] = (groups_date1[income_col] / groups_date1[amount_col].replace(0, np.nan)) * 100
        groups_date2['ratio'] = (groups_date2[income_col] / groups_date2[amount_col].replace(0, np.nan)) * 100

        all_groups = sorted(set(groups_date1[group_var].tolist() + groups_date2[group_var].tolist()))

        ratio_data_date1 = groups_date1.set_index(group_var)['ratio'].reindex(all_groups, fill_value=0)
        ratio_data_date2 = groups_date2.set_index(group_var)['ratio'].reindex(all_groups, fill_value=0)

        ratio_text_parts.append("\n\nRETURN RATIO ANALYSIS:\n" + "=" * 30 + "\n")
        for group in all_groups:
            r1 = ratio_data_date1.get(group, 0)
            r2 = ratio_data_date2.get(group, 0)
            change = r2 - r1
            direction = "improved" if change > 0 else "declined" if change < 0 else "remained stable"
            ratio_text_parts.append(f"• {group}: {r1:.2f}% → {r2:.2f}% ({direction}, {change:+.2f}pp)\n")
    else:
        ratio_old = (income_old / amount_old * 100) if amount_old != 0 else 0
        ratio_new = (income_new / amount_new * 100) if amount_new != 0 else 0
        change = ratio_new - ratio_old
        direction = "improved" if change > 0 else "declined" if change < 0 else "remained stable"
        ratio_text_parts.append(f"\n\nRETURN RATIO ANALYSIS:\n" + "=" * 30 + "\n")
        ratio_text_parts.append(f"• Overall ratio {direction}: {ratio_old:.2f}% → {ratio_new:.2f}% ({change:+.2f}pp)\n")

    comparison_text = comparison_text + "".join(ratio_text_parts)

    return (value_boxes, amount_chart, income_chart, ratio_comparison_fig,
            amount_heatmap, income_heatmap, amount_dumbbell, income_dumbbell,
            amount_division, income_division, type2_amount_chart, type2_income_chart, comparison_text)


@callback(
    Output("download-dataframe-xlsx", "data"),
    Input("export-excel-btn", "n_clicks"),
    [State("comparison-type-selector", "value"),
     State("comparison-date-selector", "value"),
     State("comparison-entity-selector", "value"),
     State("comparison-division-selector", "value"),
     State("comparison-filter-selector", "value"),
     State("comparison-filter-values-selector", "value"),
     State("comparison-group-selector", "value"),
     State("comparison-stack-selector", "value")],
    prevent_initial_call=True
)
def export_comparison_excel(n_clicks, selected_type, selected_dates, entity_filter, division_filter, filter_var, filter_values, group_var, stack_var):
    """
    Export all comparison chart data to multi-sheet Excel

    Args:
        n_clicks: Number of times button clicked
        selected_type: Type of data (Total, Best, Type1, Type2, Type3)
        selected_dates: List of selected dates
        entity_filter: Entity filter value
        division_filter: Division filter value
        filter_var: Additional filter variable
        filter_values: Additional filter values
        group_var: Variable to group by
        stack_var: Variable to stack by

    Returns:
        dcc.send_bytes: Excel file download
    """
    if n_clicks and selected_dates and len(selected_dates) == 2:
        date1, date2 = sorted([pd.to_datetime(date + '-01') for date in selected_dates])
        df = sample_data.copy()

        # Filter by dates
        df_date1 = df[df['date'].dt.to_period('M') == date1.to_period('M')].copy()
        df_date2 = df[df['date'].dt.to_period('M') == date2.to_period('M')].copy()

        # Apply Entity filter
        if entity_filter != "All":
            df_date1 = df_date1[df_date1['Entity'] == entity_filter]
            df_date2 = df_date2[df_date2['Entity'] == entity_filter]

        # Apply Division filter
        if division_filter != "All":
            df_date1 = df_date1[df_date1['Division'] == division_filter]
            df_date2 = df_date2[df_date2['Division'] == division_filter]

        # Apply filters
        if filter_var != "none" and filter_var in df.columns and filter_values:
            df_date1 = df_date1[df_date1[filter_var].isin(filter_values)]
            df_date2 = df_date2[df_date2[filter_var].isin(filter_values)]

        # Create Excel file with multiple sheets
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Sheet 1: Amount & Income totals
            amount_col = f'Amount_{selected_type}' if selected_type != 'Total' else 'Amount_total'
            income_col = f'Income_{selected_type}' if selected_type != 'Total' else 'Income_total'

            summary_data = pd.DataFrame({
                'Date': [date1.strftime('%Y-%m'), date2.strftime('%Y-%m')],
                'Amount': [df_date1[amount_col].sum(), df_date2[amount_col].sum()],
                'Income': [df_date1[income_col].sum(), df_date2[income_col].sum()]
            })
            summary_data.to_excel(writer, sheet_name='Summary', index=False)

            # Sheet 2: By group/stack variable if selected
            group_col = None
            if group_var != "none" and group_var in ['Division', 'Type', 'Item', 'Function']:
                group_col = group_var
            elif stack_var != "none" and stack_var in ['Division', 'Type', 'Item', 'Function']:
                group_col = stack_var

            if group_col and group_col in df.columns:
                group_data = []
                for date, df_temp in [(date1, df_date1), (date2, df_date2)]:
                    for cat in df_temp[group_col].unique():
                        cat_df = df_temp[df_temp[group_col] == cat]
                        group_data.append({
                            'Date': date.strftime('%b-%Y'),
                            group_col: cat,
                            'Amount': cat_df[amount_col].sum(),
                            'Income': cat_df[income_col].sum()
                        })
                pd.DataFrame(group_data).to_excel(writer, sheet_name=f'By {group_col}', index=False)

            # Sheet 3: Division breakdown if available and not already exported
            if 'Division' in df.columns and group_col != 'Division':
                div_data = []
                for date, df_temp in [(date1, df_date1), (date2, df_date2)]:
                    for div in df_temp['Division'].unique():
                        div_df = df_temp[df_temp['Division'] == div]
                        div_data.append({
                            'Date': date.strftime('%Y-%m'),
                            'Division': div,
                            'Amount': div_df[amount_col].sum(),
                            'Income': div_df[income_col].sum()
                        })
                pd.DataFrame(div_data).to_excel(writer, sheet_name='By Division', index=False)

            # Sheet 4: Tool sample data if available
            try:
                tool_date1 = tool_sample[tool_sample['date'] == date1].copy()
                tool_date2 = tool_sample[tool_sample['date'] == date2].copy()
                if filter_var != "none" and filter_values and filter_var in tool_date1.columns:
                    tool_date1 = tool_date1[tool_date1[filter_var].isin(filter_values)]
                    tool_date2 = tool_date2[tool_date2[filter_var].isin(filter_values)]
                tool_combined = pd.concat([tool_date1, tool_date2])
                if not tool_combined.empty:
                    tool_combined.to_excel(writer, sheet_name='Income Corrections', index=False)
            except:
                pass

        output.seek(0)
        return dcc.send_bytes(output.getvalue(), f"comparison_data_{selected_type}_{datetime.now().strftime('%Y%m%d')}.xlsx")


@callback(
    Output("download-comparison-png", "data"),
    Input("comparison-png-btn", "n_clicks"),
    [State("comparison-var1-chart", "figure"),
     State("comparison-var2-chart", "figure"),
     State("ratio-comparison-chart", "figure"),
     State("amount-heatmap-chart", "figure"),
     State("income-heatmap-chart", "figure"),
     State("var1-dumbbell-chart", "figure"),
     State("var2-dumbbell-chart", "figure"),
     State("amount-division-chart", "figure"),
     State("income-division-chart", "figure"),
     State("comparison-type-selector", "value")],
    prevent_initial_call=True
)
def export_comparison_png(n_clicks, var1_fig, var2_fig, ratio_fig, amt_heat_fig, inc_heat_fig,
                         dump1_fig, dump2_fig, amt_div_fig, inc_div_fig, selected_type):
    """
    Export all Comparison tab charts as PNG files in a ZIP

    Args:
        n_clicks: Number of times button clicked
        var1_fig: Amount comparison chart figure
        var2_fig: Income comparison chart figure
        ratio_fig: Ratio comparison chart figure
        amt_heat_fig: Amount heatmap chart figure
        inc_heat_fig: Income heatmap chart figure
        dump1_fig: Amount dumbbell chart figure
        dump2_fig: Income dumbbell chart figure
        amt_div_fig: Amount division chart figure
        inc_div_fig: Income division chart figure
        selected_type: Type of data (Total, Best, Type1, Type2, Type3)

    Returns:
        dcc.send_bytes: ZIP file download containing PNG images
    """
    if n_clicks:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            charts = [
                (var1_fig, 'amount_comparison'),
                (var2_fig, 'income_comparison'),
                (ratio_fig, 'ratio_comparison'),
                (amt_heat_fig, 'amount_heatmap'),
                (inc_heat_fig, 'income_heatmap'),
                (dump1_fig, 'amount_proportions'),
                (dump2_fig, 'income_proportions'),
                (amt_div_fig, 'amount_by_division'),
                (inc_div_fig, 'income_by_division')
            ]
            for fig_data, name in charts:
                fig = go.Figure(fig_data)
                img_bytes = fig.to_image(format="png", width=1200, height=600)
                zip_file.writestr(f"{name}_{selected_type}.png", img_bytes)

        zip_buffer.seek(0)
        return dcc.send_bytes(zip_buffer.getvalue(), f"comparison_charts_{selected_type}_{datetime.now().strftime('%Y%m%d')}.zip")


@callback(
    Output("save-comparison-btn", "children"),
    Input("save-comparison-btn", "n_clicks"),
    State("comparison-textbox", "value"),
    prevent_initial_call=True
)
def save_comparison(n_clicks, comparison_text):
    """
    Save comparison text (currently just updates button text)

    Args:
        n_clicks: Number of times button clicked
        comparison_text: Text from comparison textbox

    Returns:
        str: Updated button text
    """
    return "Comparison Saved!" if n_clicks else "Save Comparison"
