# Function to generate enhanced comparison text with proportion analysis - updated for new data structure
def generate_enhanced_comparison_text_updated(amount_old, amount_new, income_old, income_new, date1, date2, 
                                            filter_var, filter_values, group_var, df1, df2):
    """Generate comprehensive comparison analysis text including proportion changes"""
    
    # Helper function to determine change type and generate sentence
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
    
    # Build the text
    text_parts = []
    
    # Add filter information if applied
    if filter_var != "none" and filter_values:
        filter_text = f"Analysis filtered by {filter_var}: {', '.join(filter_values)}.\n\n"
        text_parts.append(filter_text)
    
    # Add comparison header
    text_parts.append("COMPARISON ANALYSIS:\n")
    text_parts.append("=" * 30 + "\n\n")
    
    # Generate sentences for Amount and Income
    amount_sentence = create_change_sentence("Amount Total", amount_old, amount_new, date1, date2)
    income_sentence = create_change_sentence("Income Total", income_old, income_new, date1, date2)
    
    text_parts.append(amount_sentence + "\n\n")
    text_parts.append(income_sentence + "\n\n")
    
    # Add ratio analysis
    ratio_old = (amount_old / income_old) if income_old != 0 else 0
    ratio_new = (amount_new / income_new) if income_new != 0 else 0
    ratio_change = ratio_new - ratio_old
    
    if abs(ratio_change) < 0.01:
        ratio_text = f"The Amount/Income ratio remained stable at approximately {ratio_old:.2f}."
    elif ratio_change > 0:
        ratio_text = f"The Amount/Income ratio improved from {ratio_old:.2f} to {ratio_new:.2f}, representing an increase of {ratio_change:.2f}."
    else:
        ratio_text = f"The Amount/Income ratio declined from {ratio_old:.2f} to {ratio_new:.2f}, representing a decrease of {abs(ratio_change):.2f}."
    
    text_parts.append(ratio_text + "\n\n")
    
    # Add proportion analysis if grouping is selected
    if group_var != "none" and group_var in ['Division', 'Type', 'Item', 'Function'] and not df1.empty and not df2.empty:
        text_parts.append("PROPORTION ANALYSIS BY GROUPS:\n")
        text_parts.append("=" * 30 + "\n\n")
        
        # Analyze Amount proportions
        amount_groups1 = df1.groupby(group_var)['Amount_total'].sum()
        amount_total1 = df1['Amount_total'].sum()
        amount_props1 = (amount_groups1 / amount_total1 * 100) if amount_total1 > 0 else pd.Series(dtype=float)
        
        amount_groups2 = df2.groupby(group_var)['Amount_total'].sum()
        amount_total2 = df2['Amount_total'].sum()
        amount_props2 = (amount_groups2 / amount_total2 * 100) if amount_total2 > 0 else pd.Series(dtype=float)
        
        text_parts.append("Amount Total Proportion Changes:\n")
        all_groups = set(amount_props1.index) | set(amount_props2.index)
        for group in sorted(all_groups):
            prop1 = amount_props1.get(group, 0)
            prop2 = amount_props2.get(group, 0)
            amount1 = amount_groups1.get(group, 0)
            amount2 = amount_groups2.get(group, 0)
            prop_change = prop2 - prop1
            
            change_desc = "increased" if prop_change > 0 else "decreased" if prop_change < 0 else "remained stable"
            text_parts.append(f"• {group}: {prop1:.1f}% → {prop2:.1f}% ({change_desc} by {abs(prop_change):.1f}pp), amounts: {amount1:.1f} → {amount2:.1f}\n")
        
        text_parts.append("\n")
        
        # Analyze Income proportions
        income_groups1 = df1.groupby(group_var)['Income_total'].sum()
        income_total1 = df1['Income_total'].sum()
        income_props1 = (income_groups1 / income_total1 * 100) if income_total1 > 0 else pd.Series(dtype=float)
        
        income_groups2 = df2.groupby(group_var)['Income_total'].sum()
        income_total2 = df2['Income_total'].sum()
        income_props2 = (income_groups2 / income_total2 * 100) if income_total2 > 0 else pd.Series(dtype=float)
        
        text_parts.append("Income Total Proportion Changes:\n")
        all_groups = set(income_props1.index) | set(income_props2.index)
        for group in sorted(all_groups):
            prop1 = income_props1.get(group, 0)
            prop2 = income_props2.get(group, 0)
            amount1 = income_groups1.get(group, 0)
            amount2 = income_groups2.get(group, 0)
            prop_change = prop2 - prop1
            
            change_desc = "increased" if prop_change > 0 else "decreased" if prop_change < 0 else "remained stable"
            text_parts.append(f"• {group}: {prop1:.1f}% → {prop2:.1f}% ({change_desc} by {abs(prop_change):.1f}pp), amounts: {amount1:.1f} → {amount2:.1f}\n")
        
        text_parts.append("\n")
    
    # Add summary section
    text_parts.append("SUMMARY:\n")
    text_parts.append("=" * 30 + "\n")
    text_parts.append("• [Add your key insights here]\n")
    text_parts.append("• [Note any significant patterns]\n")
    text_parts.append("• [Record actionable findings]")
    
    return "".join(text_parts)# Callback for the amount vs income chart
@callback(
    Output("amount-income-chart", "figure"),
    [Input("year-range-slider", "value"),
     Input("filter-selector", "value"),
     Input("filter-values-selector", "value"),
     Input("group-selector", "value")]
)
def update_amount_income_chart(year_range, filter_var, filter_values, group_var):
    # Create a copy of the data for processing
    df = sample_data.copy()
    
    # Filter by year range
    df = df[(df['date'].dt.year >= year_range[0]) & (df['date'].dt.year <= year_range[1])]
    
    # Apply filtering if selected
    if filter_var != "none" and filter_var in df.columns and filter_values:
        df = df[df[filter_var].isin(filter_values)]
    
    # Prepare data for plotting
    df['month'] = df['date'].dt.to_period('M').astype(str)
    
    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    if group_var != "none" and group_var in df.columns:
        # Create grouped line chart
        if group_var in ['Division', 'Type', 'Item', 'Function']:
            for category in sorted(df[group_var].unique()):
                category_data = df[df[group_var] == category]
                monthly_data = category_data.groupby('month').agg({
                    'Amount_total': 'sum',
                    'Income_total': 'sum'
                }).reset_index()
                
                # Add Amount traces
                fig.add_trace(
                    go.Scatter(
                        x=monthly_data['month'],
                        y=monthly_data['Amount_total'],
                        mode='lines+markers',
                        name=f"Amount - {category}",
                        line=dict(width=2, dash='solid'),
                        marker=dict(size=6)
                    ),
                    secondary_y=False
                )
                
                # Add Income traces
                fig.add_trace(
                    go.Scatter(
                        x=monthly_data['month'],
                        y=monthly_data['Income_total'],
                        mode='lines+markers',
                        name=f"Income - {category}",
                        line=dict(width=2, dash='dash'),
                        marker=dict(size=6, symbol='diamond')
                    ),
                    secondary_y=True
                )
    else:
        # Create simple line chart
        monthly_data = df.groupby('month').agg({
            'Amount_total': 'sum',
            'Income_total': 'sum'
        }).reset_index()
        
        fig.add_trace(
            go.Scatter(
                x=monthly_data['month'],
                y=monthly_data['Amount_total'],
                mode='lines+markers',
                name='Amount Total',
                line=dict(color='#1f77b4', width=3),
                marker=dict(size=8)
            ),
            secondary_y=False
        )
        
        fig.add_trace(
            go.Scatter(
                x=monthly_data['month'],
                y=monthly_data['Income_total'],
                mode='lines+markers',
                name='Income Total',
                line=dict(color='#ff7f0e', width=3),
                marker=dict(size=8, symbol='diamond')
            ),
            secondary_y=True
        )
    
    # Update axes labels
    fig.update_xaxes(title_text="Month", tickangle=45)
    fig.update_yaxes(title_text="Amount Total", secondary_y=False)
    fig.update_yaxes(title_text="Income Total", secondary_y=True)
    
    # Update layout
    fig.update_layout(
        title="Amount vs Income Trends",
        template="plotly_white",
        height=300,
        margin=dict(l=50, r=50, t=40, b=50),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
    )
    
    return figimport dash
