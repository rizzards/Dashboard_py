"""
Layout components for the History feature
Defines the UI structure for the history tab
"""
from dash import dcc, html
import dash_mantine_components as dmc
from dash_iconify import DashIconify

from shared.data_loaders import sample_data, min_year, max_year


def create_history_layout():
    """
    Create the complete layout for the History tab.

    Returns:
        dmc.TabsPanel component containing the history tab UI
    """
    return dmc.TabsPanel(value="history", children=[
        dmc.Stack([
            # Chart Controls Card
            dmc.Card([
                dmc.CardSection([
                    dmc.Title("Chart Controls", order=4, mb="md"),

                    # Variable Selector
                    dmc.Stack([
                        dmc.Text("Display Variable:", size="sm", fw=500, mb=5),
                        dmc.SegmentedControl(
                            id="variable-selector",
                            value="Total",
                            orientation="horizontal",
                            fullWidth=True,
                            color="blue",
                            size="sm",
                            data=[
                                {"value": "Total", "label": "Total"},
                                {"value": "Best", "label": "Best"},
                                {"value": "Type1", "label": "Type 1"},
                                {"value": "Type2", "label": "Type 2"},
                                {"value": "Type3", "label": "Type 3"}
                            ]
                        ),
                    ], gap="xs", mb="md"),

                    # Year Range Slider
                    dmc.Stack([
                        dmc.Text("Year Range:", size="sm", fw=500, mb=5),
                        dmc.RangeSlider(
                            id="year-range-slider",
                            min=min_year,
                            max=max_year,
                            step=1,
                            value=[min_year, max_year],
                            marks=[{"value": year, "label": str(year)}
                                  for year in range(min_year, max_year + 1)],
                            mb="md",
                            minRange=1,
                            size="md",
                            style={"width": "100%"}
                        )
                    ], gap="xs", mb="lg"),

                    # Entity, Division, Stack, Group Controls
                    dmc.Grid([
                        dmc.GridCol(span=3, children=[
                            dmc.Text("Entity:", size="sm", fw=500, mb=5),
                            dmc.Select(
                                id="entity-selector",
                                placeholder="Select entity",
                                value="All",
                                size="sm",
                                data=[{"value": "All", "label": "All"}] + [
                                    {"value": val, "label": val}
                                    for val in sorted(sample_data['Entity'].unique())
                                    if val != "All"
                                ]
                            )
                        ]),
                        dmc.GridCol(span=3, children=[
                            dmc.Text("Division:", size="sm", fw=500, mb=5),
                            dmc.Select(
                                id="division-selector",
                                placeholder="Select division",
                                value="All",
                                size="sm",
                                data=[{"value": "All", "label": "All"}] + [
                                    {"value": val, "label": val}
                                    for val in sorted(sample_data['Division'].unique())
                                    if val != "All"
                                ]
                            )
                        ]),
                        dmc.GridCol(span=3, children=[
                            dmc.Text("Stack by:", size="sm", fw=500, mb=5),
                            dmc.Select(
                                id="stack-selector",
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
                                id="group-selector",
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

                    # Filter Controls
                    dmc.Grid([
                        dmc.GridCol(span=6, children=[
                            dmc.Text("Filter by:", size="sm", fw=500, mb=5),
                            dmc.Select(
                                id="filter-selector",
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
                                id="filter-values-selector",
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

            # Events Summary Card
            dmc.Card([
                dmc.CardSection([
                    dmc.Title("Events Summary", order=4, mb="md"),

                    # Events Filter Controls
                    dmc.Grid([
                        dmc.GridCol(span=4, children=[
                            dmc.Text("Select Date:", size="sm", fw=500, mb=5),
                            dmc.Select(
                                id="events-date-selector",
                                placeholder="Select date",
                                data=[],
                                value=None,
                                size="sm",
                                searchable=True,
                                clearable=True,
                                leftSection=DashIconify(icon="material-symbols:calendar-month", width=20)
                            )
                        ]),
                        dmc.GridCol(span=4, children=[
                            dmc.Text("Division:", size="sm", fw=500, mb=5),
                            dmc.Select(
                                id="events-division-selector",
                                placeholder="Select division",
                                value=None,
                                size="sm",
                                data=[],
                                searchable=True,
                                clearable=True
                            )
                        ]),
                        dmc.GridCol(span=4, children=[
                            dmc.Text("Metric:", size="sm", fw=500, mb=5),
                            dmc.Select(
                                id="events-metric-selector",
                                placeholder="Select metric",
                                value=None,
                                size="sm",
                                data=[],
                                searchable=True,
                                clearable=True
                            )
                        ]),
                    ], gutter="md", mb="md"),

                    # Events Display
                    dmc.Stack([
                        dmc.Switch(
                            id="events-details-toggle",
                            label="Include Additional Details",
                            checked=False,
                            size="sm"
                        ),
                        dmc.Textarea(
                            id="events-textbox",
                            placeholder="Select date, division, and metric to view summary...",
                            autosize=True,
                            minRows=6,
                            maxRows=12,
                            value=""
                        )
                    ], gap="xs")
                ], withBorder=True, inheritPadding=True, py="md"),
            ], withBorder=True, shadow="sm", radius="md", mb="md"),

            # Charts and Metrics Card
            dmc.Card([
                # Summary Metrics
                dmc.CardSection([
                    dmc.Title("Summary Metrics", order=6, mb="sm"),
                    html.Div(id="history-summary-boxes")
                ], inheritPadding=True, pt="xs"),

                # Amount Analysis Chart
                dmc.CardSection([
                    dmc.Title("Amount Analysis", order=6, mb="sm"),
                    dcc.Graph(id="amount-barchart", style={"height": "350px"})
                ], inheritPadding=True, pt="xs"),

                # Income Analysis Chart
                dmc.CardSection([
                    dmc.Title("Income Analysis", order=6, mb="sm"),
                    dcc.Graph(id="income-barchart", style={"height": "350px"})
                ], inheritPadding=True, pt="xs"),

                # Quarterly Income Difference Chart
                dmc.CardSection([
                    dmc.Title("Quarterly Income Difference", order=6, mb="sm"),
                    dcc.Graph(id="income-diff-chart", style={"height": "350px"})
                ], inheritPadding=True, pt="xs"),

                # Return Ratio Chart
                dmc.CardSection([
                    dmc.Title("Return Ratio (Income/Amount)", order=6, mb="sm"),
                    dcc.Graph(id="ratio-chart", style={"height": "250px"})
                ], inheritPadding=True, pt="xs"),

                # Export Buttons
                dmc.CardSection([
                    dmc.Group([
                        dmc.Button(
                            "Export History Data - Excel",
                            id="history-export-btn",
                            variant="filled",
                            size="sm",
                            leftSection=DashIconify(icon="vscode-icons:file-type-excel", width=20)
                        ),
                        dmc.Button(
                            "Export Charts as PNG",
                            id="history-png-btn",
                            variant="filled",
                            size="sm",
                            leftSection=DashIconify(icon="mdi:image", width=20)
                        ),
                    ]),
                    dcc.Download(id="download-history-data"),
                    dcc.Download(id="download-history-png"),
                ], inheritPadding=True, pt="xs"),
            ], withBorder=True, shadow="sm", radius="md")
        ], gap="md")
    ])
