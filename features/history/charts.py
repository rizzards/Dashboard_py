"""
Chart creation functions for the History feature
Handles all visualization generation for the history tab
"""
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from config import get_color_sequence
from shared.formatters import format_number, format_hover_value, format_period


def create_bar_chart(df, variable_col, title, stack_var, group_var):
    """
    Create a bar chart with optional stacking or grouping.

    Args:
        df: DataFrame with 'month' column and variable_col
        variable_col: Column name to visualize
        title: Chart title
        stack_var: Variable to stack by (or 'none')
        group_var: Variable to group by (or 'none')

    Returns:
        Plotly Figure object
    """
    fig = go.Figure()

    if stack_var != "none" and stack_var in df.columns and stack_var in ['Division', 'Type', 'Item', 'Function']:
        # Stacked bar chart
        stacked_data = df.groupby(['month', stack_var])[variable_col].sum().unstack(fill_value=0)
        colors = get_color_sequence('stacked', len(stacked_data.columns))
        formatted_dates = [format_period(m) for m in stacked_data.index]

        for i, category in enumerate(stacked_data.columns):
            hover_text = [format_hover_value(v) for v in stacked_data[category]]

            fig.add_trace(go.Bar(
                x=formatted_dates,
                y=stacked_data[category],
                name=f"{category}",
                marker_color=colors[i],
                text=[format_number(v) for v in stacked_data[category]],
                textposition='auto',
                customdata=hover_text,
                hovertemplate='<b>%{x}</b><br>' + f'{category}<br>' + 'Value: %{customdata}<extra></extra>'
            ))
        fig.update_layout(barmode='stack')

    elif group_var != "none" and group_var in df.columns and group_var in ['Division', 'Type', 'Item', 'Function']:
        # Grouped bar chart
        categories = sorted(df[group_var].unique())
        colors = get_color_sequence('grouped', len(categories))

        for i, category in enumerate(categories):
            category_data = df[df[group_var] == category]
            monthly_data = category_data.groupby('month')[variable_col].sum().reset_index()
            hover_text = [format_hover_value(v) for v in monthly_data[variable_col]]
            formatted_dates = [format_period(m) for m in monthly_data['month']]

            fig.add_trace(go.Bar(
                x=formatted_dates,
                y=monthly_data[variable_col],
                name=f"{category}",
                marker_color=colors[i],
                text=[format_number(v) for v in monthly_data[variable_col]],
                textposition='auto',
                customdata=hover_text,
                hovertemplate='<b>%{x}</b><br>' + f'{category}<br>' + 'Value: %{customdata}<extra></extra>'
            ))
        fig.update_layout(barmode='group')

    else:
        # Simple bar chart
        monthly_data = df.groupby('month')[variable_col].sum().reset_index()
        hover_text = [format_hover_value(v) for v in monthly_data[variable_col]]
        formatted_dates = [format_period(m) for m in monthly_data['month']]

        fig.add_trace(go.Bar(
            x=formatted_dates,
            y=monthly_data[variable_col],
            name=title,
            marker_color=get_color_sequence('bar', 1)[0],
            text=[format_number(v) for v in monthly_data[variable_col]],
            textposition='auto',
            customdata=hover_text,
            hovertemplate='<b>%{x}</b><br>Value: %{customdata}<extra></extra>'
        ))

    # Determine appropriate y-axis format
    all_values = []
    for trace in fig.data:
        all_values.extend([v for v in trace.y if v is not None])
    max_val = max(all_values) if all_values else 0

    if max_val >= 1e9:
        fig.update_yaxes(tickformat=".2s", title_text="Value (Billions)")
    elif max_val >= 1e6:
        fig.update_yaxes(tickformat=".2s", title_text="Value (Millions)")
    elif max_val >= 1e3:
        fig.update_yaxes(tickformat=".2s", title_text="Value (Thousands)")
    else:
        fig.update_yaxes(title_text="Value")

    fig.update_layout(
        title=title,
        xaxis_title="Month",
        template="plotly_white",
        showlegend=True,
        height=350,
        margin=dict(l=50, r=50, t=60, b=50),
        xaxis=dict(type='category', tickangle=45)
    )

    return fig