from dash import dcc, html, Input, Output, callback, State
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Initialize the Dash app
app = dash.Dash(__name__)

# Load data from CSV file
try:
    sample_data = pd.read_csv('Example_df.csv')
    
    # Convert Date column to proper datetime format (from "2020-03" to datetime)
    sample_data['Date'] = pd.to_datetime(sample_data['Date'], format='%Y-%m')
    sample_data = sample_data.rename(columns={'Date': 'date'})  # Keep lowercase for consistency
    
    # Sort by date for better visualization
    sample_data = sample_data.sort_values('date').reset_index(drop=True)
    
    print(f"Successfully loaded {len(sample_data)} records from Example_df.csv")
    print(f"Date range: {sample_data['date'].min()} to {sample_data['date'].max()}")
    
except FileNotFoundError:
    print("Example_df.csv not found. Creating sample data for demonstration.")
    # Fallback sample data with similar structure
    np.random.seed(42)
    date_range = pd.date_range(start='2020-01-01', end='2024-12-31', freq='M')
    n_records = len(date_range) * 10
    
    sample_dates = np.random.choice(date_range, n_records, replace=True)
    sample_data = pd.DataFrame({
        'date': sample_dates,
        'Division': np.random.choice(['North', 'South', 'East', 'West'], n_records),
        'Type': np.random.choice(['Type A', 'Type B', 'Type C'], n_records),
        'Item': np.random.choice(['Item 1', 'Item 2', 'Item 3', 'Item 4'], n_records),
        'Function': np.random.choice(['Sales', 'Marketing', 'Operations', 'Support'], n_records),
        'Amount_total': np.random.normal(1000, 200, n_records),
        'Amount_1': np.random.normal(300, 50, n_records),
        'Amount_2': np.random.normal(400, 60, n_records),
        'Amount_3': np.random.normal(300, 40, n_records),
        'Income_total': np.random.normal(1200, 250, n_records),
        'Income_1': np.random.normal(400, 80, n_records),
        'Income_2': np.random.normal(500, 90, n_records),
        'Income_3': np.random.normal(300, 50, n_records),
    })
    sample_data = sample_data.sort_values('date').reset_index(drop=True)

# Get the year range for the slider
min_year = sample_data['date'].dt.year.min()
max_year = sample_data['date'].dt.year.max()

# Create year range marks for the slider
year_marks = {year: {'label': str(year)} for year in range(min_year, max_year + 1)}

