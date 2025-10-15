import dash
from dash import dcc, html, Input, Output, callback, State
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime

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
# INITIALIZATION
# ============================================================================
app = dash.Dash(__name__)

# ============================================================================
# DATA LOADING
# ============================================================================
try:
    sample_data = pd.read_csv('Example_df.csv')
    sample_data['Date'] = pd.to_datetime(sample_data['Date'], format='%Y-%m')
    sample_data = sample_data.rename(columns={'Date': 'date'})
    sample_data = sample_data.sort_values('date').reset_index(drop=True)
    print(f"Successfully loaded {len(sample_data)} records from Example_df.csv")

    tool_sample = pd.read_csv('Example_correction.csv')
    tool_sample['Date'] = pd.to_datetime(tool_sample['Date'], format='%Y-%m')
    tool_sample = tool_sample.rename(columns={'Date': 'date'})
    tool_sample = tool_sample.sort_values('date').reset_index(drop=True)
    print(f"Successfully loaded {len(tool_sample)} records from Example_correction.csv")

except FileNotFoundError:
    print("Example_df.csv not found.")
    print("Example_correction.csv not found.")

min_year = sample_data['date'].dt.year.min()
max_year = sample_data['date'].dt.year.max()
year_marks = {year: {'label': str(year)} for year in range(min_year, max_year + 1)}

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def format_number(value):
    """Format numbers to billions, millions, or thousands"""
    if abs(value) >= 1e8:
        return f"{value/1e9:.2f}B"
    elif abs(value) >= 1e5:
        return f"{value/1e6:.2f}M"
    elif abs(value) >= 1e2:
        return f"{value/1e3:.2f}K"
    else:
        return f"{value:.2f}"

def format_hover_value(value):
    """Format hover values with one extra decimal compared to axis"""
    if abs(value) >= 1e8:
        return f"{value/1e9:.3f}B"
    elif abs(value) >= 1e5:
        return f"{value/1e6:.3f}M"
    elif abs(value) >= 1e2:
        return f"{value/1e3:.3f}K"
    else:
        return f"{value:.3f}"


