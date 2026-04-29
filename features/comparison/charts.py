"""
Comparison Feature - Chart Creation
Handles all chart generation for the comparison tab
"""

import plotly.graph_objects as go
import pandas as pd
import numpy as np
from config import get_color_sequence
from shared.formatters import format_number, format_hover_value, format_period
from features.comparison.logic import prepare_type_breakdown_data


def create_comparison_heatmap(df1, df2, variable, date1, date2, group_var, selected_type, var_label):
    """
    Create a heatmap showing values across two dates for many grouped items

    Args:
        df1: DataFrame for first date
        df2: DataFrame for second date
        variable: Column name to display
        date1: First date (datetime)
        date2: Second date (datetime)
        group_var: Variable to group by ('Division', 'Type', 'Item', 'Function')
        selected_type: Type of data (Total, Best, Type1, Type2, Type3)
        var_label: Label for the variable (e.g., "Amount", "Income")

    Returns:
        plotly.graph_objects.Figure: Heatmap chart
    """
    if group_var == "none":
        group_var = "Function"

    if group_var not in ['Division', 'Type', 'Item', 'Function']:
        fig = go.Figure()
        fig.add_annotation(text="Invalid grouping variable", xref="paper", yref="paper", x=0.5, y=0.5,
            xanchor='center', yanchor='middle', showarrow=False, font=dict(size=14, color="gray"))
        fig.update_layout(title=f"{var_label} Heatmap - {selected_type}", template="plotly_white", height=350)
        return fig

    # Aggregate data by group
    if not df1.empty:
        group1_data = df1.groupby(group_var)[variable].sum()
    else:
        group1_data = pd.Series(dtype=float)

    if not df2.empty:
        group2_data = df2.groupby(group_var)[variable].sum()
    else:
        group2_data = pd.Series(dtype=float)

    all_groups = set()
    if not group1_data.empty: all_groups.update(group1_data.index)
    if not group2_data.empty: all_groups.update(group2_data.index)

    if not all_groups:
        fig = go.Figure()
        fig.add_annotation(text="No data available", xref="paper", yref="paper", x=0.5, y=0.5,
            xanchor='center', yanchor='middle', showarrow=False, font=dict(size=14, color="gray"))
        fig.update_layout(title=f"{var_label} Heatmap by {group_var} - {selected_type}", template="plotly_white", height=350)
        return fig

    sorted_groups = sorted(all_groups)
    dates = [date1.strftime('%b-%Y'), date2.strftime('%b-%Y')]

    # Create matrix for heatmap
    z_matrix = []
    text_matrix = []
    for group in sorted_groups:
        val1 = group1_data.get(group, 0)
        val2 = group2_data.get(group, 0)
        z_matrix.append([val1, val2])
        text_matrix.append([format_number(val1), format_number(val2)])

    fig = go.Figure(data=go.Heatmap(
        z=z_matrix,
        x=dates,
        y=sorted_groups,
        text=text_matrix,
        texttemplate="%{text}",
        textfont={"size": 10},
        colorscale='Blues',
        hovertemplate='<b>%{y}</b><br>Date: %{x}<br>Value: %{text}<extra></extra>'
    ))

    fig.update_layout(
        title=f"{var_label} Heatmap by {group_var} - {selected_type}",
        xaxis_title="Date",
        yaxis_title=group_var,
        template="plotly_white",
        height=max(350, len(sorted_groups) * 25),
        margin=dict(l=120, r=50, t=80, b=50),
        xaxis=dict(type='category')
    )
    return fig