# Define the app layout with AppShell
app.layout = dmc.MantineProvider(
    theme={
        "colorScheme": "light",
        "primaryColor": "blue",
    },
    children=[
        dmc.AppShell(
            id="app-shell",
            header={"height": 60},
            navbar={"width": 250, "breakpoint": "sm"},
            padding="md",
            children=[
                # Header
                dmc.AppShellHeader(
                    px="md",
                    children=[
                        dmc.Group(
                            justify="space-between",
                            h="100%",
                            children=[
                                dmc.Title("Dashboard", order=3, c="blue"),
                                dmc.Text(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", size="sm", c="dimmed"),
                            ],
                        )
                    ],
                ),
                
                # Navbar
                dmc.AppShellNavbar(
                    p="md",
                    children=[
                        dmc.Title("Navigation", order=4, mb="md"),
                        dmc.NavLink(
                            label="Today",
                            id="nav-today",
                            leftSection=DashIconify(icon="material-symbols:today", width=20),
                            active=True,
                        ),
                        dmc.NavLink(
                            label="Scenario",
                            id="nav-scenario",
                            leftSection=DashIconify(icon="material-symbols:analytics", width=20),
                        ),
                    ],
                ),
                
                # Main content
                dmc.AppShellMain(
                    id="main-content",
                    children=[
                        # Today page content
                        html.Div(
                            id="today-content",
                            children=[
                                dmc.Tabs(
                                    value="history",
                                    children=[
                                        dmc.TabsList([
                                            dmc.TabsTab("History", value="history"),
                                            dmc.TabsTab("Comparison", value="comparison"),
                                            dmc.TabsTab("Tool", value="tool"),
                                        ]),
                                        
                                        # History Tab
                                        dmc.TabsPanel(
                                            value="history",
                                            children=[
                                                dmc.Grid([
                                                    # Chart controls and visualization (left side)
                                                    dmc.GridCol(
                                                        span=8,
                                                        children=[
                                                            dmc.Card([
                                                                dmc.CardSection([
                                                                    dmc.Title("Chart Controls", order=4, mb="md"),
                                                                    
                                                                    # First row: Display Variable (SegmentedControl) and Year Range
                                                                    dmc.Group([
                                                                        # Display Variable - SegmentedControl vertical with color
                                                                        dmc.Stack([
                                                                            dmc.Text("Display Variable:", size="sm", fw=500, mb=5),
                                                                            dmc.SegmentedControl(
                                                                                id="variable-selector",
                                                                                value="Amount_total",
                                                                                orientation="vertical",
                                                                                fullWidth=False,
                                                                                color="blue",
                                                                                data=[
                                                                                    {"value": "Amount_total", "label": "Amount Total"},
                                                                                    {"value": "Income_total", "label": "Income Total"},
                                                                                    {"value": "Amount_1", "label": "Amount 1"},
                                                                                    {"value": "Amount_2", "label": "Amount 2"},
                                                                                    {"value": "Amount_3", "label": "Amount 3"},
                                                                                    {"value": "Income_1", "label": "Income 1"},
                                                                                    {"value": "Income_2", "label": "Income 2"},
                                                                                    {"value": "Income_3", "label": "Income 3"},
                                                                                ],
                                                                                size="sm",
                                                                                style={"width": "140px"}
                                                                            ),
                                                                        ], gap="xs", align="flex-start"),
                                                                        
                                                                        # Year Range - takes remaining horizontal space
                                                                        dmc.Stack([
                                                                            dmc.Text("Year Range:", size="sm", fw=500, mb=5),
                                                                            html.Div([
                                                                                dcc.RangeSlider(
                                                                                    id="year-range-slider",
                                                                                    min=min_year,
                                                                                    max=max_year,
                                                                                    step=1,
                                                                                    value=[min_year, max_year],
                                                                                    marks=year_marks,
                                                                                    tooltip={"placement": "bottom", "always_visible": True}
                                                                                ),
                                                                            ], style={"width": "100%", "padding": "10px 20px"})
                                                                        ], gap="xs", style={"flex": 1}),
                                                                    ], justify="space-between", align="flex-start", mb="lg"),
                                                                    
                                                                    # Second row: Filter by, Stack by, Group by
                                                                    dmc.Grid([
                                                                        dmc.GridCol(
                                                                            span=4,
                                                                            children=[
                                                                                dmc.Text("Filter by:", size="sm", fw=500, mb=5),
                                                                                dmc.Select(
                                                                                    id="filter-selector",
                                                                                    placeholder="Select filter",
                                                                                    data=[
                                                                                        {"value": "none", "label": "No Filter"},
                                                                                        {"value": "Division", "label": "Division"},
                                                                                        {"value": "Type", "label": "Type"},
                                                                                        {"value": "Item", "label": "Item"},
                                                                                        {"value": "Function", "label": "Function"},
                                                                                    ],
                                                                                    value="none",
                                                                                    size="sm",
                                                                                ),
                                                                            ]
                                                                        ),
                                                                        
                                                                        dmc.GridCol(
                                                                            span=4,
                                                                            children=[
                                                                                dmc.Text("Stack by:", size="sm", fw=500, mb=5),
                                                                                dmc.Select(
                                                                                    id="stack-selector",
                                                                                    placeholder="Select stack variable",
                                                                                    data=[
                                                                                        {"value": "none", "label": "No Stack"},
                                                                                        {"value": "Division", "label": "Division"},
                                                                                        {"value": "Type", "label": "Type"},
                                                                                        {"value": "Item", "label": "Item"},
                                                                                        {"value": "Function", "label": "Function"},
                                                                                    ],
                                                                                    value="none",
                                                                                    size="sm",
                                                                                ),
                                                                            ]
                                                                        ),
                                                                        
                                                                        dmc.GridCol(
                                                                            span=4,
                                                                            children=[
                                                                                dmc.Text("Group by:", size="sm", fw=500, mb=5),
                                                                                dmc.Select(
                                                                                    id="group-selector",
                                                                                    placeholder="Select group variable",
                                                                                    data=[
                                                                                        {"value": "none", "label": "No Grouping"},
                                                                                        {"value": "Division", "label": "Division"},
                                                                                        {"value": "Type", "label": "Type"},
                                                                                        {"value": "Item", "label": "Item"},
                                                                                        {"value": "Function", "label": "Function"},
                                                                                    ],
                                                                                    value="none",
                                                                                    size="sm",
                                                                                ),
                                                                            ]
                                                                        ),
                                                                    ], gutter="md", mb="lg"),
                                                                    
                                                                    # Third row: Filter values (MultiSelect)
                                                                    html.Div([
                                                                        dmc.Text("Filter values:", size="sm", fw=500, mb=5),
                                                                        dmc.MultiSelect(
                                                                            id="filter-values-selector",
                                                                            placeholder="Select values",
                                                                            data=[],
                                                                            value=[],
                                                                            size="sm",
                                                                            disabled=True,
                                                                        ),
                                                                    ], style={"width": "100%"}),
                                                                    
                                                                ], withBorder=True, inheritPadding=True, py="md"),
                                                                
                                                                dmc.CardSection([
                                                                    dcc.Graph(
                                                                        id="main-barchart",
                                                                        style={"height": "400px"}
                                                                    )
                                                                ], inheritPadding=True, pt="xs"),
                                                                
                                                                dmc.CardSection([
                                                                    dmc.Title("Amount vs Income Trends", order=5, mb="sm"),
                                                                    dcc.Graph(
                                                                        id="amount-income-chart",
                                                                        style={"height": "300px"}
                                                                    )
                                                                ], inheritPadding=True, pt="xs"),
                                                            ], withBorder=True, shadow="sm", radius="md", mb="md")
                                                        ]
                                                    ),
                                                    
                                                    # Text box (right side)
                                                    dmc.GridCol(
                                                        span=4,
                                                        children=[
                                                            dmc.Card([
                                                                dmc.CardSection([
                                                                    dmc.Title("Analysis Notes", order=4, mb="md"),
                                                                    dmc.Textarea(
                                                                        id="analysis-textbox",
                                                                        placeholder="Enter your analysis notes here...",
                                                                        autosize=True,
                                                                        minRows=15,
                                                                        maxRows=20,
                                                                        value="Chart Analysis:\n\n• Use the controls on the left to modify the visualization\n• Switch between Var1 and Var2 for different metrics\n• Apply filters to focus on specific data subsets\n• Use stacking to show composition\n• Group data for comparative analysis\n\nKey Insights:\n• [Add your observations here]\n• [Identify trends and patterns]\n• [Note any anomalies or interesting findings]"
                                                                    ),
                                                                ], withBorder=True, inheritPadding=True, py="xs"),
                                                                
                                                                dmc.CardSection([
                                                                    dmc.Button(
                                                                        "Save Analysis",
                                                                        id="save-analysis-btn",
                                                                        variant="filled",
                                                                        size="sm",
                                                                        fullWidth=True
                                                                    )
                                                                ], inheritPadding=True, pt="xs")
                                                            ], withBorder=True, shadow="sm", radius="md", h="100%")
                                                        ]
                                                    )
                                                ], gutter="md")
                                            ]
                                        ),
                                        
                                        # Comparison Tab - New Layout
                                        dmc.TabsPanel(
                                            value="comparison",
                                            children=[
                                                dmc.Stack([
                                                    # Comparison Controls Card - Top
                                                    dmc.Card([
                                                        dmc.CardSection([
                                                            dmc.Title("Comparison Controls", order=4, mb="md"),
                                                            
                                                            # First row: Date Selection
                                                            dmc.Group([
                                                                # Date Selection - MultiSelect with calendar icon
                                                                dmc.Stack([
                                                                    dmc.Text("Select Dates for Comparison:", size="sm", fw=500, mb=5),
                                                                    dmc.MultiSelect(
                                                                        id="comparison-date-selector",
                                                                        placeholder="Select exactly 2 dates to compare",
                                                                        data=[],  # Will be populated by callback
                                                                        value=[],
                                                                        maxValues=2,
                                                                        size="sm",
                                                                        searchable=True,
                                                                        clearable=True,
                                                                        leftSection=DashIconify(icon="material-symbols:calendar-month", width=20),
                                                                        styles={
                                                                            "dropdown": {"maxHeight": "200px", "overflowY": "auto"},
                                                                            "input": {"minWidth": "300px"}
                                                                        }
                                                                    ),
                                                                ], gap="xs", style={"flex": 1}),
                                                            ], justify="flex-start", align="flex-start", mb="lg"),
                                                            
                                                            # Second row: Filter by, Stack by, Group by (modified)
                                                            dmc.Grid([
                                                                dmc.GridCol(
                                                                    span=4,
                                                                    children=[
                                                                        dmc.Text("Filter by:", size="sm", fw=500, mb=5),
                                                                        dmc.Select(
                                                                            id="comparison-filter-selector",
                                                                            placeholder="Select filter",
                                                                            data=[
                                                                                {"value": "none", "label": "No Filter"},
                                                                                {"value": "Division", "label": "Division"},
                                                                                {"value": "Type", "label": "Type"},
                                                                                {"value": "Item", "label": "Item"},
                                                                                {"value": "Function", "label": "Function"},
                                                                            ],
                                                                            value="none",
                                                                            size="sm",
                                                                        ),
                                                                    ]
                                                                ),
                                                                
                                                                dmc.GridCol(
                                                                    span=4,
                                                                    children=[
                                                                        dmc.Text("Stack by:", size="sm", fw=500, mb=5),
                                                                        dmc.Select(
                                                                            id="comparison-stack-selector",
                                                                            placeholder="Select stack variable",
                                                                            data=[
                                                                                {"value": "none", "label": "No Stack"},
                                                                                {"value": "Division", "label": "Division"},
                                                                                {"value": "Type", "label": "Type"},
                                                                                {"value": "Item", "label": "Item"},
                                                                                {"value": "Function", "label": "Function"},
                                                                            ],
                                                                            value="none",
                                                                            size="sm",
                                                                        ),
                                                                    ]
                                                                ),
                                                                
                                                                dmc.GridCol(
                                                                    span=4,
                                                                    children=[
                                                                        dmc.Text("Group by:", size="sm", fw=500, mb=5),
                                                                        dmc.Select(
                                                                            id="comparison-group-selector",
                                                                            placeholder="Select group variable",
                                                                            data=[
                                                                                {"value": "none", "label": "No Grouping"},
                                                                                {"value": "Division", "label": "Division"},
                                                                                {"value": "Type", "label": "Type"},
                                                                                {"value": "Item", "label": "Item"},
                                                                                {"value": "Function", "label": "Function"},
                                                                            ],
                                                                            value="none",
                                                                            size="sm",
                                                                        ),
                                                                    ]
                                                                ),
                                                            ], gutter="md", mb="lg"),
                                                            
                                                            # Third row: Filter values (MultiSelect)
                                                            html.Div([
                                                                dmc.Text("Filter values:", size="sm", fw=500, mb=5),
                                                                dmc.MultiSelect(
                                                                    id="comparison-filter-values-selector",
                                                                    placeholder="Select values",
                                                                    data=[],
                                                                    value=[],
                                                                    size="sm",
                                                                    disabled=True,
                                                                ),
                                                            ], style={"width": "100%"}),
                                                            
                                                        ], withBorder=True, inheritPadding=True, py="md"),
                                                    ], withBorder=True, shadow="sm", radius="md", mb="md"),
                                                    
                                                    # Comparison Notes Box
                                                    dmc.Card([
                                                        dmc.CardSection([
                                                            dmc.Title("Comparison Notes", order=4, mb="md"),
                                                            dmc.Textarea(
                                                                id="comparison-textbox",
                                                                placeholder="Enter your comparison analysis notes here...",
                                                                autosize=True,
                                                                minRows=8,
                                                                maxRows=15,
                                                                value="Comparison Analysis:\n\n• Select exactly 2 dates to compare data\n• Use filters and grouping to focus analysis\n• Monitor value changes and ratios\n• Identify significant trends between periods\n\nKey Observations:\n• [Record changes in Var1 and Var2]\n• [Note ratio changes and their implications]\n• [Highlight significant variations]\n• [Document insights for decision making]"
                                                            ),
                                                        ], withBorder=True, inheritPadding=True, py="xs"),
                                                        
                                                        dmc.CardSection([
                                                            dmc.Button(
                                                                "Save Comparison",
                                                                id="save-comparison-btn",
                                                                variant="filled",
                                                                size="sm",
                                                                fullWidth=True
                                                            )
                                                        ], inheritPadding=True, pt="xs")
                                                    ], withBorder=True, shadow="sm", radius="md", mb="md"),
                                                    
                                                    # Comparison Metrics and Charts
                                                    dmc.Card([
                                                        # Value Boxes for Comparison Metrics
                                                        dmc.CardSection([
                                                            dmc.Title("Comparison Metrics", order=5, mb="sm"),
                                                            html.Div(id="comparison-value-boxes")
                                                        ], inheritPadding=True, pt="xs"),
                                                        
                                                        # Comparison Charts
                                                        dmc.CardSection([
                                                            dmc.Grid([
                                                                dmc.GridCol([
                                                                    dmc.Title("Amount Total Comparison", order=5, mb="sm"),
                                                                    dcc.Graph(
                                                                        id="comparison-var1-chart",
                                                                        style={"height": "300px"}
                                                                    )
                                                                ], span=6),
                                                                dmc.GridCol([
                                                                    dmc.Title("Income Total Comparison", order=5, mb="sm"),
                                                                    dcc.Graph(
                                                                        id="comparison-var2-chart",
                                                                        style={"height": "300px"}
                                                                    )
                                                                ], span=6),
                                                            ], gutter="md")
                                                        ], inheritPadding=True, pt="xs"),
                                                        
                                                        # Dumbbell Charts Section
                                                        dmc.CardSection([
                                                            dmc.Title("Proportion Changes Analysis", order=5, mb="sm"),
                                                            dmc.Grid([
                                                                dmc.GridCol([
                                                                    dmc.Title("Amount Total Proportion Changes", order=6, mb="sm"),
                                                                    dcc.Graph(
                                                                        id="var1-dumbbell-chart",
                                                                        style={"height": "350px"}
                                                                    )
                                                                ], span=6),
                                                                dmc.GridCol([
                                                                    dmc.Title("Income Total Proportion Changes", order=6, mb="sm"),
                                                                    dcc.Graph(
                                                                        id="var2-dumbbell-chart",
                                                                        style={"height": "350px"}
                                                                    )
                                                                ], span=6),
                                                            ], gutter="md")
                                                        ], inheritPadding=True, pt="xs"),
                                                    ], withBorder=True, shadow="sm", radius="md")
                                                ], gap="md")
                                            ]
                                        ),
                                        
                                        dmc.TabsPanel(
                                            value="tool",
                                            children=[
                                                dmc.Center([
                                                    dmc.Stack([
                                                        dmc.Title("Tool Tab", order=2),
                                                        dmc.Text("This tab is ready for tool features implementation.", c="dimmed"),
                                                    ], align="center")
                                                ], style={"height": "400px"})
                                            ]
                                        ),
                                    ],
                                    id="main-tabs"
                                )
                            ],
                            style={"display": "block"}
                        ),
                        
                        # Scenario page content (placeholder)
                        html.Div(
                            id="scenario-content",
                            children=[
                                dmc.Center([
                                    dmc.Stack([
                                        dmc.Title("Scenario Page", order=2),
                                        dmc.Text("This page is ready for scenario analysis implementation.", c="dimmed"),
                                    ], align="center")
                                ], style={"height": "400px"})
                            ],
                            style={"display": "none"}
                        )
                    ]
                ),
            ],
        )
    ]
)

# Updated function to create dumbbell charts for new data structure
def create_dumbbell_chart_updated(df1, df2, variable, date1, date2, group_var):
    """Create a dumbbell chart showing proportion changes between two dates - updated for new data structure"""
    if group_var == "none":
        fig = go.Figure()
        fig.add_annotation(
            text="Select a grouping variable to see proportion analysis",
            xref="paper", yref="paper", x=0.5, y=0.5,
            xanchor='center', yanchor='middle', showarrow=False,
            font=dict(size=14, color="gray")
        )
        fig.update_layout(
            title=f"{variable.replace('_', ' ').title()} Proportions",
            template="plotly_white",
            height=350
        )
        return fig
    
    # Calculate totals for each group at each date
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
    
    # Get all unique groups
    all_groups = set()
    if not proportions1.empty:
        all_groups.update(proportions1.index)
    if not proportions2.empty:
        all_groups.update(proportions2.index)
    
    if not all_groups:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available for selected dates and grouping",
            xref="paper", yref="paper", x=0.5, y=0.5,
            xanchor='center', yanchor='middle', showarrow=False,
            font=dict(size=14, color="gray")
        )
        fig.update_layout(
            title=f"{variable.replace('_', ' ').title()} Proportions by {group_var}",
            template="plotly_white",
            height=350
        )
        return fig
    
    fig = go.Figure()
    
    # Create dumbbell chart
    for i, group in enumerate(sorted(all_groups)):
        prop1 = proportions1.get(group, 0)
        prop2 = proportions2.get(group, 0)
        val1 = group1_data.get(group, 0)
        val2 = group2_data.get(group, 0)
        
        # Calculate circle sizes based on actual values (scaled)
        max_val = max(val1, val2) if max(val1, val2) > 0 else 1
        size1 = max(10, min(30, (val1 / max_val) * 25 + 5))
        size2 = max(10, min(30, (val2 / max_val) * 25 + 5))
        
        y_pos = i
        
        # Add connecting line
        fig.add_trace(go.Scatter(
            x=[prop1, prop2],
            y=[y_pos, y_pos],
            mode='lines',
            line=dict(color='gray', width=2),
            showlegend=False,
            hoverinfo='skip'
        ))
        
        # Add circles for date 1
        fig.add_trace(go.Scatter(
            x=[prop1],
            y=[y_pos],
            mode='markers',
            marker=dict(
                size=size1,
                color='lightblue',
                line=dict(width=2, color='blue')
            ),
            name=f"{date1.strftime('%Y-%m')}",
            legendgroup="date1",
            showlegend=(i == 0),
            hovertemplate=f"<b>{group}</b><br>" +
                         f"Month: {date1.strftime('%Y-%m')}<br>" +
                         f"Proportion: {prop1:.1f}%<br>" +
                         f"Amount: {val1:.1f}<extra></extra>"
        ))
        
        # Add circles for date 2
        fig.add_trace(go.Scatter(
            x=[prop2],
            y=[y_pos],
            mode='markers',
            marker=dict(
                size=size2,
                color='lightcoral',
                line=dict(width=2, color='red')
            ),
            name=f"{date2.strftime('%Y-%m')}",
            legendgroup="date2",
            showlegend=(i == 0),
            hovertemplate=f"<b>{group}</b><br>" +
                         f"Month: {date2.strftime('%Y-%m')}<br>" +
                         f"Proportion: {prop2:.1f}%<br>" +
                         f"Amount: {val2:.1f}<extra></extra>"
        ))
    
    # Update layout
    fig.update_layout(
        title=f"{variable.replace('_', ' ').title()} Proportions by {group_var}",
        xaxis_title="Proportion (%)",
        yaxis=dict(
            tickmode='array',
            tickvals=list(range(len(all_groups))),
            ticktext=list(sorted(all_groups)),
            title=group_var
        ),
        template="plotly_white",
        height=350,
        showlegend=True,
        margin=dict(l=100, r=50, t=80, b=50)
    )
    
    return fig

