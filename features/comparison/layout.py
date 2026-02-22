"""
Comparison Feature - UI Layout
Defines the user interface layout for the comparison tab
"""

from dash import dcc, html
import dash_mantine_components as dmc
from dash_iconify import DashIconify
from shared.data_loaders import sample_data


def create_comparison_layout():
    """
    Create the complete comparison tab layout

    Returns:
        dmc.Stack: Comparison tab layout with all controls, filters, and charts
    """
    return dmc.Stack([
        # Comparison Controls Card
        dmc.Card([
            dmc.CardSection([
                dmc.Title("Comparison Controls", order=4, mb="md"),

                # Display Type Selector
                dmc.Group([
                    dmc.Stack([
                        dmc.Text("Display Type:", size="sm", fw=500, mb=5),
                        dmc.SegmentedControl(
                            id="comparison-type-selector",
                            value="Total",
                            orientation="horizontal",
                            fullWidth=False,
                            color="blue",
                            size="sm",
                            data=[
                                {"value": "Total", "label": "Total"},
                                {"value": "Best", "label": "Best"},
                                {"value": "Type1", "label": "Type 1"},
                                {"value": "Type2", "label": "Type 2"},
                                {"value": "Type3", "label": "Type 3"}
                            ]
                        )
                    ], gap="xs", style={"flex": 1})
                ], justify="flex-start", align="flex-start", mb="lg"),

                # Date Selector
                dmc.Group([
                    dmc.Stack([
                        dmc.Text("Select Dates for Comparison:", size="sm", fw=500, mb=5),
                        dmc.MultiSelect(
                            id="comparison-date-selector",
                            placeholder="Select exactly 2 dates to compare",
                            data=[],
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
                        )
                    ], gap="xs", style={"flex": 1})
                ], justify="flex-start", align="flex-start", mb="lg"),

                # Entity, Division, Stack, Group Filters
                dmc.Grid([
                    dmc.GridCol(span=3, children=[
                        dmc.Text("Entity:", size="sm", fw=500, mb=5),
                        dmc.Select(
                            id="comparison-entity-selector",
                            placeholder="Select entity",
                            value="All",
                            size="sm",
                            data=[{"value": "All", "label": "All"}] +
                                [{"value": val, "label": val} for val in sorted(sample_data['Entity'].unique()) if val != "All"]
                        )
                    ]),
                    dmc.GridCol(span=3, children=[
                        dmc.Text("Division:", size="sm", fw=500, mb=5),
                        dmc.Select(
                            id="comparison-division-selector",
                            placeholder="Select division",
                            value="All",
                            size="sm",
                            data=[{"value": "All", "label": "All"}] +
                                [{"value": val, "label": val} for val in sorted(sample_data['Division'].unique()) if val != "All"]
                        )
                    ]),
                    dmc.GridCol(span=3, children=[
                        dmc.Text("Stack by:", size="sm", fw=500, mb=5),
                        dmc.Select(
                            id="comparison-stack-selector",
                            placeholder="Select stack variable",
                            value="none",
                            size="sm",
                            data=[
                                {"value": "none", "label": "No Stack"},
                                {"value": "Type", "label": "Type"},
                                {"value": "Item", "label": "Item"},
                                {"value": "Function", "label": "Function"}
                            ]
                        )
                    ]),
                    dmc.GridCol(span=3, children=[
                        dmc.Text("Group by:", size="sm", fw=500, mb=5),
                        dmc.Select(
                            id="comparison-group-selector",
                            placeholder="Select group variable",
                            value="none",
                            size="sm",
                            data=[
                                {"value": "none", "label": "No Grouping"},
                                {"value": "Type", "label": "Type"},
                                {"value": "Item", "label": "Item"},
                                {"value": "Function", "label": "Function"}
                            ]
                        )
                    ]),
                ], gutter="md", mb="md"),

                # Additional Filters
                dmc.Grid([
                    dmc.GridCol(span=6, children=[
                        dmc.Text("Filter by:", size="sm", fw=500, mb=5),
                        dmc.Select(
                            id="comparison-filter-selector",
                            placeholder="Select filter",
                            value="none",
                            size="sm",
                            data=[
                                {"value": "none", "label": "No Filter"},
                                {"value": "Type", "label": "Type"},
                                {"value": "Item", "label": "Item"},
                                {"value": "Function", "label": "Function"}
                            ]
                        )
                    ]),
                    dmc.GridCol(span=6, children=[
                        dmc.Text("Filter values:", size="sm", fw=500, mb=5),
                        dmc.MultiSelect(
                            id="comparison-filter-values-selector",
                            placeholder="Select values",
                            data=[],
                            value=[],
                            size="sm",
                            disabled=True
                        )
                    ]),
                ], gutter="md", mb="lg"),
            ], withBorder=True, inheritPadding=True, py="md"),
        ], withBorder=True, shadow="sm", radius="md", mb="md"),

        # Comparison Notes Card
        dmc.Card([
            dmc.CardSection([
                dmc.Title("Comparison Notes", order=4, mb="md"),
                dmc.Group([
                    dmc.Switch(
                        id="financial-analyst-toggle",
                        label="AI Financial Analyst",
                        checked=False,
                        size="sm",
                        description="Enable LLM-powered analysis (requires Azure OpenAI setup)"
                    )
                ], mb="sm"),
                dmc.Textarea(
                    id="comparison-textbox",
                    placeholder="Enter your comparison analysis notes here...",
                    autosize=True,
                    minRows=8,
                    maxRows=15,
                    value="Comparison Analysis:\n\n• Select exactly 2 dates to compare data\n• Use filters and grouping to focus analysis\n• Monitor value changes and ratios\n• Identify significant trends between periods"
                )
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

        # Comparison Charts and Results Card
        dmc.Card([
            # Comparison Metrics Section
            dmc.CardSection([
                dmc.Title("Comparison Metrics", order=6, mb="sm"),
                html.Div(id="comparison-value-boxes")
            ], inheritPadding=True, pt="xs"),

            # Amount and Income Total Comparison
            dmc.CardSection([
                dmc.Grid([
                    dmc.GridCol([
                        dmc.Title("Amount Total Comparison", order=6, mb="sm"),
                        dcc.Graph(id="comparison-var1-chart", style={"height": "300px"})
                    ], span=6),
                    dmc.GridCol([
                        dmc.Title("Income Total Comparison", order=6, mb="sm"),
                        dcc.Graph(id="comparison-var2-chart", style={"height": "300px"})
                    ], span=6),
                ], gutter="md")
            ], inheritPadding=True, pt="xs"),

            # Return Ratio Comparison
            dmc.CardSection([
                dmc.Title("Return Ratio (Income/Amount) Comparison", order=6, mb="sm"),
                dcc.Graph(id="ratio-comparison-chart", style={"height": "400px"})
            ], inheritPadding=True, pt="xs"),

            # Heatmap Comparison
            dmc.CardSection([
                dmc.Title("Heatmap Comparison", order=6, mb="sm"),
                dmc.Grid([
                    dmc.GridCol([
                        dmc.Title("Amount Heatmap", order=6, mb="sm"),
                        dcc.Graph(id="amount-heatmap-chart", style={"height": "350px"})
                    ], span=6),
                    dmc.GridCol([
                        dmc.Title("Income Heatmap", order=6, mb="sm"),
                        dcc.Graph(id="income-heatmap-chart", style={"height": "350px"})
                    ], span=6),
                ], gutter="md")
            ], inheritPadding=True, pt="xs"),

            # Proportion Changes Analysis
            dmc.CardSection([
                dmc.Title("Proportion Changes Analysis", order=6, mb="sm"),
                dmc.Grid([
                    dmc.GridCol([
                        dmc.Title("Amount Total Proportion Changes", order=6, mb="sm"),
                        dcc.Graph(id="var1-dumbbell-chart", style={"height": "350px"})
                    ], span=6),
                    dmc.GridCol([
                        dmc.Title("Income Total Proportion Changes", order=6, mb="sm"),
                        dcc.Graph(id="var2-dumbbell-chart", style={"height": "350px"})
                    ], span=6),
                ], gutter="md")
            ], inheritPadding=True, pt="xs"),

            # Division Percentage Contribution
            dmc.CardSection([
                dmc.Title("Division Percentage Contribution", order=6, mb="sm"),
                dmc.Grid([
                    dmc.GridCol([
                        dmc.Title("Amount by Division", order=6, mb="sm"),
                        dcc.Graph(id="amount-division-chart", style={"height": "350px"})
                    ], span=6),
                    dmc.GridCol([
                        dmc.Title("Income by Division", order=6, mb="sm"),
                        dcc.Graph(id="income-division-chart", style={"height": "350px"})
                    ], span=6),
                ], gutter="md")
            ], inheritPadding=True, pt="xs"),

            # Type 2 Breakdown (WW / DP / PP)
            dmc.CardSection([
                dmc.Title("Type 2 Breakdown (WW / DP / PP)", order=6, mb="sm"),
                dmc.Grid([
                    dmc.GridCol([
                        dmc.Title("Amount Breakdown", order=6, mb="sm"),
                        dcc.Graph(id="type2-amount-chart", style={"height": "350px"})
                    ], span=6),
                    dmc.GridCol([
                        dmc.Title("Income Breakdown", order=6, mb="sm"),
                        dcc.Graph(id="type2-income-chart", style={"height": "350px"})
                    ], span=6),
                ], gutter="md")
            ], inheritPadding=True, pt="xs"),

            # Export Buttons
            dmc.CardSection([
                dmc.Group([
                    dmc.Button(
                        "Export Comparison Data - Excel",
                        id="export-excel-btn",
                        variant="filled",
                        size="sm",
                        leftSection=DashIconify(icon="vscode-icons:file-type-excel", width=20)
                    ),
                    dmc.Button(
                        "Export Charts as PNG",
                        id="comparison-png-btn",
                        variant="filled",
                        size="sm",
                        leftSection=DashIconify(icon="mdi:image", width=20)
                    ),
                ]),
                dcc.Download(id="download-dataframe-xlsx"),
                dcc.Download(id="download-comparison-png"),
            ], inheritPadding=True, pt="xs"),
        ], withBorder=True, shadow="sm", radius="md")
    ], gap="md")