def generate_enhanced_comparison_text_updated(amount_old, amount_new, income_old, income_new, date1, date2, 
                                            filter_var, filter_values, group_var, df1, df2, selected_type, amount_col, income_col):
    """Generate comprehensive comparison analysis text"""
    def create_change_sentence(variable, old_val, new_val, date1, date2):
        if abs((new_val - old_val) / old_val) < 0.01 if old_val != 0 else abs(new_val) < 0.01:
            change_type = "remained essentially equal"
            relative_change = 0
        elif new_val > old_val:
            change_type = "increased"
            relative_change = ((new_val - old_val) / old_val * 100) if old_val != 0 else 100
        else:
            change_type = "decreased"
            relative_change = ((new_val - old_val) / old_val * 100) if old_val != 0 else -100
        
        if change_type == "remained essentially equal":
            return f"{variable} amount was {old_val:.1f} in {date1.strftime('%Y-%m')} and {change_type} at {new_val:.1f} in {date2.strftime('%Y-%m')}."
        else:
            return f"{variable} amount was {old_val:.1f} in {date1.strftime('%Y-%m')} and {change_type} to {new_val:.1f} in {date2.strftime('%Y-%m')}, which corresponds to a relative {change_type.replace('increased', 'increase').replace('decreased', 'decrease')} of {abs(relative_change):.1f}%."
    
    text_parts = [f"COMPARISON ANALYSIS - {selected_type}:\n", "=" * 30 + "\n\n"]
    if filter_var != "none" and filter_values:
        text_parts.append(f"Analysis filtered by {filter_var}: {', '.join(filter_values)}.\n\n")
    
    text_parts.append(create_change_sentence(f"Amount ({selected_type})", amount_old, amount_new, date1, date2) + "\n\n")
    text_parts.append(create_change_sentence(f"Income ({selected_type})", income_old, income_new, date1, date2) + "\n\n")
    
    ratio_old = (income_old / amount_old) if amount_old != 0 else 0
    ratio_new = (income_new / amount_new) if amount_new != 0 else 0
    ratio_change = ratio_new - ratio_old
    
    if abs(ratio_change) < 0.01:
        text_parts.append(f"The Return Ratio (Income/Amount) remained stable at approximately {ratio_old:.2f}.\n\n")
    elif ratio_change > 0:
        text_parts.append(f"The Return Ratio (Income/Amount) improved from {ratio_old:.2f} to {ratio_new:.2f}, representing an increase of {ratio_change:.2f}.\n\n")
    else:
        text_parts.append(f"The Return Ratio (Income/Amount) declined from {ratio_old:.2f} to {ratio_new:.2f}, representing a decrease of {abs(ratio_change):.2f}.\n\n")
    
    # Determine which grouping variable to analyze (default to Item if none selected)
    analysis_group_var = group_var if group_var != "none" else "Function"
    
    if analysis_group_var in ['Division', 'Type', 'Item', 'Function'] and not df1.empty and not df2.empty:
        text_parts.append(f"PROPORTION ANALYSIS BY {analysis_group_var.upper()}:\n" + "=" * 30 + "\n\n")
        
        for col, label in [(amount_col, "Amount"), (income_col, "Income")]:
            groups1 = df1.groupby(analysis_group_var)[col].sum()
            total1 = df1[col].sum()
            props1 = (groups1 / total1 * 100) if total1 > 0 else pd.Series(dtype=float)
            
            groups2 = df2.groupby(analysis_group_var)[col].sum()
            total2 = df2[col].sum()
            props2 = (groups2 / total2 * 100) if total2 > 0 else pd.Series(dtype=float)
            
            text_parts.append(f"{label} ({selected_type}) Proportion Changes by {analysis_group_var}:\n")
            for group in sorted(set(props1.index) | set(props2.index)):
                prop1, prop2 = props1.get(group, 0), props2.get(group, 0)
                amt1, amt2 = groups1.get(group, 0), groups2.get(group, 0)
                prop_change = prop2 - prop1
                change_desc = "increased" if prop_change > 0 else "decreased" if prop_change < 0 else "remained stable"
                text_parts.append(f"• {group}: {prop1:.1f}% → {prop2:.1f}% ({change_desc} by {abs(prop_change):.1f}pp), amounts: {format_number(amt1)} → {format_number(amt2)}\n")
            text_parts.append("\n")
    
    # Always analyze Division contribution (stacked bar chart)
    if 'Division' in df1.columns and 'Division' in df2.columns and not df1.empty and not df2.empty:
        text_parts.append("DIVISION PERCENTAGE CONTRIBUTION:\n" + "=" * 30 + "\n\n")
        
        for col, label in [(amount_col, "Amount"), (income_col, "Income")]:
            div1 = df1.groupby('Division')[col].sum()
            total1 = div1.sum()
            pct1 = (div1 / total1 * 100) if total1 > 0 else pd.Series(dtype=float)
            
            div2 = df2.groupby('Division')[col].sum()
            total2 = div2.sum()
            pct2 = (div2 / total2 * 100) if total2 > 0 else pd.Series(dtype=float)
            
            text_parts.append(f"{label} ({selected_type}) Division Contribution:\n")
            for division in sorted(set(pct1.index) | set(pct2.index)):
                p1, p2 = pct1.get(division, 0), pct2.get(division, 0)
                pct_change = p2 - p1
                change_desc = "increased" if pct_change > 0 else "decreased" if pct_change < 0 else "remained stable"
                text_parts.append(f"• {division}: {p1:.1f}% → {p2:.1f}% ({change_desc} by {abs(pct_change):.1f}pp)\n")
            text_parts.append("\n")
    
    # Add Tool Sample (Income Correction) Analysis
    try:
        # Filter tool_sample data for the same date range and criteria
        tool_date1 = tool_sample[tool_sample['date'] == date1].copy()
        tool_date2 = tool_sample[tool_sample['date'] == date2].copy()
        
        # Apply same filtering criteria
        if filter_var != "none" and filter_values and filter_var in tool_date1.columns:
            tool_date1 = tool_date1[tool_date1[filter_var].isin(filter_values)]
            tool_date2 = tool_date2[tool_date2[filter_var].isin(filter_values)]
        
        if not tool_date1.empty or not tool_date2.empty:
            text_parts.append("INCOME CORRECTION ANALYSIS (Tool Data):\n" + "=" * 30 + "\n\n")
            
            # Total income corrections
            corr_total1 = tool_date1['Income_corr'].sum() if not tool_date1.empty else 0
            corr_total2 = tool_date2['Income_corr'].sum() if not tool_date2.empty else 0
            
            if corr_total1 > 0 or corr_total2 > 0:
                corr_change = corr_total2 - corr_total1
                corr_pct_change = (corr_change / corr_total1 * 100) if corr_total1 != 0 else (100 if corr_total2 > 0 else 0)
                change_desc = "increased" if corr_change > 0 else "decreased" if corr_change < 0 else "remained stable"
                
                text_parts.append(f"Total Income Correction was {format_number(corr_total1)} in {date1.strftime('%Y-%m')} and {change_desc} to {format_number(corr_total2)} in {date2.strftime('%Y-%m')}")
                if abs(corr_pct_change) > 0.01:
                    text_parts.append(f", representing a {abs(corr_pct_change):.1f}% change.\n\n")
                else:
                    text_parts.append(".\n\n")
                
                # Breakdown by Function
                if 'Function' in tool_date1.columns or 'Function' in tool_date2.columns:
                    text_parts.append("Income Correction by Function:\n")
                    
                    func1 = tool_date1.groupby('Function')['Income_corr'].sum() if not tool_date1.empty and 'Function' in tool_date1.columns else pd.Series(dtype=float)
                    func2 = tool_date2.groupby('Function')['Income_corr'].sum() if not tool_date2.empty and 'Function' in tool_date2.columns else pd.Series(dtype=float)
                    
                    all_functions = sorted(set(func1.index) | set(func2.index))
                    for function in all_functions:
                        f1, f2 = func1.get(function, 0), func2.get(function, 0)
                        f_change = f2 - f1
                        f_pct_change = (f_change / f1 * 100) if f1 != 0 else (100 if f2 > 0 else 0)
                        f_change_desc = "increased" if f_change > 0 else "decreased" if f_change < 0 else "remained stable"
                        
                        text_parts.append(f"• {function}: {format_number(f1)} → {format_number(f2)} ({f_change_desc}")
                        if abs(f_pct_change) > 0.01:
                            text_parts.append(f" by {abs(f_pct_change):.1f}%)\n")
                        else:
                            text_parts.append(")\n")
                    text_parts.append("\n")
    except Exception as e:
        # Silently skip if tool_sample data not available
        pass
    
    text_parts.extend(["SUMMARY:\n", "=" * 30 + "\n", "• [Add your key insights here]\n", "• [Note any significant patterns]\n", "• [Record actionable findings]"])
    return "".join(text_parts)

def create_dumbbell_chart_updated(df1, df2, variable, date1, date2, group_var, selected_type, var_label):
    """Create a dumbbell chart showing proportion changes"""
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
        fig.update_layout(title=f"{var_label} Proportions by {group_var} - {selected_type}", template="plotly_white", height=350)
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
            name=f"{date1.strftime('%Y-%m')}", legendgroup="date1", showlegend=(i == 0),
            hovertemplate=f"<b>{group}</b><br>Month: {date1.strftime('%Y-%m')}<br>Proportion: {prop1:.1f}%<br>Amount: {format_number(val1)}<extra></extra>"))
        fig.add_trace(go.Scatter(x=[prop2], y=[i], mode='markers',
            marker=dict(size=size2, color='lightcoral', line=dict(width=2, color='red')),
            name=f"{date2.strftime('%Y-%m')}", legendgroup="date2", showlegend=(i == 0),
            hovertemplate=f"<b>{group}</b><br>Month: {date2.strftime('%Y-%m')}<br>Proportion: {prop2:.1f}%<br>Amount: {format_number(val2)}<extra></extra>"))
    
    fig.update_layout(title=f"{var_label} Proportions by {group_var} - {selected_type}", xaxis_title="Proportion (%)",
        yaxis=dict(tickmode='array', tickvals=list(range(len(all_groups))), ticktext=list(sorted(all_groups)), title=group_var),
        template="plotly_white", height=350, showlegend=True, margin=dict(l=100, r=50, t=80, b=50))
    return fig