# Function to generate enhanced comparison text with proportion analysis
def generate_enhanced_comparison_text(var1_old, var1_new, var2_old, var2_new, date1, date2, 
                                    filter_var, filter_values, group_var, df1, df2):
    """Generate comprehensive comparison analysis text including proportion changes"""
    
    # Helper function to determine change type and generate sentence
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
            return f"{variable} amount was {old_val:.1f} in {date1.strftime('%Y-%m-%d')} and {change_type} at {new_val:.1f} in {date2.strftime('%Y-%m-%d')}."
        else:
            return f"{variable} amount was {old_val:.1f} in {date1.strftime('%Y-%m-%d')} and {change_type} to {new_val:.1f} in {date2.strftime('%Y-%m-%d')}, which corresponds to a relative {change_type.replace('increased', 'increase').replace('decreased', 'decrease')} of {abs(relative_change):.1f}%."
    
    # Build the text
    text_parts = []
    
    # Add filter information if applied
    if filter_var != "none" and filter_values:
        filter_text = f"Analysis filtered by {filter_var}: {', '.join(filter_values)}.\n\n"
        text_parts.append(filter_text)
    
    # Add comparison header
    text_parts.append("COMPARISON ANALYSIS:\n")
    text_parts.append("=" * 30 + "\n\n")
    
    # Generate sentences for Var1 and Var2
    var1_sentence = create_change_sentence("Var1", var1_old, var1_new, date1, date2)
    var2_sentence = create_change_sentence("Var2", var2_old, var2_new, date1, date2)
    
    text_parts.append(var1_sentence + "\n\n")
    text_parts.append(var2_sentence + "\n\n")
    
    # Add ratio analysis
    ratio_old = (var1_old / var2_old) if var2_old != 0 else 0
    ratio_new = (var1_new / var2_new) if var2_new != 0 else 0
    ratio_change = ratio_new - ratio_old
    
    if abs(ratio_change) < 0.01:
        ratio_text = f"The Var1/Var2 ratio remained stable at approximately {ratio_old:.2f}."
    elif ratio_change > 0:
        ratio_text = f"The Var1/Var2 ratio improved from {ratio_old:.2f} to {ratio_new:.2f}, representing an increase of {ratio_change:.2f}."
    else:
        ratio_text = f"The Var1/Var2 ratio declined from {ratio_old:.2f} to {ratio_new:.2f}, representing a decrease of {abs(ratio_change):.2f}."
    
    text_parts.append(ratio_text + "\n\n")
    
    # Add proportion analysis if grouping is selected
    if group_var != "none" and group_var in ['var3', 'var4'] and not df1.empty and not df2.empty:
        text_parts.append("PROPORTION ANALYSIS BY GROUPS:\n")
        text_parts.append("=" * 30 + "\n\n")
        
        # Analyze Var1 proportions
        var1_groups1 = df1.groupby(group_var)['var1'].sum()
        var1_total1 = df1['var1'].sum()
        var1_props1 = (var1_groups1 / var1_total1 * 100) if var1_total1 > 0 else pd.Series(dtype=float)
        
        var1_groups2 = df2.groupby(group_var)['var1'].sum()
        var1_total2 = df2['var1'].sum()
        var1_props2 = (var1_groups2 / var1_total2 * 100) if var1_total2 > 0 else pd.Series(dtype=float)
        
        text_parts.append("Var1 Proportion Changes:\n")
        all_groups = set(var1_props1.index) | set(var1_props2.index)
        for group in sorted(all_groups):
            prop1 = var1_props1.get(group, 0)
            prop2 = var1_props2.get(group, 0)
            amount1 = var1_groups1.get(group, 0)
            amount2 = var1_groups2.get(group, 0)
            prop_change = prop2 - prop1
            
            change_desc = "increased" if prop_change > 0 else "decreased" if prop_change < 0 else "remained stable"
            text_parts.append(f"• {group}: {prop1:.1f}% → {prop2:.1f}% ({change_desc} by {abs(prop_change):.1f}pp), amounts: {amount1:.1f} → {amount2:.1f}\n")
        
        text_parts.append("\n")
        
        # Analyze Var2 proportions
        var2_groups1 = df1.groupby(group_var)['var2'].sum()
        var2_total1 = df1['var2'].sum()
        var2_props1 = (var2_groups1 / var2_total1 * 100) if var2_total1 > 0 else pd.Series(dtype=float)
        
        var2_groups2 = df2.groupby(group_var)['var2'].sum()
        var2_total2 = df2['var2'].sum()
        var2_props2 = (var2_groups2 / var2_total2 * 100) if var2_total2 > 0 else pd.Series(dtype=float)
        
        text_parts.append("Var2 Proportion Changes:\n")
        all_groups = set(var2_props1.index) | set(var2_props2.index)
        for group in sorted(all_groups):
            prop1 = var2_props1.get(group, 0)
            prop2 = var2_props2.get(group, 0)
            amount1 = var2_groups1.get(group, 0)
            amount2 = var2_groups2.get(group, 0)
            prop_change = prop2 - prop1
            
            change_desc = "increased" if prop_change > 0 else "decreased" if prop_change < 0 else "remained stable"
            text_parts.append(f"• {group}: {prop1:.1f}% → {prop2:.1f}% ({change_desc} by {abs(prop_change):.1f}pp), amounts: {amount1:.1f} → {amount2:.1f}\n")
        
        text_parts.append("\n")
    
    # Add summary section
    text_parts.append("SUMMARY:\n")
    text_parts.append("=" * 30 + "\n")
    text_parts.append("• [Add your key insights here]\n")
    text_parts.append("• [Note any significant patterns]\n")
    text_parts.append("• [Record actionable findings]")
    
    return "".join(text_parts)