def create_dumbbell_chart_updated(df1, df2, variable, date1, date2, group_var, selected_type, var_label):
    """
    Create a dumbbell chart showing proportion changes between two dates

    Args:
        df1: DataFrame for first date
        df2: DataFrame for second date
        variable: Column name to display
        date1: First date (datetime)
        date2: Second date (datetime)
        group_var: Variable to group by ('Division', 'Type', 'Item', 'Function')
        selected_type: Type of data (Total, Best, Type1, Type2, Type3)
        var_label: Label for the variable (e.g., "Amount", "Income")

    Returns:
        plotly.graph_objects.Figure: Dumbbell chart
    """
    if group_var == "none":
        group_var = "Function"

    if group_var not in ['Division', 'Type', 'Item', 'Function']:
        fig = go.Figure()
        fig.add_annotation(text="Invalid grouping variable", xref="paper", yref="paper", x=0.5, y=0.5,
            xanchor='center', yanchor='middle', showarrow=False, font=dict(size=14, color="gray"))
        fig.update_layout(title=f"{var_label} Proportions - {selected_type}", template="plotly_white", height=350)
        return fig

    if not df1.empty:
        group1_data = df1.groupby(group_var)[variable].sum()
        total1 = df1[variable].sum()
        proportions1 = (group1_data / total1 * 100) if total1 > 0 else pd.Series(dtype=float)
    else:
        proportions1 = pd.Series(dtype=float)
        group1_data = pd.Series(dtype=float)

    if not df2.empty:
        group2_data = df2.groupby(group_var)[variable].sum()
        total2 = df2[variable].sum()
        proportions2 = (group2_data / total2 * 100) if total2 > 0 else pd.Series(dtype=float)
    else:
        proportions2 = pd.Series(dtype=float)
        group2_data = pd.Series(dtype=float)

    all_groups = set()
    if not proportions1.empty: all_groups.update(proportions1.index)
    if not proportions2.empty: all_groups.update(proportions2.index)

    if not all_groups:
        fig = go.Figure()
        fig.add_annotation(text="No data available", xref="paper", yref="paper", x=0.5, y=0.5,
            xanchor='center', yanchor='middle', showarrow=False, font=dict(size=14, color="gray"))
        fig.update_layout(title=f"{var_label} Share by {group_var} - {selected_type}", template="plotly_white", height=350)
        return fig

    fig = go.Figure()
    for i, group in enumerate(sorted(all_groups)):
        prop1, prop2 = proportions1.get(group, 0), proportions2.get(group, 0)
        val1, val2 = group1_data.get(group, 0), group2_data.get(group, 0)
        max_val = max(val1, val2) if max(val1, val2) > 0 else 1
        size1 = max(10, min(30, (val1 / max_val) * 25 + 5))
        size2 = max(10, min(30, (val2 / max_val) * 25 + 5))

        fig.add_trace(go.Scatter(x=[prop1, prop2], y=[i, i], mode='lines', line=dict(color='gray', width=2),
            showlegend=False, hoverinfo='skip'))
        fig.add_trace(go.Scatter(x=[prop1], y=[i], mode='markers',
            marker=dict(size=size1, color='lightgray', line=dict(width=2, color='gray')),
            name=f"{date1.strftime('%b-%Y')}", legendgroup="date1", showlegend=(i == 0),
            hovertemplate=f"<b>{group}</b><br>Month: {date1.strftime('%b-%Y')}<br>Proportion: {prop1:.1f}%<br>Amount: {format_number(val1)}<extra></extra>"))
        fig.add_trace(go.Scatter(x=[prop2], y=[i], mode='markers',
            marker=dict(size=size2, color='lightcoral', line=dict(width=2, color='red')),
            name=f"{date2.strftime('%b-%Y')}", legendgroup="date2", showlegend=(i == 0),
            hovertemplate=f"<b>{group}</b><br>Month: {date2.strftime('%b-%Y')}<br>Proportion: {prop2:.1f}%<br>Amount: {format_number(val2)}<extra></extra>"))

    fig.update_layout(title=f"{var_label} Share by {group_var} - {selected_type}", xaxis_title="Proportion (%)",
        yaxis=dict(tickmode='array', tickvals=list(range(len(all_groups))), ticktext=list(sorted(all_groups)), title=group_var, autorange='reversed'),
        template="plotly_white", height=350, showlegend=True, margin=dict(l=100, r=50, t=80, b=50))
    return fig