# ============================================================================
# APP LAYOUT
# ============================================================================
app.layout = dmc.MantineProvider(
    theme={"colorScheme": "light", "primaryColor": "gray"},
    children=[dmc.AppShell(
        id="app-shell", header={"height": 60}, navbar={"width": 250, "breakpoint": "sm"}, padding="md",
        children=[
            dmc.AppShellHeader(px="md", children=[
                dmc.Group(justify="space-between", h="100%", children=[
                    dmc.Title("Dashboard", order=3, c="blue"),
                    dmc.Text(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", size="sm", c="dimmed"),
                ])
            ]),
            dmc.AppShellNavbar(p="md", children=[
                dmc.Title("Navigation", order=4, mb="md"),
                dmc.NavLink(label="Today", id="nav-today", leftSection=DashIconify(icon="material-symbols:today", width=20), active=True),
                dmc.NavLink(label="Scenario", id="nav-scenario", leftSection=DashIconify(icon="material-symbols:analytics", width=20)),
            ]),
            dmc.AppShellMain(id="main-content", children=[
                html.Div(id="today-content", style={"display": "block"}, children=[
                    dmc.Tabs(value="history", id="main-tabs", children=[
                        dmc.TabsList([
                            dmc.TabsTab("History", value="history"),
                            dmc.TabsTab("Comparison", value="comparison"),
                            dmc.TabsTab("Tool", value="tool"),
                        ]),
                        dmc.TabsPanel(value="history", children=[
                            dmc.Grid([
                                dmc.GridCol(span=8, children=[
                                    dmc.Card([
                                        dmc.CardSection([
                                            dmc.Title("Chart Controls", order=4, mb="md"),
                                            dmc.Group([
                                                dmc.Stack([
                                                    dmc.Text("Display Variable:", size="sm", fw=500, mb=5),
                                                    dmc.SegmentedControl(id="variable-selector", value="Total", orientation="vertical",
                                                        fullWidth=False, color="blue", size="sm", style={"width": "120px"},
                                                        data=[{"value": "Total", "label": "Total"}, {"value": "Type1", "label": "Type 1"},
                                                            {"value": "Type2", "label": "Type 2"}, {"value": "Type3", "label": "Type 3"}]),
                                                ], gap="xs", align="flex-start"),
                                                dmc.Stack([
                                                    dmc.Text("Year Range:", size="sm", fw=500, mb=5),
                                                    dmc.RangeSlider(
                                                        id="year-range-slider",
                                                        min=min_year,
                                                        max=max_year,
                                                        step=1,
                                                        value=[min_year, max_year],
                                                        marks=[{"value": year, "label": str(year)} for year in range(min_year, max_year + 1)],
                                                        mb="md",
                                                        minRange=1,
                                                        size="md",
                                                        style={"width": "100%"}
                                                    )
                                                ], gap="xs", style={"flex": 1}),
                                            ], justify="space-between", align="flex-start", mb="lg"),
                                            dmc.Grid([
                                                dmc.GridCol(span=4, children=[dmc.Text("Filter by:", size="sm", fw=500, mb=5),
                                                    dmc.Select(id="filter-selector", placeholder="Select filter", value="none", size="sm",
                                                        data=[{"value": "none", "label": "No Filter"}, {"value": "Division", "label": "Division"},
                                                            {"value": "Type", "label": "Type"}, {"value": "Item", "label": "Item"}, {"value": "Function", "label": "Function"}])]),
                                                dmc.GridCol(span=4, children=[dmc.Text("Stack by:", size="sm", fw=500, mb=5),
                                                    dmc.Select(id="stack-selector", placeholder="Select stack variable", value="none", size="sm",
                                                        data=[{"value": "none", "label": "No Stack"}, {"value": "Division", "label": "Division"},
                                                            {"value": "Type", "label": "Type"}, {"value": "Item", "label": "Item"}, {"value": "Function", "label": "Function"}])]),
                                                dmc.GridCol(span=4, children=[dmc.Text("Group by:", size="sm", fw=500, mb=5),
                                                    dmc.Select(id="group-selector", placeholder="Select group variable", value="none", size="sm",
                                                        data=[{"value": "none", "label": "No Grouping"}, {"value": "Division", "label": "Division"},
                                                            {"value": "Type", "label": "Type"}, {"value": "Item", "label": "Item"}, {"value": "Function", "label": "Function"}])]),
                                            ], gutter="md", mb="lg"),
                                            html.Div([dmc.Text("Filter values:", size="sm", fw=500, mb=5),
                                                dmc.MultiSelect(id="filter-values-selector", placeholder="Select values", data=[], value=[], size="sm", disabled=True)],
                                                style={"width": "100%"}),
                                        ], withBorder=True, inheritPadding=True, py="md"),
                                        dmc.CardSection([dmc.Title("Summary Metrics", order=5, mb="sm"), html.Div(id="history-summary-boxes")],
                                            inheritPadding=True, pt="xs"),
                                        dmc.CardSection([dmc.Title("Amount Analysis", order=5, mb="sm"), dcc.Graph(id="amount-barchart", style={"height": "350px"})],
                                            inheritPadding=True, pt="xs"),
                                        dmc.CardSection([dmc.Title("Income Analysis", order=5, mb="sm"), dcc.Graph(id="income-barchart", style={"height": "350px"})],
                                            inheritPadding=True, pt="xs"),
                                        dmc.CardSection([dmc.Title("Return Ratio (Income/Amount)", order=5, mb="sm"), dcc.Graph(id="ratio-chart", style={"height": "250px"})],
                                            inheritPadding=True, pt="xs"),
                                        dmc.CardSection([
                                            dmc.Button("Export History Data - Excel", id="history-export-btn", variant="outline", size="sm", fullWidth=True),
                                            dcc.Download(id="download-history-data"),
                                        ], inheritPadding=True, pt="xs"),
                                    ], withBorder=True, shadow="sm", radius="md", mb="md")
                                ]),
                                dmc.GridCol(span=4, children=[
                                    dmc.Card([
                                        dmc.CardSection([dmc.Title("Analysis Notes", order=4, mb="md"),
                                            dmc.Textarea(id="analysis-textbox", placeholder="Enter your analysis notes here...", autosize=True, minRows=15, maxRows=20,
                                                value="Chart Analysis:\n\n• Use the controls on the left to modify the visualization\n• Switch between Total and Type 1/2/3 for different metrics\n• Apply filters to focus on specific data subsets\n• Use stacking to show composition\n• Group data for comparative analysis\n\nKey Insights:\n• [Add your observations here]\n• [Identify trends and patterns]\n• [Note any anomalies or interesting findings]")
                                        ], withBorder=True, inheritPadding=True, py="xs"),
                                        dmc.CardSection([dmc.Button("Save Analysis", id="save-analysis-btn", variant="filled", size="sm", fullWidth=True)],
                                            inheritPadding=True, pt="xs")
                                    ], withBorder=True, shadow="sm", radius="md", h="100%")
                                ])
                            ], gutter="md")
                        ]),
                        dmc.TabsPanel(value="comparison", children=[
                            dmc.Stack([
                                dmc.Card([
                                    dmc.CardSection([
                                        dmc.Title("Comparison Controls", order=4, mb="md"),
                                        dmc.Group([dmc.Stack([dmc.Text("Display Type:", size="sm", fw=500, mb=5),
                                            dmc.SegmentedControl(id="comparison-type-selector", value="Total", orientation="horizontal", fullWidth=False, color="blue", size="sm",
                                                data=[{"value": "Total", "label": "Total"}, {"value": "Type1", "label": "Type 1"},
                                                    {"value": "Type2", "label": "Type 2"}, {"value": "Type3", "label": "Type 3"}])],
                                            gap="xs", style={"flex": 1})], justify="flex-start", align="flex-start", mb="lg"),
                                        dmc.Group([dmc.Stack([dmc.Text("Select Dates for Comparison:", size="sm", fw=500, mb=5),
                                            dmc.MultiSelect(id="comparison-date-selector", placeholder="Select exactly 2 dates to compare", data=[], value=[],
                                                maxValues=2, size="sm", searchable=True, clearable=True, leftSection=DashIconify(icon="material-symbols:calendar-month", width=20),
                                                styles={"dropdown": {"maxHeight": "200px", "overflowY": "auto"}, "input": {"minWidth": "300px"}})],
                                            gap="xs", style={"flex": 1})], justify="flex-start", align="flex-start", mb="lg"),
                                        dmc.Grid([
                                            dmc.GridCol(span=4, children=[dmc.Text("Filter by:", size="sm", fw=500, mb=5),
                                                dmc.Select(id="comparison-filter-selector", placeholder="Select filter", value="none", size="sm",
                                                    data=[{"value": "none", "label": "No Filter"}, {"value": "Division", "label": "Division"},
                                                        {"value": "Type", "label": "Type"}, {"value": "Item", "label": "Item"}, {"value": "Function", "label": "Function"}])]),
                                            dmc.GridCol(span=4, children=[dmc.Text("Stack by:", size="sm", fw=500, mb=5),
                                                dmc.Select(id="comparison-stack-selector", placeholder="Select stack variable", value="none", size="sm",
                                                    data=[{"value": "none", "label": "No Stack"}, {"value": "Division", "label": "Division"},
                                                        {"value": "Type", "label": "Type"}, {"value": "Item", "label": "Item"}, {"value": "Function", "label": "Function"}])]),
                                            dmc.GridCol(span=4, children=[dmc.Text("Group by:", size="sm", fw=500, mb=5),
                                                dmc.Select(id="comparison-group-selector", placeholder="Select group variable", value="none", size="sm",
                                                    data=[{"value": "none", "label": "No Grouping"}, {"value": "Division", "label": "Division"},
                                                        {"value": "Type", "label": "Type"}, {"value": "Item", "label": "Item"}, {"value": "Function", "label": "Function"}])]),
                                        ], gutter="md", mb="lg"),
                                        html.Div([dmc.Text("Filter values:", size="sm", fw=500, mb=5),
                                            dmc.MultiSelect(id="comparison-filter-values-selector", placeholder="Select values", data=[], value=[], size="sm", disabled=True)],
                                            style={"width": "100%"}),
                                    ], withBorder=True, inheritPadding=True, py="md"),
                                ], withBorder=True, shadow="sm", radius="md", mb="md"),
                                dmc.Card([
                                    dmc.CardSection([dmc.Title("Comparison Notes", order=4, mb="md"),
                                        dmc.Textarea(id="comparison-textbox", placeholder="Enter your comparison analysis notes here...", autosize=True, minRows=8, maxRows=15,
                                            value="Comparison Analysis:\n\n• Select exactly 2 dates to compare data\n• Use filters and grouping to focus analysis\n• Monitor value changes and ratios\n• Identify significant trends between periods")],
                                        withBorder=True, inheritPadding=True, py="xs"),
                                    dmc.CardSection([dmc.Button("Save Comparison", id="save-comparison-btn", variant="filled", size="sm", fullWidth=True)],
                                        inheritPadding=True, pt="xs")
                                ], withBorder=True, shadow="sm", radius="md", mb="md"),
                                dmc.Card([
                                    dmc.CardSection([dmc.Title("Comparison Metrics", order=5, mb="sm"), html.Div(id="comparison-value-boxes")],
                                        inheritPadding=True, pt="xs"),
                                    dmc.CardSection([dmc.Grid([
                                        dmc.GridCol([dmc.Title("Amount Total Comparison", order=5, mb="sm"), dcc.Graph(id="comparison-var1-chart", style={"height": "300px"})], span=6),
                                        dmc.GridCol([dmc.Title("Income Total Comparison", order=5, mb="sm"), dcc.Graph(id="comparison-var2-chart", style={"height": "300px"})], span=6),
                                    ], gutter="md")], inheritPadding=True, pt="xs"),
                                    dmc.CardSection([dmc.Title("Proportion Changes Analysis", order=5, mb="sm"),
                                        dmc.Grid([
                                            dmc.GridCol([dmc.Title("Amount Total Proportion Changes", order=6, mb="sm"), dcc.Graph(id="var1-dumbbell-chart", style={"height": "350px"})], span=6),
                                            dmc.GridCol([dmc.Title("Income Total Proportion Changes", order=6, mb="sm"), dcc.Graph(id="var2-dumbbell-chart", style={"height": "350px"})], span=6),
                                        ], gutter="md")], inheritPadding=True, pt="xs"),
                                    dmc.CardSection([dmc.Title("Division Percentage Contribution", order=5, mb="sm"),
                                        dmc.Grid([
                                            dmc.GridCol([dmc.Title("Amount by Division", order=6, mb="sm"), dcc.Graph(id="amount-division-chart", style={"height": "350px"})], span=6),
                                            dmc.GridCol([dmc.Title("Income by Division", order=6, mb="sm"), dcc.Graph(id="income-division-chart", style={"height": "350px"})], span=6),
                                        ], gutter="md")], inheritPadding=True, pt="xs"),
                                    dmc.CardSection([
                                        dmc.Button("Export Comparison Data - Excel", id="export-excel-btn", variant="outline", size="sm"),
                                        dcc.Download(id="download-dataframe-xlsx"),
                                    ], inheritPadding=True, pt="xs"),
                                ], withBorder=True, shadow="sm", radius="md")
                            ], gap="md")
                        ]),
                        dmc.TabsPanel(value="tool", children=[
                            dmc.Stack([
                                dmc.Card([
                                    dmc.CardSection([
                                        dmc.Title("Tool Controls", order=4, mb="md"),
                                        dmc.Stack([
                                            dmc.Text("Year Range:", size="sm", fw=500, mb=5),
                                            dmc.RangeSlider(
                                                id="tool-year-range-slider",
                                                min=min_year,
                                                max=max_year,
                                                step=1,
                                                value=[min_year, max_year],
                                                marks=[{"value": year, "label": str(year)} for year in range(min_year, max_year + 1)],
                                                mb="md",
                                                minRange=1,
                                                size="md",
                                                style={"width": "100%"}
                                            )
                                        ], gap="xs", mb="lg"),
                                        dmc.Grid([
                                            dmc.GridCol(span=4, children=[
                                                dmc.Text("Filter by Division:", size="sm", fw=500, mb=5),
                                                dmc.Select(id="tool-division-filter", placeholder="Select Division", value="none", size="sm",
                                                    data=[{"value": "none", "label": "All Divisions"}] + 
                                                        [{"value": val, "label": val} for val in sorted(sample_data['Division'].unique())])
                                            ]),
                                            dmc.GridCol(span=4, children=[
                                                dmc.Text("Filter by Item:", size="sm", fw=500, mb=5),
                                                dmc.Select(id="tool-item-filter", placeholder="Select Item", value="none", size="sm",
                                                    data=[{"value": "none", "label": "All Items"}] + 
                                                        [{"value": val, "label": val} for val in sorted(sample_data['Item'].unique())])
                                            ]),
                                            dmc.GridCol(span=4, children=[
                                                dmc.Text("Filter by Function:", size="sm", fw=500, mb=5),
                                                dmc.Select(id="tool-function-filter", placeholder="Select Function", value="none", size="sm",
                                                    data=[{"value": "none", "label": "All Functions"}] + 
                                                        [{"value": val, "label": val} for val in sorted(sample_data['Function'].unique())])
                                            ]),
                                        ], gutter="md", mb="lg"),
                                    ], withBorder=True, inheritPadding=True, py="md"),
                                ], withBorder=True, shadow="sm", radius="md", mb="md"),
                                
                                dmc.Card([
                                    dmc.CardSection([
                                        dmc.Title("Income Analysis: Original vs Corrected", order=4, mb="md"),
                                        dcc.Graph(id="tool-income-chart", style={"height": "500px"})
                                    ], inheritPadding=True, pt="xs"),
                                    dmc.CardSection([
                                        dmc.Button("Export Tool Data - Excel", id="tool-export-btn", variant="outline", size="sm", fullWidth=True),
                                        dcc.Download(id="download-tool-data"),
                                    ], inheritPadding=True, pt="xs"),
                                ], withBorder=True, shadow="sm", radius="md")
                            ], gap="md")
                        ]),
                    ])
                ]),
                html.Div(id="scenario-content", style={"display": "none"}, children=[
                    dmc.Center([dmc.Stack([dmc.Title("Scenario Page", order=2), dmc.Text("This page is ready for scenario analysis implementation.", c="dimmed")],
                        align="center")], style={"height": "400px"})
                ])
            ])
        ]
    )]
)

# ============================================================================
# CALLBACKS
# ============================================================================
@callback([Output("filter-values-selector", "data"), Output("filter-values-selector", "disabled"), Output("filter-values-selector", "value")],
    [Input("filter-selector", "value")])
def update_filter_values(filter_var):
    if filter_var == "none":
        return [], True, []
    if filter_var in ['Division', 'Type', 'Item', 'Function']:
        unique_values = sample_data[filter_var].unique()
        options = [{"value": val, "label": val} for val in sorted(unique_values)]
        return options, False, list(unique_values)
    return [], True, []

@callback([Output("history-summary-boxes", "children"), Output("amount-barchart", "figure"), Output("income-barchart", "figure"), Output("ratio-chart", "figure")],
    [Input("variable-selector", "value"), Input("filter-selector", "value"), Input("filter-values-selector", "value"),
     Input("stack-selector", "value"), Input("group-selector", "value"), Input("year-range-slider", "value")])
def update_barcharts(selected_type, filter_var, filter_values, stack_var, group_var, year_range):
    if selected_type == "Total":
        amount_col, income_col = "Amount_total", "Income_total"
    elif selected_type == "Type1":
        amount_col, income_col = "Amount_1", "Income_1"
    elif selected_type == "Type2":
        amount_col, income_col = "Amount_2", "Income_2"
    else:
        amount_col, income_col = "Amount_3", "Income_3"
    
    df = sample_data.copy()
    df = df[(df['date'].dt.year >= year_range[0]) & (df['date'].dt.year <= year_range[1])]
    if filter_var != "none" and filter_var in df.columns and filter_values:
        df = df[df[filter_var].isin(filter_values)]
    df['month'] = df['date'].dt.to_period('M').astype(str)
    
    monthly_totals = df.groupby('month').agg({amount_col: 'sum', income_col: 'sum'}).reset_index()
    avg_amount = monthly_totals[amount_col].mean()
    avg_income = monthly_totals[income_col].mean()
    avg_ratio = (monthly_totals[income_col].sum() / monthly_totals[amount_col].sum()) if monthly_totals[amount_col].sum() != 0 else 0
    
    summary_boxes = dmc.SimpleGrid([
        dmc.Card([dmc.Stack([dmc.Text(f"Average Amount - {selected_type}", size="sm", c="dimmed"),
            dmc.Text(format_number(avg_amount), size="xl", fw=700, c="blue"), dmc.Text("Monthly average", size="xs", c="dimmed")],
            gap="xs")], withBorder=True, shadow="sm", radius="md", p="md"),
        dmc.Card([dmc.Stack([dmc.Text(f"Average Income - {selected_type}", size="sm", c="dimmed"),
            dmc.Text(format_number(avg_income), size="xl", fw=700, c="orange"), dmc.Text("Monthly average", size="xs", c="dimmed")],
            gap="xs")], withBorder=True, shadow="sm", radius="md", p="md"),
        dmc.Card([dmc.Stack([dmc.Text(f"Return Ratio - {selected_type}", size="sm", c="dimmed"),
            dmc.Text(f"{avg_ratio*100:.2f}%", size="xl", fw=700, c="green"), dmc.Text("Income/Amount ratio", size="xs", c="dimmed")],
            gap="xs")], withBorder=True, shadow="sm", radius="md", p="md"),
    ], cols=3, spacing="sm", mb="lg")
    
    def create_bar_chart(variable_col, title):
        fig = go.Figure()
        if stack_var != "none" and stack_var in df.columns and stack_var in ['Division', 'Type', 'Item', 'Function']:
            stacked_data = df.groupby(['month', stack_var])[variable_col].sum().unstack(fill_value=0)
            colors = get_color_sequence('stacked', len(stacked_data.columns))
            for i, category in enumerate(stacked_data.columns):
                hover_text = [format_hover_value(v) for v in stacked_data[category]]
                fig.add_trace(go.Bar(x=stacked_data.index, y=stacked_data[category], name=f"{category}",
                    marker_color=colors[i],
                    text=[format_number(v) for v in stacked_data[category]], textposition='auto',
                    customdata=hover_text,
                    hovertemplate='<b>%{x}</b><br>' + f'{category}<br>' + 'Value: %{customdata}<extra></extra>'))
            fig.update_layout(barmode='stack')
        elif group_var != "none" and group_var in df.columns and group_var in ['Division', 'Type', 'Item', 'Function']:
            categories = sorted(df[group_var].unique())
            colors = get_color_sequence('grouped', len(categories))
            for i, category in enumerate(categories):
                category_data = df[df[group_var] == category]
                monthly_data = category_data.groupby('month')[variable_col].sum().reset_index()
                hover_text = [format_hover_value(v) for v in monthly_data[variable_col]]
                fig.add_trace(go.Bar(x=monthly_data['month'], y=monthly_data[variable_col], name=f"{category}",
                    marker_color=colors[i],
                    text=[format_number(v) for v in monthly_data[variable_col]], textposition='auto',
                    customdata=hover_text,
                    hovertemplate='<b>%{x}</b><br>' + f'{category}<br>' + 'Value: %{customdata}<extra></extra>'))
            fig.update_layout(barmode='group')
        else:
            monthly_data = df.groupby('month')[variable_col].sum().reset_index()
            hover_text = [format_hover_value(v) for v in monthly_data[variable_col]]
            fig.add_trace(go.Bar(x=monthly_data['month'], y=monthly_data[variable_col], name=title,
                marker_color=get_color_sequence('bar', 1)[0],
                text=[format_number(v) for v in monthly_data[variable_col]], textposition='auto',
                customdata=hover_text,
                hovertemplate='<b>%{x}</b><br>Value: %{customdata}<extra></extra>'))
        
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
            
        fig.update_layout(title=title, xaxis_title="Month", template="plotly_white",
            showlegend=True, height=350, margin=dict(l=50, r=50, t=60, b=50))
        fig.update_xaxes(tickangle=45)
        return fig
    
    amount_chart = create_bar_chart(amount_col, f"Amount - {selected_type}")
    income_chart = create_bar_chart(income_col, f"Income - {selected_type}")
    
    ratio_fig = go.Figure()
    if group_var != "none" and group_var in df.columns and group_var in ['Division', 'Type', 'Item', 'Function']:
        categories = sorted(df[group_var].unique())
        colors = get_color_sequence('line', len(categories))
        for i, category in enumerate(categories):
            category_data = df[df[group_var] == category]
            monthly_data = category_data.groupby('month').agg({amount_col: 'sum', income_col: 'sum'}).reset_index()
            monthly_data['ratio'] = (monthly_data[income_col] / monthly_data[amount_col].replace(0, np.nan)) * 100
            ratio_fig.add_trace(go.Scatter(x=monthly_data['month'], y=monthly_data['ratio'],
                mode='lines+markers', name=f"{category}", line=dict(color=colors[i], width=2), marker=dict(size=6)))
    else:
        monthly_data = df.groupby('month').agg({amount_col: 'sum', income_col: 'sum'}).reset_index()
        monthly_data['ratio'] = (monthly_data[income_col] / monthly_data[amount_col].replace(0, np.nan)) * 100
        ratio_fig.add_trace(go.Scatter(x=monthly_data['month'], y=monthly_data['ratio'],
            mode='lines+markers', name='Return Ratio', line=dict(color=get_color_sequence('line', 1)[0], width=3), marker=dict(size=8)))
    
    ratio_fig.update_layout(title=f"Return Ratio (Income/Amount) - {selected_type}", xaxis_title="Month", yaxis_title="Ratio (%)",
        template="plotly_white", height=250, margin=dict(l=50, r=50, t=60, b=100), showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=-0.35, xanchor="center", x=0.5))
    ratio_fig.update_xaxes(tickangle=45)
    ratio_fig.update_yaxes(ticksuffix="%")
    
    return summary_boxes, amount_chart, income_chart, ratio_fig