# Callback for navigation
@callback(
    [Output("today-content", "style"),
     Output("scenario-content", "style"),
     Output("nav-today", "active"),
     Output("nav-scenario", "active")],
    [Input("nav-today", "n_clicks"),
     Input("nav-scenario", "n_clicks")],
    prevent_initial_call=True
)
def update_navigation(today_clicks, scenario_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return {"display": "block"}, {"display": "none"}, True, False
    
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if triggered_id == "nav-today":
        return {"display": "block"}, {"display": "none"}, True, False
    elif triggered_id == "nav-scenario":
        return {"display": "none"}, {"display": "block"}, False, True
    
    return {"display": "block"}, {"display": "none"}, True, False

# Callback to update filter values based on selected filter variable
@callback(
    [Output("filter-values-selector", "data"),
     Output("filter-values-selector", "disabled"),
     Output("filter-values-selector", "value")],
    [Input("filter-selector", "value")]
)
def update_filter_values(filter_var):
    if filter_var == "none":
        return [], True, []
    
    if filter_var in ['Division', 'Type', 'Item', 'Function']:
        unique_values = sample_data[filter_var].unique()
        options = [{"value": val, "label": val} for val in sorted(unique_values)]
        return options, False, list(unique_values)  # Select all by default
    
    return [], True, []

# Callback for the main bar chart
@callback(
    Output("main-barchart", "figure"),
    [Input("variable-selector", "value"),
     Input("filter-selector", "value"),
     Input("filter-values-selector", "value"),
     Input("stack-selector", "value"),
     Input("group-selector", "value"),
     Input("year-range-slider", "value")]
)
def update_barchart(selected_var, filter_var, filter_values, stack_var, group_var, year_range):
    # Create a copy of the data for processing
    df = sample_data.copy()
    
    # Filter by year range
    df = df[(df['date'].dt.year >= year_range[0]) & (df['date'].dt.year <= year_range[1])]
    
    # Apply filtering if selected
    if filter_var != "none" and filter_var in df.columns and filter_values:
        df = df[df[filter_var].isin(filter_values)]
    
    # Prepare data for plotting - use year-month format since data is monthly
    df['month'] = df['date'].dt.to_period('M').astype(str)
    
    # Create the figure based on selected options
    fig = go.Figure()
    
    if stack_var != "none" and stack_var in df.columns:
        # Create stacked bar chart - each column per month divided by stack_var
        if stack_var in ['Division', 'Type', 'Item', 'Function']:  # Categorical variables
            # Group by month and stack variable, then sum the selected variable
            stacked_data = df.groupby(['month', stack_var])[selected_var].sum().unstack(fill_value=0)
            
            for category in stacked_data.columns:
                fig.add_trace(go.Bar(
                    x=stacked_data.index,
                    y=stacked_data[category],
                    name=f"{category}",
                    text=stacked_data[category].round(1),
                    textposition='auto',
                ))
        
        fig.update_layout(barmode='stack')
        
    elif group_var != "none" and group_var in df.columns:
        # Create grouped bar chart
        if group_var in ['Division', 'Type', 'Item', 'Function']:  # Categorical variables
            for category in df[group_var].unique():
                category_data = df[df[group_var] == category]
                monthly_data = category_data.groupby('month')[selected_var].sum().reset_index()
                
                fig.add_trace(go.Bar(
                    x=monthly_data['month'],
                    y=monthly_data[selected_var],
                    name=f"{category}",
                    text=monthly_data[selected_var].round(1),
                    textposition='auto',
                ))
        
        fig.update_layout(barmode='group')
        
    else:
        # Create simple bar chart
        monthly_data = df.groupby('month')[selected_var].sum().reset_index()
        
        fig.add_trace(go.Bar(
            x=monthly_data['month'],
            y=monthly_data[selected_var],
            name=selected_var.upper().replace('_', ' '),
            marker_color='#1f77b4',
            text=monthly_data[selected_var].round(1),
            textposition='auto',
        ))
    
    # Update layout
    fig.update_layout(
        title=f"{selected_var.upper()} Analysis Over Time",
        xaxis_title="Month",
        yaxis_title=selected_var.upper(),
        template="plotly_white",
        showlegend=True,
        height=400,
        margin=dict(l=50, r=50, t=80, b=50),
    )
    
    # Rotate x-axis labels for better readability
    fig.update_xaxes(tickangle=45)
    
    return fig

    return fig

@callback(
    Output("comparison-date-selector", "data"),
    Input("main-tabs", "value")
)
def populate_comparison_dates(active_tab):
    if active_tab == "comparison":
        # Get unique dates from the dataset and format them nicely
        unique_dates = sorted(sample_data['date'].dt.to_period('M').unique())
        date_options = [
            {
                "value": str(date), 
                "label": str(date)  # Format as YYYY-MM
            } 
            for date in unique_dates
        ]
        return date_options
    return []

# Callback to update comparison filter values
@callback(
    [Output("comparison-filter-values-selector", "data"),
     Output("comparison-filter-values-selector", "disabled"),
     Output("comparison-filter-values-selector", "value")],
    [Input("comparison-filter-selector", "value")]
)
def update_comparison_filter_values(filter_var):
    if filter_var == "none":
        return [], True, []
    
    if filter_var in ['Division', 'Type', 'Item', 'Function']:
        unique_values = sample_data[filter_var].unique()
        options = [{"value": val, "label": val} for val in sorted(unique_values)]
        return options, False, list(unique_values)  # Select all by default
    
    return [], True, []

# Enhanced callback for comparison content including dumbbell charts
@callback(
    [Output("comparison-value-boxes", "children"),
     Output("comparison-var1-chart", "figure"),
     Output("comparison-var2-chart", "figure"),
     Output("var1-dumbbell-chart", "figure"),
     Output("var2-dumbbell-chart", "figure"),
     Output("comparison-textbox", "value")],
    [Input("comparison-date-selector", "value"),
     Input("comparison-filter-selector", "value"),
     Input("comparison-filter-values-selector", "value"),
     Input("comparison-stack-selector", "value"),
     Input("comparison-group-selector", "value")]
)
def update_enhanced_comparison_content(selected_dates, filter_var, filter_values, stack_var, group_var):
    # Default empty figures
    empty_fig = go.Figure()
    empty_fig.update_layout(
        title="Select 2 dates to compare",
        template="plotly_white",
        height=300,
        showlegend=False
    )
    empty_fig.add_annotation(
        text="Please select exactly 2 dates for comparison",
        xref="paper", yref="paper",
        x=0.5, y=0.5, xanchor='center', yanchor='middle',
        showarrow=False, font=dict(size=14, color="gray")
    )
    
    # Check if exactly 2 dates are selected
    if not selected_dates or len(selected_dates) != 2:
        empty_boxes = dmc.Center([
            dmc.Text("Please select exactly 2 dates to see comparison metrics", c="dimmed", size="sm")
        ], style={"padding": "20px"})
        default_text = "Comparison Analysis:\n\n• Select exactly 2 dates to compare data\n• Use filters and grouping to focus analysis\n• Monitor value changes and ratios\n• Identify significant trends between periods\n\nKey Observations:\n• [Record changes in Var1 and Var2]\n• [Note ratio changes and their implications]\n• [Highlight significant variations]\n• [Document insights for decision making]"
        return empty_boxes, empty_fig, empty_fig, empty_fig, empty_fig, default_text
    
    # Convert dates and sort them (oldest first, newest second)
    date1, date2 = sorted([pd.to_datetime(date + '-01') for date in selected_dates])  # Convert YYYY-MM to datetime
    
    # Filter data for the selected months
    df = sample_data.copy()
    df_date1 = df[df['date'].dt.to_period('M') == date1.to_period('M')]
    df_date2 = df[df['date'].dt.to_period('M') == date2.to_period('M')]
    
    # Apply additional filtering if selected
    if filter_var != "none" and filter_var in df.columns and filter_values:
        df_date1 = df_date1[df_date1[filter_var].isin(filter_values)]
        df_date2 = df_date2[df_date2[filter_var].isin(filter_values)]
    
    # Calculate aggregate values for comparison - using Amount_total and Income_total as primary comparison variables
    amount_old = df_date1['Amount_total'].sum() if not df_date1.empty else 0
    amount_new = df_date2['Amount_total'].sum() if not df_date2.empty else 0
    income_old = df_date1['Income_total'].sum() if not df_date1.empty else 0
    income_new = df_date2['Income_total'].sum() if not df_date2.empty else 0
    
    # Calculate percentage changes
    amount_change = ((amount_new - amount_old) / amount_old * 100) if amount_old != 0 else 0
    income_change = ((income_new - income_old) / income_old * 100) if income_old != 0 else 0
    
    # Calculate ratios
    ratio_old = (amount_old / income_old) if income_old != 0 else 0
    ratio_new = (amount_new / income_new) if income_new != 0 else 0
    ratio_difference = ratio_new - ratio_old
    
    # Generate enhanced automatic text with proportion analysis
    comparison_text = generate_enhanced_comparison_text_updated(
        amount_old, amount_new, income_old, income_new, date1, date2, 
        filter_var, filter_values, group_var, df_date1, df_date2
    )
    
    # Create value boxes
    value_boxes = dmc.SimpleGrid([
        # Amount Change
        dmc.Card([
            dmc.Stack([
                dmc.Text("Amount Change", size="sm", c="dimmed"),
                dmc.Group([
                    dmc.Text(f"{amount_change:+.1f}%", size="xl", fw=700, 
                            c="green" if amount_change >= 0 else "red"),
                    DashIconify(
                        icon="material-symbols:trending-up" if amount_change >= 0 else "material-symbols:trending-down",
                        width=24,
                        color="green" if amount_change >= 0 else "red"
                    )
                ], justify="space-between", align="center"),
                dmc.Text(f"{amount_old:.1f} → {amount_new:.1f}", size="xs", c="dimmed")
            ], gap="xs")
        ], withBorder=True, shadow="sm", radius="md", p="md"),
        
        # Income Change
        dmc.Card([
            dmc.Stack([
                dmc.Text("Income Change", size="sm", c="dimmed"),
                dmc.Group([
                    dmc.Text(f"{income_change:+.1f}%", size="xl", fw=700,
                            c="green" if income_change >= 0 else "red"),
                    DashIconify(
                        icon="material-symbols:trending-up" if income_change >= 0 else "material-symbols:trending-down",
                        width=24,
                        color="green" if income_change >= 0 else "red"
                    )
                ], justify="space-between", align="center"),
                dmc.Text(f"{income_old:.1f} → {income_new:.1f}", size="xs", c="dimmed")
            ], gap="xs")
        ], withBorder=True, shadow="sm", radius="md", p="md"),
        
        # Ratio Difference
        dmc.Card([
            dmc.Stack([
                dmc.Text("Amount/Income Ratio Change", size="sm", c="dimmed"),
                dmc.Group([
                    dmc.Text(f"{ratio_difference:+.2f}", size="xl", fw=700,
                            c="green" if ratio_difference >= 0 else "red"),
                    DashIconify(
                        icon="material-symbols:trending-up" if ratio_difference >= 0 else "material-symbols:trending-down",
                        width=24,
                        color="green" if ratio_difference >= 0 else "red"
                    )
                ], justify="space-between", align="center"),
                dmc.Text(f"{ratio_old:.2f} → {ratio_new:.2f}", size="xs", c="dimmed")
            ], gap="xs")
        ], withBorder=True, shadow="sm", radius="md", p="md"),
    ], cols=3, spacing="sm", mb="lg")
    
    # Create comparison charts using updated function
    def create_comparison_chart_updated(df1, df2, variable, date1, date2):
        fig = go.Figure()
        
        # Create categorical x-axis labels
        date_labels = [date1.strftime('%Y-%m'), date2.strftime('%Y-%m')]
        
        if group_var != "none" and group_var in df.columns:
            # Grouped comparison
            if group_var in ['Division', 'Type', 'Item', 'Function']:  # Categorical variables
                # Get all unique categories from both datasets
                all_categories = set()
                if not df1.empty:
                    all_categories.update(df1[group_var].unique())
                if not df2.empty:
                    all_categories.update(df2[group_var].unique())
                categories = sorted(all_categories)
                
                for category in categories:
                    # Calculate values for each category at each date
                    val1 = df1[df1[group_var] == category][variable].sum() if not df1.empty and category in df1[group_var].values else 0
                    val2 = df2[df2[group_var] == category][variable].sum() if not df2.empty and category in df2[group_var].values else 0
                    
                    fig.add_trace(go.Bar(
                        x=date_labels,
                        y=[val1, val2],
                        name=f"{category}",
                        text=[f"{val1:.1f}", f"{val2:.1f}"],
                        textposition='auto',
                    ))
                fig.update_layout(barmode='group')
                
        elif stack_var != "none" and stack_var in df.columns:
            # Stacked comparison
            if stack_var in ['Division', 'Type', 'Item', 'Function']:  # Categorical variables
                # Get all unique categories from both datasets
                all_categories = set()
                if not df1.empty:
                    all_categories.update(df1[stack_var].unique())
                if not df2.empty:
                    all_categories.update(df2[stack_var].unique())
                categories = sorted(all_categories)
                
                for category in categories:
                    val1 = df1[df1[stack_var] == category][variable].sum() if not df1.empty and category in df1[stack_var].values else 0
                    val2 = df2[df2[stack_var] == category][variable].sum() if not df2.empty and category in df2[stack_var].values else 0
                    
                    fig.add_trace(go.Bar(
                        x=date_labels,
                        y=[val1, val2],
                        name=f"{category}",
                        text=[f"{val1:.1f}", f"{val2:.1f}"],
                        textposition='auto',
                    ))
                fig.update_layout(barmode='stack')
                
        else:
            # Simple comparison - just sum all values for each date
            val1 = df1[variable].sum() if not df1.empty else 0
            val2 = df2[variable].sum() if not df2.empty else 0
            
            fig.add_trace(go.Bar(
                x=date_labels,
                y=[val1, val2],
                name=variable.replace('_', ' ').title(),
                marker_color=['#1f77b4', '#ff7f0e'],
                text=[f"{val1:.1f}", f"{val2:.1f}"],
                textposition='auto',
            ))
        
        fig.update_layout(
            title=f"{variable.replace('_', ' ').title()} Comparison",
            xaxis_title="Month",
            yaxis_title=variable.replace('_', ' ').title(),
            template="plotly_white",
            height=300,
            showlegend=True,
            xaxis=dict(type='category')  # Force categorical x-axis
        )
        
        return fig
    
    # Generate charts
    amount_chart = create_comparison_chart_updated(df_date1, df_date2, 'Amount_total', date1, date2)
    income_chart = create_comparison_chart_updated(df_date1, df_date2, 'Income_total', date1, date2)
    
    # Create dumbbell charts using updated function
    amount_dumbbell = create_dumbbell_chart_updated(df_date1, df_date2, 'Amount_total', date1, date2, group_var)
    income_dumbbell = create_dumbbell_chart_updated(df_date1, df_date2, 'Income_total', date1, date2, group_var)
    
    return value_boxes, amount_chart, income_chart, amount_dumbbell, income_dumbbell, comparison_text

# Callback for save analysis button (placeholder)
@callback(
    Output("save-analysis-btn", "children"),
    Input("save-analysis-btn", "n_clicks"),
    State("analysis-textbox", "value"),
    prevent_initial_call=True
)
def save_analysis(n_clicks, analysis_text):
    if n_clicks:
        # Here you would implement actual saving functionality
        # For now, just provide feedback
        return "Analysis Saved!"
    return "Save Analysis"

# Callback for save comparison button (placeholder)
@callback(
    Output("save-comparison-btn", "children"),
    Input("save-comparison-btn", "n_clicks"),
    State("comparison-textbox", "value"),
    prevent_initial_call=True
)
def save_comparison(n_clicks, comparison_text):
    if n_clicks:
        # Here you would implement actual saving functionality
        # For now, just provide feedback
        return "Comparison Saved!"
    return "Save Comparison"

if __name__ == "__main__":
    app.run(debug=True)