def create_ratio_chart(df, amount_col, income_col, group_var, selected_type):
    """
    Create a line chart showing Income/Amount ratio over time.

    Args:
        df: DataFrame with month, amount, and income columns
        amount_col: Amount column name
        income_col: Income column name
        group_var: Variable to group by (or 'none')
        selected_type: Display type (Total, Best, Type1, etc.)

    Returns:
        Plotly Figure object
    """
    ratio_fig = go.Figure()

    if group_var != "none" and group_var in df.columns and group_var in ['Division', 'Type', 'Item', 'Function']:
        # Grouped ratio chart
        categories = sorted(df[group_var].unique())
        colors = get_color_sequence('line', len(categories))

        for i, category in enumerate(categories):
            category_data = df[df[group_var] == category]
            monthly_data = category_data.groupby('month').agg({
                amount_col: 'sum',
                income_col: 'sum'
            }).reset_index()
            monthly_data['ratio'] = (monthly_data[income_col] / monthly_data[amount_col].replace(0, np.nan)) * 100
            formatted_dates = [format_period(m) for m in monthly_data['month']]

            ratio_fig.add_trace(go.Scatter(
                x=formatted_dates,
                y=monthly_data['ratio'],
                mode='lines+markers',
                name=f"{category}",
                line=dict(color=colors[i], width=2),
                marker=dict(size=6),
                hovertemplate='<b>%{x}</b><br>' + f'{category}<br>' + 'Ratio: %{y:.2f}%<extra></extra>'
            ))
    else:
        # Simple ratio chart
        monthly_data = df.groupby('month').agg({
            amount_col: 'sum',
            income_col: 'sum'
        }).reset_index()
        monthly_data['ratio'] = (monthly_data[income_col] / monthly_data[amount_col].replace(0, np.nan)) * 100
        formatted_dates = [format_period(m) for m in monthly_data['month']]

        ratio_fig.add_trace(go.Scatter(
            x=formatted_dates,
            y=monthly_data['ratio'],
            mode='lines+markers',
            name='Return Ratio',
            line=dict(color=get_color_sequence('line', 1)[0], width=3),
            marker=dict(size=8),
            hovertemplate='<b>%{x}</b><br>Ratio: %{y:.2f}%<extra></extra>'
        ))

    ratio_fig.update_layout(
        title=f"Return Ratio (Income/Amount) - {selected_type}",
        xaxis_title="Month",
        yaxis_title="Ratio (%)",
        template="plotly_white",
        height=250,
        margin=dict(l=50, r=120, t=60, b=50),
        showlegend=True,
        legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02),
        xaxis=dict(type='category', tickangle=45)
    )
    ratio_fig.update_yaxes(ticksuffix="%")

    return ratio_fig


