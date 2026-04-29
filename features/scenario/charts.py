"""
Chart generation functions for the Scenario feature
Creates stacked bar charts for scenario weight distribution analysis
and macroeconomic prediction charts
"""
import plotly.graph_objects as go
import pandas as pd

from config import get_color_sequence
from config_macro import PREDICTION_CHART_CONFIG
from shared.formatters import format_period


def create_scenario_weight_chart(scenw_sample, year_range):
    """
    Create stacked bar chart showing scenario weight percentages by date.

    Args:
        scenw_sample: DataFrame with scenario weight data (date, ScenName, Weight columns)
        year_range: list - [min_year, max_year] or None

    Returns:
        plotly.graph_objects.Figure - Stacked bar chart with scenario distribution
    """
    try:
        df = scenw_sample.copy()

        # Handle None year_range (initial load)
        if year_range is None:
            year_range = [df['date'].dt.year.min(), df['date'].dt.year.max()]

        # Filter by year range
        df = df[(df['date'].dt.year >= year_range[0]) & (df['date'].dt.year <= year_range[1])]

        # Prepare data
        df['month'] = df['date'].dt.to_period('M').astype(str)

        # Aggregate weights by month and scenario (in case of duplicates)
        df_agg = df.groupby(['month', 'ScenName'])['Weight'].sum().reset_index()

        # Pivot to get scenario weights by month
        pivot_df = df_agg.pivot(index='month', columns='ScenName', values='Weight').fillna(0)

        # Sort by month
        pivot_df = pivot_df.sort_index()

        # Get unique scenarios
        unique_scenarios = sorted(df['ScenName'].unique())

        # Create figure
        fig = go.Figure()

        # Get color sequence for scenarios
        colors = get_color_sequence('stacked', len(unique_scenarios))

        # Add traces for each scenario
        formatted_dates = [format_period(m) for m in pivot_df.index]

        for i, scenario in enumerate(unique_scenarios):
            if scenario in pivot_df.columns:
                weights = pivot_df[scenario]

                # Convert to percentage (multiply by 100)
                weight_pct = weights * 100

                fig.add_trace(go.Bar(
                    x=formatted_dates,
                    y=weight_pct,
                    name=scenario,
                    marker_color=colors[i],
                    text=[f"{w:.1f}%" if w > 2 else "" for w in weight_pct],
                    textposition='inside',
                    textfont=dict(color='white', size=10),
                    hovertemplate='<b>%{x}</b><br>' + f'{scenario}<br>' +
                                 'Weight: %{y:.2f}%<extra></extra>'
                ))

        fig.update_layout(
            title="Scenario Weight Distribution Over Time",
            xaxis_title="Month",
            yaxis_title="Weight (%)",
            barmode='stack',
            template="plotly_white",
            height=500,
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.02
            ),
            margin=dict(l=50, r=150, t=60, b=100),
            yaxis=dict(range=[0, 100], ticksuffix="%"),
            xaxis=dict(type='category', tickangle=45)
        )

        return fig

    except Exception as e:
        # Return error figure if anything goes wrong
        fig = go.Figure()
        fig.add_annotation(text=f"Error: {str(e)}",
                          xref="paper", yref="paper", x=0.5, y=0.5,
                          xanchor='center', yanchor='middle', showarrow=False,
                          font=dict(size=12, color="red"))
        fig.update_layout(title="Scenario Weight Distribution Over Time", template="plotly_white", height=500)
        return fig


def create_prediction_chart(country, indicator, include_historical):
    """
    Create macroeconomic prediction chart with optional historical time series.

    ⚠️ PLACEHOLDER FUNCTION ⚠️
    This is a placeholder for your custom prediction chart implementation.
    Replace this function with your prepared chart logic.

    Args:
        country: str - Selected country name
        indicator: str - Selected macroeconomic indicator
        include_historical: bool - Whether to include historical time series

    Returns:
        plotly.graph_objects.Figure - Prediction chart with optional historical data

    Usage:
        To integrate your custom chart:
        1. Replace the placeholder implementation below
        2. Load your prediction data (from file, API, or database)
        3. Create your chart using plotly.graph_objects
        4. Return the figure object

    Example structure:
        # Load your data
        prediction_data = load_prediction_data(country, indicator)
        historical_data = load_historical_data(country, indicator) if include_historical else None

        # Create figure
        fig = go.Figure()

        # Add historical trace (if enabled)
        if include_historical and historical_data is not None:
            fig.add_trace(go.Scatter(
                x=historical_data['date'],
                y=historical_data['value'],
                name='Historical',
                mode='lines',
                line=dict(color='#718096')
            ))

        # Add prediction trace
        fig.add_trace(go.Scatter(
            x=prediction_data['date'],
            y=prediction_data['forecast'],
            name='Forecast',
            mode='lines+markers',
            line=dict(color='#E53E3E', dash='dash')
        ))

        # Update layout
        fig.update_layout(...)

        return fig
    """
    # PLACEHOLDER IMPLEMENTATION - Replace with your chart logic
    fig = go.Figure()

    # Add placeholder annotation
    fig.add_annotation(
        text=f"<b>Prediction Chart Placeholder</b><br><br>"
             f"Country: {country}<br>"
             f"Indicator: {indicator}<br>"
             f"Historical Data: {'Included' if include_historical else 'Excluded'}<br><br>"
             f"<i>Replace create_prediction_chart() function<br>"
             f"in features/scenario/charts.py<br>"
             f"with your custom implementation</i>",
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        xanchor='center',
        yanchor='middle',
        showarrow=False,
        font=dict(size=14, color="#4A5568"),
        align='center'
    )

    # Apply configuration from config_macro
    fig.update_layout(
        title=f"{indicator} Forecast - {country}",
        template=PREDICTION_CHART_CONFIG['template'],
        height=PREDICTION_CHART_CONFIG['height'],
        xaxis=dict(
            title="Date",
            showgrid=True,
            gridcolor='#E2E8F0'
        ),
        yaxis=dict(
            title=indicator,
            showgrid=True,
            gridcolor='#E2E8F0'
        ),
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    return fig
