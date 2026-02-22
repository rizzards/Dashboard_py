"""
Main Application Layout
Creates the complete Dash application layout with navigation and feature integration
"""
from dash import html, dcc
import dash_mantine_components as dmc
from dash_iconify import DashIconify
from datetime import datetime

# Import feature layouts
from features.history import create_history_layout
from features.comparison import create_comparison_layout
from features.tool import create_tool_layout
from features.scenario import create_scenario_layout


def create_app_layout():
    """
    Creates the complete application layout.

    Returns:
        dmc.MantineProvider: Complete application layout with navigation and all features
    """
    return dmc.MantineProvider(
        theme={"colorScheme": "light", "primaryColor": "gray"},
        children=[dmc.AppShell(
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
                                dmc.Text(
                                    f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                                    size="sm",
                                    c="dimmed"
                                ),
                            ]
                        )
                    ]
                ),

                # Sidebar Navigation
                dmc.AppShellNavbar(
                    p="md",
                    children=[
                        dmc.Title("Navigation", order=4, mb="md"),
                        dmc.NavLink(
                            label="Today",
                            id="nav-today",
                            leftSection=DashIconify(icon="material-symbols:today", width=20),
                            active=True
                        ),
                        dmc.NavLink(
                            label="Scenario",
                            id="nav-scenario",
                            leftSection=DashIconify(icon="material-symbols:analytics", width=20)
                        ),
                    ]
                ),

                # Main Content Area
                dmc.AppShellMain(
                    id="main-content",
                    children=[
                        # Today Content (History, Comparison, Tool tabs)
                        html.Div(
                            id="today-content",
                            style={"display": "block"},
                            children=[
                                dmc.Tabs(
                                    value="history",
                                    id="main-tabs",
                                    children=[
                                        # Tab List
                                        dmc.TabsList([
                                            dmc.TabsTab("History", value="history"),
                                            dmc.TabsTab("Comparison", value="comparison"),
                                            dmc.TabsTab("Tool", value="tool"),
                                        ]),

                                        # History Tab
                                        dmc.TabsPanel(
                                            value="history",
                                            children=[create_history_layout()]
                                        ),

                                        # Comparison Tab
                                        dmc.TabsPanel(
                                            value="comparison",
                                            children=[create_comparison_layout()]
                                        ),

                                        # Tool Tab
                                        dmc.TabsPanel(
                                            value="tool",
                                            children=[create_tool_layout()]
                                        ),
                                    ]
                                )
                            ]
                        ),

                        # Scenario Content (separate section)
                        html.Div(
                            id="scenario-content",
                            style={"display": "none"},
                            children=[create_scenario_layout()]
                        )
                    ]
                )
            ]
        )]
    )


# Callback for navigation toggle (kept here since it's navigation-specific)
from dash import callback, Input, Output, ctx

@callback(
    [Output("today-content", "style"), Output("scenario-content", "style"),
     Output("nav-today", "active"), Output("nav-scenario", "active")],
    [Input("nav-today", "n_clicks"), Input("nav-scenario", "n_clicks")],
    prevent_initial_call=True
)
def toggle_navigation(today_clicks, scenario_clicks):
    """
    Toggle between Today and Scenario views based on which nav item was clicked.

    Args:
        today_clicks: Number of clicks on Today nav item
        scenario_clicks: Number of clicks on Scenario nav item

    Returns:
        tuple: Display styles and active states for both sections
    """
    triggered = ctx.triggered_id
    if triggered == "nav-scenario":
        return {"display": "none"}, {"display": "block"}, False, True
    return {"display": "block"}, {"display": "none"}, True, False