def create_income_diff_chart(df, income_col, selected_type, stack_var="none", group_var="none"):
    """
    Create a quarterly income difference (QoQ) chart.
    - No stack/group: single green/red bar per quarter transition
    - stack_var active: each bar is stacked by category contribution to the QoQ diff
    - group_var active: grouped bars per quarter transition, one bar per category

    Args:
        df: DataFrame with month and income columns
        income_col: Income column name
        selected_type: Display type (Total, Best, Type1, etc.)
        stack_var: Variable to stack by (or 'none')
        group_var: Variable to group by (or 'none')

    Returns:
        Plotly Figure object
    """
    income_diff_fig = go.Figure()

    if df.empty:
        income_diff_fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper", x=0.5, y=0.5,
            xanchor='center', yanchor='middle', showarrow=False,
            font=dict(size=14, color="gray")
        )
        income_diff_fig.update_layout(title=f"Quarterly Income Difference - {selected_type}",
            template="plotly_white", height=350)
        return income_diff_fig

    # Attach quarter label to every row
    df = df.copy()
    df['date_obj'] = pd.to_datetime(df['month'].astype(str))
    df['quarter'] = df['date_obj'].dt.to_period('Q').astype(str)

    use_stack = stack_var != "none" and stack_var in df.columns and stack_var in ['Division', 'Type', 'Item', 'Function']
    use_group = group_var != "none" and group_var in df.columns and group_var in ['Division', 'Type', 'Item', 'Function']

    if use_stack or use_group:
        dim = stack_var if use_stack else group_var

        # Quarterly totals per category
        quarterly_by_cat = (
            df.groupby(['quarter', dim])[income_col].sum()
            .unstack(fill_value=0)
            .sort_index()
        )

        # QoQ diff per category — drop first quarter (no prior period)
        diff_by_cat = quarterly_by_cat.diff().iloc[1:]

        if diff_by_cat.empty:
            income_diff_fig.add_annotation(
                text="Insufficient data for quarterly comparison",
                xref="paper", yref="paper", x=0.5, y=0.5,
                xanchor='center', yanchor='middle', showarrow=False,
                font=dict(size=14, color="gray")
            )
            income_diff_fig.update_layout(title=f"Quarterly Income Difference - {selected_type}",
                template="plotly_white", height=350)
            return income_diff_fig

        quarters = list(diff_by_cat.index)
        categories = list(diff_by_cat.columns)

        if use_stack:
            colors = get_color_sequence('stacked', len(categories))
            for i, cat in enumerate(categories):
                vals = diff_by_cat[cat].tolist()
                income_diff_fig.add_trace(go.Bar(
                    x=quarters, y=vals, name=str(cat),
                    marker_color=colors[i],
                    text=[format_number(v) for v in vals],
                    textposition='auto',
                    hovertemplate='<b>%{x}</b><br>' + f'{cat}<br>' + 'Diff: %{y:.2s}<extra></extra>'
                ))
            income_diff_fig.update_layout(barmode='relative')  # stacked allowing negative offsets
        else:
            colors = get_color_sequence('grouped', len(categories))
            for i, cat in enumerate(categories):
                vals = diff_by_cat[cat].tolist()
                income_diff_fig.add_trace(go.Bar(
                    x=quarters, y=vals, name=str(cat),
                    marker_color=colors[i],
                    text=[format_number(v) for v in vals],
                    textposition='auto',
                    hovertemplate='<b>%{x}</b><br>' + f'{cat}<br>' + 'Diff: %{y:.2s}<extra></extra>'
                ))
            income_diff_fig.update_layout(barmode='group')

        income_diff_fig.update_layout(
            title=f"Quarterly Income Difference by {dim} - {selected_type}",
            xaxis_title="Quarter", yaxis_title="Income Difference",
            template="plotly_white", height=350, showlegend=True,
            margin=dict(l=50, r=50, t=60, b=50),
            xaxis=dict(type='category', tickangle=45)
        )

    else:
        # Original total diff logic
        monthly_data = df.groupby('quarter')[income_col].sum().reset_index().sort_values('quarter')

        if len(monthly_data) > 1:
            monthly_data['income_diff'] = monthly_data[income_col].diff()
            monthly_data['pct_change'] = monthly_data[income_col].pct_change() * 100

            bar_colors = ['green' if v > 0 else 'red' if v < 0 else 'gray'
                         for v in monthly_data['income_diff'].fillna(0)]

            income_diff_fig.add_trace(go.Bar(
                x=monthly_data['quarter'],
                y=monthly_data['income_diff'].fillna(0),
                marker_color=bar_colors,
                text=[format_number(v) if pd.notna(v) else 'N/A' for v in monthly_data['income_diff']],
                textposition='auto',
                customdata=list(zip(
                    monthly_data['quarter'],
                    [format_number(v) if pd.notna(v) else 'N/A' for v in monthly_data['income_diff']],
                    [f"{v:.1f}%" if pd.notna(v) else 'N/A' for v in monthly_data['pct_change']]
                )),
                hovertemplate='<b>%{customdata[0]}</b><br>Difference: %{customdata[1]}<br>Change: %{customdata[2]}<extra></extra>'
            ))
            income_diff_fig.update_layout(
                title=f"Quarterly Income Difference - {selected_type}",
                xaxis_title="Quarter", yaxis_title="Income Difference",
                template="plotly_white", height=350, showlegend=False,
                margin=dict(l=50, r=50, t=60, b=50),
                xaxis=dict(type='category', tickangle=45)
            )
        else:
            income_diff_fig.add_annotation(
                text="Insufficient data for quarterly comparison",
                xref="paper", yref="paper", x=0.5, y=0.5,
                xanchor='center', yanchor='middle', showarrow=False,
                font=dict(size=14, color="gray")
            )
            income_diff_fig.update_layout(title=f"Quarterly Income Difference - {selected_type}",
                template="plotly_white", height=350)

    return income_diff_fig
