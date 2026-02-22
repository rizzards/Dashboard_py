"""
Chart generation functions for the Tool feature
Creates stacked bar charts for Income analysis (Original vs Corrected)
"""
import plotly.graph_objects as go
import pandas as pd

from shared.formatters import format_number, format_hover_value


def create_tool_income_chart(sample_data, tool_sample, division_filter, item_filter, function_filter, year_range):
    """
    Create stacked bar chart showing Original Income vs Correction.

    Args:
        sample_data: DataFrame with main dataset (Income_total column)
        tool_sample: DataFrame with correction dataset (Income_corr column)
        division_filter: str - Selected division or "none"
        item_filter: str - Selected item or "none"
        function_filter: str - Selected function or "none"
        year_range: list - [min_year, max_year]

    Returns:
        plotly.graph_objects.Figure - Stacked bar chart
    """
    # Filter sample_data
    df_main = sample_data.copy()
    df_main = df_main[(df_main['date'].dt.year >= year_range[0]) & (df_main['date'].dt.year <= year_range[1])]
    if division_filter != "none":
        df_main = df_main[df_main['Division'] == division_filter]
    if item_filter != "none":
        df_main = df_main[df_main['Item'] == item_filter]
    if function_filter != "none":
        df_main = df_main[df_main['Function'] == function_filter]

    # Filter tool_sample
    df_corr = tool_sample.copy()
    df_corr = df_corr[(df_corr['date'].dt.year >= year_range[0]) & (df_corr['date'].dt.year <= year_range[1])]
    if division_filter != "none":
        df_corr = df_corr[df_corr['Division'] == division_filter]
    if item_filter != "none":
        df_corr = df_corr[df_corr['Item'] == item_filter]
    if function_filter != "none":
        df_corr = df_corr[df_corr['Function'] == function_filter]

    # Aggregate by date
    main_agg = df_main.groupby('date')['Income_total'].sum().reset_index()
    main_agg['month'] = main_agg['date'].dt.to_period('M').astype(str)

    corr_agg = df_corr.groupby('date')['Income_corr'].sum().reset_index()
    corr_agg['month'] = corr_agg['date'].dt.to_period('M').astype(str)

    # Merge the two datasets
    merged = pd.merge(main_agg[['month', 'Income_total']], corr_agg[['month', 'Income_corr']],
                     on='month', how='outer').fillna(0)
    merged = merged.sort_values('month')

    # Create stacked bar chart
    fig = go.Figure()

    # Format dates for hover
    hover_dates = [pd.to_datetime(str(m)).strftime('%b-%Y') for m in merged['month']]

    fig.add_trace(go.Bar(
        x=merged['month'],
        y=merged['Income_total'],
        name='Income Total (Original)',
        marker_color='#718096',  # Gray medium for baseline
        text=[format_number(v) for v in merged['Income_total']],
        textposition='inside',
        customdata=list(zip(hover_dates, [format_hover_value(v) for v in merged['Income_total']])),
        hovertemplate='<b>%{customdata[0]}</b><br>Income Total (Original)<br>Value: %{customdata[1]}<extra></extra>'
    ))

    fig.add_trace(go.Bar(
        x=merged['month'],
        y=merged['Income_corr'],
        name='Income Correction',
        marker_color='#E53E3E',  # Red for emphasis
        text=[format_number(v) for v in merged['Income_corr']],
        textposition='inside',
        customdata=list(zip(hover_dates, [format_hover_value(v) for v in merged['Income_corr']])),
        hovertemplate='<b>%{customdata[0]}</b><br>Income Correction<br>Value: %{customdata[1]}<extra></extra>'
    ))

    # Format y-axis
    all_values = list(merged['Income_total']) + list(merged['Income_corr'])
    max_val = max(all_values) if all_values else 0

    if max_val >= 1e9:
        fig.update_yaxes(tickformat=".2s", title_text="Income (Billions)")
    elif max_val >= 1e6:
        fig.update_yaxes(tickformat=".2s", title_text="Income (Millions)")
    elif max_val >= 1e3:
        fig.update_yaxes(tickformat=".2s", title_text="Income (Thousands)")
    else:
        fig.update_yaxes(title_text="Income")

    fig.update_layout(
        title="Income Analysis: Original vs Corrected",
        xaxis_title="Month",
        barmode='stack',
        template="plotly_white",
        height=500,
        showlegend=True,
        margin=dict(l=50, r=50, t=60, b=50)
    )
    fig.update_xaxes(tickangle=45)

    return fig
