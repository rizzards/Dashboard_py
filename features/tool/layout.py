"""
Layout components for the Tool feature
Defines the UI structure for the tool tab with division/item/function filters
"""
from dash import dcc, html
import dash_mantine_components as dmc
from dash_iconify import DashIconify

from shared.data_loaders import sample_data, min_year, max_year


def create_tool_layout():
    """
    Create the complete layout for the Tool tab.

    Returns:
        dmc.TabsPanel component containing the tool tab UI
    """
    return dmc.TabsPanel(value="tool", children=[
        dmc.Stack([
            # Tool Controls Card
            dmc.Card([
                dmc.CardSection([
                    dmc.Title("Tool Analysis Controls", order=4, mb="md"),

                    # Year Range Slider
                    dmc.Stack([
                        dmc.Text("Year Range:", size="sm", fw=500, mb=5),
                        dmc.RangeSlider(
                            id="tool-year-range-slider",
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

                    # Division, Item, Function Filters
                    dmc.Grid([
                        dmc.GridCol(span=4, children=[
                            dmc.Text("Filter by Division:", size="sm", fw=500, mb=5),
                            dmc.Select(
                                id="tool-division-filter",
                                placeholder="Select Division",
                                value="none",
                                size="sm",
                                data=[{"value": "none", "label": "All Divisions"}] +
                                    [{"value": val, "label": val}
                                     for val in sorted(sample_data['Division'].unique())]
                            )
                        ]),
                        dmc.GridCol(span=4, children=[
                            dmc.Text("Filter by Item:", size="sm", fw=500, mb=5),
                            dmc.Select(
                                id="tool-item-filter",
                                placeholder="Select Item",
                                value="none",
                                size="sm",
                                data=[{"value": "none", "label": "All Items"}] +
                                    [{"value": val, "label": val}
                                     for val in sorted(sample_data['Item'].unique())]
                            )
                        ]),
                        dmc.GridCol(span=4, children=[
                            dmc.Text("Filter by Function:", size="sm", fw=500, mb=5),
                            dmc.Select(
                                id="tool-function-filter",
                                placeholder="Select Function",
                                value="none",
                                size="sm",
                                data=[{"value": "none", "label": "All Functions"}] +
                                    [{"value": val, "label": val}
                                     for val in sorted(sample_data['Function'].unique())]
                            )
                        ]),
                    ], gutter="md", mb="lg"),
                ], withBorder=True, inheritPadding=True, py="md"),
            ], withBorder=True, shadow="sm", radius="md", mb="md"),

            # Income Chart Card
            dmc.Card([
                dmc.CardSection([
                    dmc.Title("Income Analysis: Original vs Corrected", order=4, mb="md"),
                    dcc.Graph(id="tool-income-chart", style={"height": "500px"})
                ], inheritPadding=True, pt="xs"),

                # Export Buttons
                dmc.CardSection([
                    dmc.Group([
                        dmc.Button(
                            "Export Tool Data - Excel",
                            id="tool-export-btn",
                            variant="filled",
                            size="sm",
                            leftSection=DashIconify(icon="vscode-icons:file-type-excel", width=20)
                        ),
                        dmc.Button(
                            "Export Charts as PNG",
                            id="tool-png-btn",
                            variant="filled",
                            size="sm",
                            leftSection=DashIconify(icon="mdi:image", width=20)
                        ),
                    ]),
                    dcc.Download(id="download-tool-data"),
                    dcc.Download(id="download-tool-png"),
                ], inheritPadding=True, pt="xs"),
            ], withBorder=True, shadow="sm", radius="md")
        ], gap="md")
    ])