def create_division_stacked_chart(df1, df2, variable, var_label, date1, date2, selected_type, division_filter, entity_filter, filter_var, filter_values, df, group_var="none"):
    """
    Create a stacked bar chart showing division percentage contribution.
    When group_var is active, the x-axis shows one pair of date bars per group value,
    each bar still stacked by Division.

    Args:
        df1: DataFrame for first date (filtered)
        df2: DataFrame for second date (filtered)
        variable: Column name to display
        var_label: Label for the variable (e.g., "Amount", "Income")
        date1: First date (datetime)
        date2: Second date (datetime)
        selected_type: Type of data (Total, Best, Type1, Type2, Type3)
        division_filter: Division filter value ("All" or specific division)
        entity_filter: Entity filter value
        filter_var: Additional filter variable
        filter_values: Additional filter values
        df: Full DataFrame with all data
        group_var: Variable to group x-axis by (default "none")

    Returns:
        plotly.graph_objects.Figure: Stacked bar chart
    """
    # If division filter is set to "All", use dataset filtered to exclude "All" divisions
    if division_filter == "All":
        df_temp1 = df[(df['date'].dt.to_period('M') == date1.to_period('M'))]
        df_temp2 = df[(df['date'].dt.to_period('M') == date2.to_period('M'))]

        if entity_filter != "All":
            df_temp1 = df_temp1[df_temp1['Entity'] == entity_filter]
            df_temp2 = df_temp2[df_temp2['Entity'] == entity_filter]

        df_temp1 = df_temp1[df_temp1['Division'] != "All"]
        df_temp2 = df_temp2[df_temp2['Division'] != "All"]

        if filter_var != "none" and filter_var in df.columns and filter_values:
            df_temp1 = df_temp1[df_temp1[filter_var].isin(filter_values)]
            df_temp2 = df_temp2[df_temp2[filter_var].isin(filter_values)]

        df1, df2 = df_temp1, df_temp2

    if 'Division' not in df1.columns or 'Division' not in df2.columns:
        fig = go.Figure()
        fig.add_annotation(text="Division data not available", xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle', showarrow=False)
        fig.update_layout(title=f"{var_label} by Division", template="plotly_white", height=350)
        return fig

    d1_label = date1.strftime('%b-%Y')
    d2_label = date2.strftime('%b-%Y')

    # Build (x_label, df_subset) pairs — one per date, or one per group+date
    if group_var != "none" and group_var in df1.columns and group_var in df2.columns:
        all_groups = sorted(set(df1[group_var].unique()) | set(df2[group_var].unique()))
        x_pairs = []
        for grp in all_groups:
            x_pairs.append((f"{grp} | {d1_label}", df1[df1[group_var] == grp]))
            x_pairs.append((f"{grp} | {d2_label}", df2[df2[group_var] == grp]))
        xaxis_title = f"{group_var} / Month"
        chart_height = max(350, len(all_groups) * 60)
    else:
        x_pairs = [(d1_label, df1), (d2_label, df2)]
        xaxis_title = "Month"
        chart_height = 350

    # Collect all divisions across all subsets
    all_divisions = set()
    for _, subset in x_pairs:
        all_divisions.update(subset['Division'].unique())
    sorted_divisions = sorted(all_divisions)
    colors = get_color_sequence('stacked', len(sorted_divisions))

    fig = go.Figure()
    x_labels = [label for label, _ in x_pairs]

    for i, division in enumerate(sorted_divisions):
        y_vals = []
        text_vals = []
        for _, subset in x_pairs:
            div_sum = subset[subset['Division'] == division][variable].sum() if not subset.empty else 0
            total = subset[variable].sum() if not subset.empty else 0
            pct = (div_sum / total * 100) if total > 0 else 0
            y_vals.append(pct)
            text_vals.append(f"{pct:.1f}%")

        fig.add_trace(go.Bar(
            x=x_labels, y=y_vals, name=division,
            marker_color=colors[i],
            text=text_vals, textposition='inside',
            hovertemplate='<b>%{x}</b><br>' + f'{division}<br>' + 'Percentage: %{y:.1f}%<extra></extra>'
        ))

    fig.update_layout(
        title=f"{var_label} Percentage Contribution by Division - {selected_type}",
        xaxis_title=xaxis_title, yaxis_title="Percentage (%)", barmode='stack',
        template="plotly_white", height=chart_height, showlegend=True,
        yaxis=dict(range=[0, 100]), xaxis=dict(type='category')
    )
    return fig


def create_type2_breakdown_charts(date1, date2, filter_var, filter_values, group_var, selected_type):
    """
    Create Type2 breakdown charts showing WW, DP, PP proportions

    Args:
        date1: First date (datetime)
        date2: Second date (datetime)
        filter_var: Variable to filter by
        filter_values: List of filter values
        group_var: Variable to group by
        selected_type: Type of data (Total, Best, Type1, Type2, Type3)

    Returns:
        tuple: (fig_amount, fig_income) - Two plotly figures for amount and income breakdowns
    """
    type_df1, type_df2, type_group_cols = prepare_type_breakdown_data(date1, date2, filter_var, filter_values, group_var)

    date_labels = [date1.strftime('%b-%Y'), date2.strftime('%b-%Y')]

    if type_df1 is None or type_df2 is None:
        # Return empty figures if data not available
        empty_fig = go.Figure()
        empty_fig.add_annotation(text="Type breakdown data not available", xref="paper", yref="paper",
            x=0.5, y=0.5, xanchor='center', yanchor='middle', showarrow=False)
        empty_fig.update_layout(template="plotly_white", height=350)
        return empty_fig, empty_fig

    # Amount breakdown chart
    fig_amount = go.Figure()

    if type_group_cols:
        # Grouped by category - show side-by-side grouped bars
        categories = sorted(set(list(type_df1[group_var]) + list(type_df2[group_var])))
        components = ['WW_Amount', 'DP_Amount', 'PP_Amount']
        colors_comp = ['#718096', '#E53E3E', '#48BB78']  # Gray, Red, Green

        for comp_idx, component in enumerate(components):
            vals_date1 = []
            vals_date2 = []
            for cat in categories:
                row1 = type_df1[type_df1[group_var] == cat]
                row2 = type_df2[type_df2[group_var] == cat]

                total1 = row1[['WW_Amount', 'DP_Amount', 'PP_Amount']].sum().sum() if not row1.empty else 1
                total2 = row2[['WW_Amount', 'DP_Amount', 'PP_Amount']].sum().sum() if not row2.empty else 1

                val1 = (row1[component].iloc[0] / total1 * 100) if not row1.empty else 0
                val2 = (row2[component].iloc[0] / total2 * 100) if not row2.empty else 0

                vals_date1.append(val1)
                vals_date2.append(val2)

            # Add traces for each date
            fig_amount.add_trace(go.Bar(
                x=[f"{cat} - {date_labels[0]}" for cat in categories],
                y=vals_date1,
                name=component.replace('_Amount', ''),
                marker_color=colors_comp[comp_idx],
                text=[f"{v:.1f}%" for v in vals_date1],
                textposition='inside',
                legendgroup=component,
                showlegend=True
            ))
            fig_amount.add_trace(go.Bar(
                x=[f"{cat} - {date_labels[1]}" for cat in categories],
                y=vals_date2,
                name=component.replace('_Amount', ''),
                marker_color=colors_comp[comp_idx],
                text=[f"{v:.1f}%" for v in vals_date2],
                textposition='inside',
                legendgroup=component,
                showlegend=False
            ))

        fig_amount.update_layout(barmode='stack')
    else:
        # Total view - simple stacked bars
        row1, row2 = type_df1.iloc[0], type_df2.iloc[0]
        components = ['WW_Amount', 'DP_Amount', 'PP_Amount']
        colors_comp = ['#718096', '#E53E3E', '#48BB78']

        for comp_idx, component in enumerate(components):
            total1 = row1['WW_Amount'] + row1['DP_Amount'] + row1['PP_Amount']
            total2 = row2['WW_Amount'] + row2['DP_Amount'] + row2['PP_Amount']

            pct1 = (row1[component] / total1 * 100) if total1 > 0 else 0
            pct2 = (row2[component] / total2 * 100) if total2 > 0 else 0

            fig_amount.add_trace(go.Bar(
                x=date_labels,
                y=[pct1, pct2],
                name=component.replace('_Amount', ''),
                marker_color=colors_comp[comp_idx],
                text=[f"{pct1:.1f}%", f"{pct2:.1f}%"],
                textposition='inside',
                hovertemplate='<b>%{x}</b><br>' + component.replace('_Amount', '') + '<br>Percentage: %{y:.1f}%<extra></extra>'
            ))

        fig_amount.update_layout(barmode='stack')

    fig_amount.update_layout(
        title=f"Amount Breakdown (WW / DP / PP) - {selected_type}",
        xaxis_title="Period" if not type_group_cols else group_var,
        yaxis_title="Percentage (%)",
        template="plotly_white",
        height=350,
        showlegend=True,
        yaxis=dict(range=[0, 100], ticksuffix="%"),
        xaxis=dict(type='category')
    )

    # Income breakdown chart (same logic as amount)
    fig_income = go.Figure()

    if type_group_cols:
        categories = sorted(set(list(type_df1[group_var]) + list(type_df2[group_var])))
        components = ['WW_Income', 'DP_Income', 'PP_Income']
        colors_comp = ['#718096', '#E53E3E', '#48BB78']

        for comp_idx, component in enumerate(components):
            vals_date1 = []
            vals_date2 = []
            for cat in categories:
                row1 = type_df1[type_df1[group_var] == cat]
                row2 = type_df2[type_df2[group_var] == cat]

                total1 = row1[['WW_Income', 'DP_Income', 'PP_Income']].sum().sum() if not row1.empty else 1
                total2 = row2[['WW_Income', 'DP_Income', 'PP_Income']].sum().sum() if not row2.empty else 1

                val1 = (row1[component].iloc[0] / total1 * 100) if not row1.empty else 0
                val2 = (row2[component].iloc[0] / total2 * 100) if not row2.empty else 0

                vals_date1.append(val1)
                vals_date2.append(val2)

            fig_income.add_trace(go.Bar(
                x=[f"{cat} - {date_labels[0]}" for cat in categories],
                y=vals_date1,
                name=component.replace('_Income', ''),
                marker_color=colors_comp[comp_idx],
                text=[f"{v:.1f}%" for v in vals_date1],
                textposition='inside',
                legendgroup=component,
                showlegend=True
            ))
            fig_income.add_trace(go.Bar(
                x=[f"{cat} - {date_labels[1]}" for cat in categories],
                y=vals_date2,
                name=component.replace('_Income', ''),
                marker_color=colors_comp[comp_idx],
                text=[f"{v:.1f}%" for v in vals_date2],
                textposition='inside',
                legendgroup=component,
                showlegend=False
            ))

        fig_income.update_layout(barmode='stack')
    else:
        row1, row2 = type_df1.iloc[0], type_df2.iloc[0]
        components = ['WW_Income', 'DP_Income', 'PP_Income']
        colors_comp = ['#718096', '#E53E3E', '#48BB78']

        for comp_idx, component in enumerate(components):
            total1 = row1['WW_Income'] + row1['DP_Income'] + row1['PP_Income']
            total2 = row2['WW_Income'] + row2['DP_Income'] + row2['PP_Income']

            pct1 = (row1[component] / total1 * 100) if total1 > 0 else 0
            pct2 = (row2[component] / total2 * 100) if total2 > 0 else 0

            fig_income.add_trace(go.Bar(
                x=date_labels,
                y=[pct1, pct2],
                name=component.replace('_Income', ''),
                marker_color=colors_comp[comp_idx],
                text=[f"{pct1:.1f}%", f"{pct2:.1f}%"],
                textposition='inside',
                hovertemplate='<b>%{x}</b><br>' + component.replace('_Income', '') + '<br>Percentage: %{y:.1f}%<extra></extra>'
            ))

        fig_income.update_layout(barmode='stack')

    fig_income.update_layout(
        title=f"Income Breakdown (WW / DP / PP) - {selected_type}",
        xaxis_title="Period" if not type_group_cols else group_var,
        yaxis_title="Percentage (%)",
        template="plotly_white",
        height=350,
        showlegend=True,
        yaxis=dict(range=[0, 100], ticksuffix="%"),
        xaxis=dict(type='category')
    )

    return fig_amount, fig_income


def create_comparison_chart(df1, df2, variable, var_label, date1, date2, selected_type, group_var, stack_var, df):
    """
    Create a comparison bar chart for amount or income

    Args:
        df1: DataFrame for first date
        df2: DataFrame for second date
        variable: Column name to display
        var_label: Label for the variable (e.g., "Amount", "Income")
        date1: First date (datetime)
        date2: Second date (datetime)
        selected_type: Type of data (Total, Best, Type1, Type2, Type3)
        group_var: Variable to group by
        stack_var: Variable to stack by
        df: Full DataFrame reference (for column check)

    Returns:
        plotly.graph_objects.Figure: Comparison bar chart
    """
    fig, date_labels = go.Figure(), [date1.strftime('%b-%Y'), date2.strftime('%b-%Y')]
    if group_var != "none" and group_var in df.columns and group_var in ['Division', 'Type', 'Item', 'Function']:
        all_categories = set()
        if not df1.empty: all_categories.update(df1[group_var].unique())
        if not df2.empty: all_categories.update(df2[group_var].unique())
        sorted_categories = sorted(all_categories)
        colors = get_color_sequence('grouped', len(sorted_categories))
        for i, category in enumerate(sorted_categories):
            val1 = df1[df1[group_var] == category][variable].sum() if not df1.empty and category in df1[group_var].values else 0
            val2 = df2[df2[group_var] == category][variable].sum() if not df2.empty and category in df2[group_var].values else 0
            hover_text = [format_hover_value(val1), format_hover_value(val2)]
            fig.add_trace(go.Bar(x=date_labels, y=[val1, val2], name=f"{category}",
                marker_color=colors[i],
                text=[format_number(val1), format_number(val2)], textposition='auto',
                customdata=hover_text,
                hovertemplate='<b>%{x}</b><br>' + f'{category}<br>' + 'Value: %{customdata}<extra></extra>'))
        fig.update_layout(barmode='group')
    elif stack_var != "none" and stack_var in df.columns and stack_var in ['Division', 'Type', 'Item', 'Function']:
        all_categories = set()
        if not df1.empty: all_categories.update(df1[stack_var].unique())
        if not df2.empty: all_categories.update(df2[stack_var].unique())
        sorted_categories = sorted(all_categories)
        colors = get_color_sequence('stacked', len(sorted_categories))
        for i, category in enumerate(sorted_categories):
            val1 = df1[df1[stack_var] == category][variable].sum() if not df1.empty and category in df1[stack_var].values else 0
            val2 = df2[df2[stack_var] == category][variable].sum() if not df2.empty and category in df2[stack_var].values else 0
            hover_text = [format_hover_value(val1), format_hover_value(val2)]
            fig.add_trace(go.Bar(x=date_labels, y=[val1, val2], name=f"{category}",
                marker_color=colors[i],
                text=[format_number(val1), format_number(val2)], textposition='auto',
                customdata=hover_text,
                hovertemplate='<b>%{x}</b><br>' + f'{category}<br>' + 'Value: %{customdata}<extra></extra>'))
        fig.update_layout(barmode='stack')
    else:
        val1 = df1[variable].sum() if not df1.empty else 0
        val2 = df2[variable].sum() if not df2.empty else 0
        comparison_colors = get_color_sequence('bar', 2, is_comparison=True)
        hover_text = [format_hover_value(val1), format_hover_value(val2)]
        fig.add_trace(go.Bar(x=date_labels, y=[val1, val2], name=var_label,
            marker_color=comparison_colors, text=[format_number(val1), format_number(val2)], textposition='auto',
            customdata=hover_text,
            hovertemplate='<b>%{x}</b><br>Value: %{customdata}<extra></extra>'))

    all_values = [v for trace in fig.data for v in trace.y if v is not None]
    max_val = max(all_values) if all_values else 0
    if max_val >= 1e9:
        fig.update_yaxes(tickformat=".2s", title_text="Value (Billions)")
    elif max_val >= 1e6:
        fig.update_yaxes(tickformat=".2s", title_text="Value (Millions)")
    elif max_val >= 1e3:
        fig.update_yaxes(tickformat=".2s", title_text="Value (Thousands)")
    else:
        fig.update_yaxes(title_text="Value")

    fig.update_layout(title=f"{var_label} Comparison - {selected_type}", xaxis_title="Month",
        template="plotly_white", height=300, showlegend=True, xaxis=dict(type='category'))
    return fig


def create_ratio_comparison_chart(df1, df2, amount_col, income_col, date1, date2, selected_type, group_var, amount_old, amount_new, income_old, income_new):
    """
    Create a return ratio comparison chart

    Args:
        df1: DataFrame for first date
        df2: DataFrame for second date
        amount_col: Column name for amount data
        income_col: Column name for income data
        date1: First date (datetime)
        date2: Second date (datetime)
        selected_type: Type of data (Total, Best, Type1, Type2, Type3)
        group_var: Variable to group by
        amount_old: Total amount for first date (for simple comparison)
        amount_new: Total amount for second date (for simple comparison)
        income_old: Total income for first date (for simple comparison)
        income_new: Total income for second date (for simple comparison)

    Returns:
        plotly.graph_objects.Figure: Ratio comparison chart
    """
    ratio_comparison_fig = go.Figure()
    if group_var != "none" and group_var in ['Type', 'Item', 'Function']:
        # Grouped ratio comparison (horizontal bars)
        groups_date1 = df1.groupby(group_var).agg({amount_col: 'sum', income_col: 'sum'}).reset_index()
        groups_date2 = df2.groupby(group_var).agg({amount_col: 'sum', income_col: 'sum'}).reset_index()

        groups_date1['ratio'] = (groups_date1[income_col] / groups_date1[amount_col].replace(0, np.nan)) * 100
        groups_date2['ratio'] = (groups_date2[income_col] / groups_date2[amount_col].replace(0, np.nan)) * 100

        all_groups = sorted(set(groups_date1[group_var].tolist() + groups_date2[group_var].tolist()))

        ratio_data_date1 = groups_date1.set_index(group_var)['ratio'].reindex(all_groups, fill_value=0)
        ratio_data_date2 = groups_date2.set_index(group_var)['ratio'].reindex(all_groups, fill_value=0)

        ratio_comparison_fig.add_trace(go.Bar(
            y=all_groups, x=ratio_data_date1, name=date1.strftime('%b-%Y'),
            orientation='h', marker_color='lightgray',
            text=[f"{v:.1f}%" for v in ratio_data_date1],
            textposition='auto',
            hovertemplate='<b>%{y}</b><br>Ratio: %{x:.2f}%<extra></extra>'
        ))
        ratio_comparison_fig.add_trace(go.Bar(
            y=all_groups, x=ratio_data_date2, name=date2.strftime('%b-%Y'),
            orientation='h', marker_color='lightcoral',
            text=[f"{v:.1f}%" for v in ratio_data_date2],
            textposition='auto',
            hovertemplate='<b>%{y}</b><br>Ratio: %{x:.2f}%<extra></extra>'
        ))

        ratio_comparison_fig.update_layout(
            title=f"Return Ratio by {group_var} - {selected_type}",
            xaxis_title="Ratio (%)",
            yaxis_title=group_var,
            template="plotly_white",
            height=max(400, len(all_groups) * 40),
            barmode='group',
            showlegend=True,
            yaxis=dict(type='category')
        )
    else:
        # Simple ratio comparison (no grouping) — horizontal bar, consistent with grouped view
        ratio_old = (income_old / amount_old * 100) if amount_old != 0 else 0
        ratio_new = (income_new / amount_new * 100) if amount_new != 0 else 0

        ratio_comparison_fig.add_trace(go.Bar(
            y=[date1.strftime('%b-%Y'), date2.strftime('%b-%Y')],
            x=[ratio_old, ratio_new],
            orientation='h',
            marker_color=['lightgray', 'lightcoral'],
            text=[f"{ratio_old:.2f}%", f"{ratio_new:.2f}%"],
            textposition='auto',
            hovertemplate='<b>%{y}</b><br>Ratio: %{x:.2f}%<extra></extra>'
        ))

        ratio_comparison_fig.update_layout(
            title=f"Return Ratio Comparison - {selected_type}",
            xaxis_title="Ratio (%)",
            yaxis_title="Date",
            template="plotly_white",
            height=400,
            showlegend=False,
            yaxis=dict(type='category')
        )

    return ratio_comparison_fig
