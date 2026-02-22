"""
Layout components for the Scenario feature
Defines the UI structure for scenario analysis tabs (Scenario Weight and Prediction)
"""
from dash import dcc
import dash_mantine_components as dmc
from dash_iconify import DashIconify

from shared.data_loaders import min_year, max_year
from config_macro import get_countries, get_indicators, DEFAULT_COUNTRY, DEFAULT_INDICATOR


def create_scenario_layout():
    """
    Create the complete layout for the Scenario section with tabs.

    Returns:
        dmc.Tabs component containing the scenario tabs UI
    """
    return dmc.Tabs(value="scenario_probability", id="scenario-tabs", children=[
            # Tab List
            dmc.TabsList([
                dmc.TabsTab("Scenario Probability", value="scenario_probability"),
                dmc.TabsTab("Prediction", value="prediction"),
            ]),

            # Scenario Probability Tab Panel
            dmc.TabsPanel(value="scenario_probability", children=[
                dmc.Stack([
                    # Scenario Controls Card
                    dmc.Card([
                        dmc.CardSection([
                            dmc.Title("Scenario Probability Controls", order=4, mb="md"),

                            # Year Range Slider
                            dmc.Stack([
                                dmc.Text("Year Range:", size="sm", fw=500, mb=5),
                                dmc.RangeSlider(
                                    id="scenario-year-range-slider",
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
                        ], withBorder=True, inheritPadding=True, py="md"),
                    ], withBorder=True, shadow="sm", radius="md", mb="md"),

                    # Scenario Weight Chart Card
                    dmc.Card([
                        dmc.CardSection([
                            dmc.Title("Scenario Weight Distribution", order=4, mb="md"),
                            dcc.Graph(id="scenario-weight-chart", style={"height": "500px"})
                        ], inheritPadding=True, pt="xs"),

                        # Export Buttons
                        dmc.CardSection([
                            dmc.Group([
                                dmc.Button(
                                    "Export Scenario Data - Excel",
                                    id="scenario-export-btn",
                                    variant="filled",
                                    size="sm",
                                    leftSection=DashIconify(icon="vscode-icons:file-type-excel", width=20)
                                ),
                                dmc.Button(
                                    "Export Chart as PNG",
                                    id="scenario-png-btn",
                                    variant="filled",
                                    size="sm",
                                    leftSection=DashIconify(icon="mdi:image", width=20)
                                ),
                            ]),
                            dcc.Download(id="download-scenario-data"),
                            dcc.Download(id="download-scenario-png"),
                        ], inheritPadding=True, pt="xs"),
                    ], withBorder=True, shadow="sm", radius="md")
                ], gap="md")
            ]),

            # Prediction Tab Panel
            dmc.TabsPanel(value="prediction", children=[
                dmc.Stack([
                    # Macroeconomic Controls Card
                    dmc.Card([
                        dmc.CardSection([
                            dmc.Title("Macroeconomic Prediction Controls", order=4, mb="md"),

                            dmc.Grid([
                                # Country Selector
                                dmc.GridCol([
                                    dmc.Stack([
                                        dmc.Text("Country:", size="sm", fw=500, mb=5),
                                        dmc.Select(
                                            id="prediction-country-selector",
                                            data=[{"value": country, "label": country}
                                                  for country in get_countries()],
                                            value=DEFAULT_COUNTRY,
                                            searchable=True,
                                            clearable=False,
                                            size="sm"
                                        )
                                    ], gap="xs")
                                ], span=6),

                                # Macro Indicator Selector
                                dmc.GridCol([
                                    dmc.Stack([
                                        dmc.Text("Macro Indicator:", size="sm", fw=500, mb=5),
                                        dmc.Select(
                                            id="prediction-indicator-selector",
                                            data=[{"value": ind, "label": ind}
                                                  for ind in get_indicators(DEFAULT_COUNTRY)],
                                            value=DEFAULT_INDICATOR,
                                            searchable=True,
                                            clearable=False,
                                            size="sm"
                                        )
                                    ], gap="xs")
                                ], span=6),
                            ], gutter="md", mb="md"),

                            # Historical Time Series Toggle
                            dmc.Group([
                                dmc.Switch(
                                    id="prediction-historical-toggle",
                                    label="Include Historical Time Series",
                                    checked=True,
                                    size="md"
                                )
                            ], mb="md"),

                        ], withBorder=True, inheritPadding=True, py="md"),
                    ], withBorder=True, shadow="sm", radius="md", mb="md"),

                    # Prediction Chart Card
                    dmc.Card([
                        dmc.CardSection([
                            dmc.Title("Macroeconomic Forecast", order=4, mb="md"),
                            dcc.Graph(
                                id="prediction-chart",
                                style={"height": "500px"},
                                config={'displayModeBar': True}
                            )
                        ], inheritPadding=True, pt="xs"),

                        # Export Buttons
                        dmc.CardSection([
                            dmc.Group([
                                dmc.Button(
                                    "Export Prediction Data - Excel",
                                    id="prediction-export-btn",
                                    variant="filled",
                                    size="sm",
                                    leftSection=DashIconify(icon="vscode-icons:file-type-excel", width=20)
                                ),
                                dmc.Button(
                                    "Export Chart as PNG",
                                    id="prediction-png-btn",
                                    variant="filled",
                                    size="sm",
                                    leftSection=DashIconify(icon="mdi:image", width=20)
                                ),
                            ]),
                            dcc.Download(id="download-prediction-data"),
                            dcc.Download(id="download-prediction-png"),
                        ], inheritPadding=True, pt="xs"),
                    ], withBorder=True, shadow="sm", radius="md")
                ], gap="md")
            ]),
        ])