@callback(Output("comparison-date-selector", "data"), Input("main-tabs", "value"))
def populate_comparison_dates(active_tab):
    if active_tab == "comparison":
        unique_dates = sorted(sample_data['date'].dt.to_period('M').unique())
        return [{"value": str(date), "label": str(date)} for date in unique_dates]
    return []

@callback(
    [Output("comparison-filter-values-selector", "data"), Output("comparison-filter-values-selector", "disabled"), 
     Output("comparison-filter-values-selector", "value")],
    [Input("comparison-filter-selector", "value")]
)
def update_comparison_filter_values(filter_var):
    if filter_var == "none":
        return [], True, []
    if filter_var in ['Division', 'Type', 'Item', 'Function']:
        unique_values = sample_data[filter_var].unique()
        options = [{"value": val, "label": val} for val in sorted(unique_values)]
        return options, False, list(unique_values)
    return [], True, []

@callback(
    [Output("comparison-value-boxes", "children"), Output("comparison-var1-chart", "figure"), 
     Output("comparison-var2-chart", "figure"), Output("var1-dumbbell-chart", "figure"), 
     Output("var2-dumbbell-chart", "figure"), Output("amount-division-chart", "figure"),
     Output("income-division-chart", "figure"), Output("comparison-textbox", "value")],
    [Input("comparison-type-selector", "value"), Input("comparison-date-selector", "value"), 
     Input("comparison-filter-selector", "value"), Input("comparison-filter-values-selector", "value"),
     Input("comparison-stack-selector", "value"), Input("comparison-group-selector", "value")]
)
def update_enhanced_comparison_content(selected_type, selected_dates, filter_var, filter_values, stack_var, group_var):
    if selected_type == "Total":
        amount_col, income_col = "Amount_total", "Income_total"
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
        return empty_boxes, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, empty_fig, default_text
    
    date1, date2 = sorted([pd.to_datetime(date + '-01') for date in selected_dates])
    df = sample_data.copy()
    df_date1 = df[df['date'].dt.to_period('M') == date1.to_period('M')]
    df_date2 = df[df['date'].dt.to_period('M') == date2.to_period('M')]
    
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
    
    def create_comparison_chart(df1, df2, variable, var_label):
        fig, date_labels = go.Figure(), [date1.strftime('%Y-%m'), date2.strftime('%Y-%m')]
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
    
    def create_division_stacked_chart(df1, df2, variable, var_label):
        if 'Division' not in df1.columns or 'Division' not in df2.columns:
            fig = go.Figure()
            fig.add_annotation(text="Division data not available", xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle', showarrow=False)
            fig.update_layout(title=f"{var_label} by Division", template="plotly_white", height=350)
            return fig
        
        fig = go.Figure()
        date_labels = [date1.strftime('%Y-%m'), date2.strftime('%Y-%m')]
        
        div1 = df1.groupby('Division')[variable].sum()
        total1 = div1.sum()
        pct1 = (div1 / total1 * 100) if total1 > 0 else pd.Series(dtype=float)
        
        div2 = df2.groupby('Division')[variable].sum()
        total2 = div2.sum()
        pct2 = (div2 / total2 * 100) if total2 > 0 else pd.Series(dtype=float)
        
        all_divisions = set()
        if not pct1.empty: all_divisions.update(pct1.index)
        if not pct2.empty: all_divisions.update(pct2.index)
        
        sorted_divisions = sorted(all_divisions)
        colors = get_color_sequence('stacked', len(sorted_divisions))
        for i, division in enumerate(sorted_divisions):
            p1, p2 = pct1.get(division, 0), pct2.get(division, 0)
            fig.add_trace(go.Bar(x=date_labels, y=[p1, p2], name=division,
                marker_color=colors[i],
                text=[f"{p1:.1f}%", f"{p2:.1f}%"], textposition='inside',
                hovertemplate='<b>%{x}</b><br>' + f'{division}<br>' + 'Percentage: %{y:.1f}%<extra></extra>'))
        
        fig.update_layout(title=f"{var_label} Percentage Contribution by Division - {selected_type}",
            xaxis_title="Month", yaxis_title="Percentage (%)", barmode='stack', template="plotly_white",
            height=350, showlegend=True, yaxis=dict(range=[0, 100]))
        return fig
    
    amount_chart = create_comparison_chart(df_date1, df_date2, amount_col, "Amount")
    income_chart = create_comparison_chart(df_date1, df_date2, income_col, "Income")
    amount_dumbbell = create_dumbbell_chart_updated(df_date1, df_date2, amount_col, date1, date2, group_var, selected_type, "Amount")
    income_dumbbell = create_dumbbell_chart_updated(df_date1, df_date2, income_col, date1, date2, group_var, selected_type, "Income")
    amount_division = create_division_stacked_chart(df_date1, df_date2, amount_col, "Amount")
    income_division = create_division_stacked_chart(df_date1, df_date2, income_col, "Income")
    
    return value_boxes, amount_chart, income_chart, amount_dumbbell, income_dumbbell, amount_division, income_division, comparison_text

@callback(Output("download-dataframe-xlsx", "data"), Input("export-excel-btn", "n_clicks"),
    [State("comparison-type-selector", "value"), State("comparison-date-selector", "value"),
     State("comparison-filter-selector", "value"), State("comparison-filter-values-selector", "value"),
     State("comparison-group-selector", "value"), State("comparison-stack-selector", "value")], prevent_initial_call=True)
def export_comparison_excel(n_clicks, selected_type, selected_dates, filter_var, filter_values, group_var, stack_var):
    """Export all comparison chart data to multi-sheet Excel"""
    if n_clicks and selected_dates and len(selected_dates) == 2:
        import io
        date1, date2 = sorted([pd.to_datetime(date + '-01') for date in selected_dates])
        df = sample_data.copy()
        
        # Filter by dates
        df_date1 = df[df['date'].dt.to_period('M') == date1.to_period('M')].copy()
        df_date2 = df[df['date'].dt.to_period('M') == date2.to_period('M')].copy()
        
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
            
            # Sheet 2: Division breakdown if available
            if 'Division' in df.columns:
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
            
            # Sheet 3: Tool sample data if available
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


@callback(Output("download-history-data", "data"), Input("history-export-btn", "n_clicks"),
    [State("variable-selector", "value"), State("year-range-slider", "value"),
     State("filter-selector", "value"), State("filter-values-selector", "value"),
     State("stack-selector", "value"), State("group-selector", "value")], prevent_initial_call=True)
def export_history_data(n_clicks, selected_type, year_range, filter_var, filter_values, stack_var, group_var):
    """Export all History tab chart data to multi-sheet Excel"""
    if n_clicks:
        import io
        df = sample_data.copy()
        
        # Apply filters
        df = df[(df['date'].dt.year >= year_range[0]) & (df['date'].dt.year <= year_range[1])]
        if filter_var != "none" and filter_var in df.columns and filter_values:
            df = df[df[filter_var].isin(filter_values)]
        
        amount_col = f'Amount_{selected_type}' if selected_type != 'Total' else 'Amount_total'
        income_col = f'Income_{selected_type}' if selected_type != 'Total' else 'Income_total'
        
        # Create Excel with multiple sheets
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Sheet 1: Amount chart data
            amount_data = df.groupby(df['date'].dt.to_period('M'))[amount_col].sum().reset_index()
            amount_data.columns = ['Month', 'Amount']
            amount_data['Month'] = amount_data['Month'].astype(str)
            amount_data.to_excel(writer, sheet_name='Amount Chart', index=False)
            
            # Sheet 2: Income chart data
            income_data = df.groupby(df['date'].dt.to_period('M'))[income_col].sum().reset_index()
            income_data.columns = ['Month', 'Income']
            income_data['Month'] = income_data['Month'].astype(str)
            income_data.to_excel(writer, sheet_name='Income Chart', index=False)
            
            # Sheet 3: Ratio chart data
            ratio_data = df.groupby(df['date'].dt.to_period('M')).agg({amount_col: 'sum', income_col: 'sum'}).reset_index()
            ratio_data['Ratio'] = (ratio_data[income_col] / ratio_data[amount_col].replace(0, np.nan)) * 100
            ratio_data.columns = ['Month', 'Amount', 'Income', 'Ratio (%)']
            ratio_data['Month'] = ratio_data['Month'].astype(str)
            ratio_data.to_excel(writer, sheet_name='Ratio Chart', index=False)
            
        
        output.seek(0)
        return dcc.send_bytes(output.getvalue(), f"history_data_{selected_type}_{datetime.now().strftime('%Y%m%d')}.xlsx")

@callback(Output("download-tool-data", "data"), Input("tool-export-btn", "n_clicks"),
    [State("tool-division-filter", "value"), State("tool-item-filter", "value"),
     State("tool-function-filter", "value"), State("tool-year-range-slider", "value")], prevent_initial_call=True)
def export_tool_data(n_clicks, division_filter, item_filter, function_filter, year_range):
    """Export Tool tab data to multi-sheet Excel"""
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


@callback(Output("save-analysis-btn", "children"), Input("save-analysis-btn", "n_clicks"), 
    State("analysis-textbox", "value"), prevent_initial_call=True)
def save_analysis(n_clicks, analysis_text):
    return "Analysis Saved!" if n_clicks else "Save Analysis"

@callback(Output("save-comparison-btn", "children"), Input("save-comparison-btn", "n_clicks"), 
    State("comparison-textbox", "value"), prevent_initial_call=True)
def save_comparison(n_clicks, comparison_text):
    return "Comparison Saved!" if n_clicks else "Save Comparison"

@callback(
    Output("tool-income-chart", "figure"),
    [Input("tool-division-filter", "value"), Input("tool-item-filter", "value"), 
     Input("tool-function-filter", "value"), Input("tool-year-range-slider", "value")]
)
def update_tool_chart(division_filter, item_filter, function_filter, year_range):
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
    
    fig.add_trace(go.Bar(
        x=merged['month'],
        y=merged['Income_total'],
        name='Income Total (Original)',
        marker_color='#718096',  # Gray medium for baseline
        text=[format_number(v) for v in merged['Income_total']],
        textposition='inside',
        customdata=[format_hover_value(v) for v in merged['Income_total']],
        hovertemplate='<b>%{x}</b><br>Income Total (Original)<br>Value: %{customdata}<extra></extra>'
    ))
    
    fig.add_trace(go.Bar(
        x=merged['month'],
        y=merged['Income_corr'],
        name='Income Correction',
        marker_color='#E53E3E',  # Red for emphasis
        text=[format_number(v) for v in merged['Income_corr']],
        textposition='inside',
        customdata=[format_hover_value(v) for v in merged['Income_corr']],
        hovertemplate='<b>%{x}</b><br>Income Correction<br>Value: %{customdata}<extra></extra>'
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

# ============================================================================
# RUN APP
# ============================================================================
if __name__ == "__main__":
    app.run(debug=True)