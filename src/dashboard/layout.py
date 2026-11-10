"""Top-level application shell: Navbar, Sidebar, Page Containers, and Route Table.

Adding or modifying a route only requires editing `ROUTES` below.
"""

import re

from dash import dcc, html

from components import panel, row
from pages.balanco import build_balanco_page
from pages.dfc import build_dfc_page
from pages.dre import build_dre_page

# ROUTE TABLE: Declarative Page & Sidebar Visibility
ROUTES = {
    "/": {
        "page": "dashboard-page",
        "tab": "tab-dashboard",
        "sidebar_panels": {"perspective", "indicador"},
        "years_mode": "range",
        "scenarios_mode": "range",
        "years_label": "Anos da concessão",
        "scenarios_label": "Cenários simulados",
    },
    "/dre": {
        "page": "dre-page",
        "tab": "tab-dre",
        "sidebar_panels": set(),
        "years_mode": "single",
        "scenarios_mode": "range",
        "years_label": "Ano da concessão",
        "scenarios_label": "Cenários simulados",
    },
    "/dfc": {
        "page": "dfc-page",
        "tab": "tab-dfc",
        "sidebar_panels": set(),
        "years_mode": "range",
        "scenarios_mode": "single",
        "years_label": "Anos da concessão",
        "scenarios_label": "Cenário simulado",
    },
    "/balanco": {
        "page": "balanco-page",
        "tab": "tab-balanco",
        "sidebar_panels": set(),
        "years_mode": "range",
        "scenarios_mode": "single",
        "years_label": "Anos da concessão",
        "scenarios_label": "Cenário simulado",
    },
}

ALL_PAGES = ("dashboard-page", "dre-page", "dfc-page", "balanco-page")
ALL_TABS = ("tab-dashboard", "tab-dre", "tab-dfc", "tab-balanco")


def resolve_route_visibility(pathname):
    """Look up `pathname` in `ROUTES` and return the styles/classes for all page and sidebar elements."""
    clean_path = (pathname or "/").rstrip("/") or "/"
    route = ROUTES.get(clean_path, ROUTES["/"])

    def page_style(page_id):
        if page_id != route["page"]:
            return {"display": "none"}
        return {} if page_id == "dashboard-page" else {"display": "block"}

    def show_if(condition):
        return {} if condition else {"display": "none"}

    def tab_class(tab_id):
        return (
            "nav-tab nav-link active" if tab_id == route["tab"] else "nav-tab nav-link"
        )

    return (
        *(page_style(p) for p in ALL_PAGES),
        show_if("perspective" in route["sidebar_panels"]),
        show_if("indicador" in route["sidebar_panels"]),
        route["years_label"],
        route["scenarios_label"],
        show_if(route["years_mode"] == "range"),
        show_if(route["years_mode"] == "single"),
        show_if(route["scenarios_mode"] == "range"),
        show_if(route["scenarios_mode"] == "single"),
        *(tab_class(t) for t in ALL_TABS),
    )


# NAVBAR: Top Navigation Bar & Sidebar Toggle
def build_navbar():
    """Build the sticky top navigation bar with route links and sidebar toggle button."""
    return html.Header(
        id="top-navbar",
        className="navbar top-navbar",
        children=[
            html.Nav(
                className="nav-links",
                children=[
                    dcc.Link(
                        "Dashboard",
                        href="/",
                        id="tab-dashboard",
                        className="nav-tab nav-link active",
                        title="Dashboard",
                    ),
                    dcc.Link(
                        "DRE",
                        href="/dre",
                        id="tab-dre",
                        className="nav-tab nav-link",
                        title="DRE",
                    ),
                    dcc.Link(
                        "DFC",
                        href="/dfc",
                        id="tab-dfc",
                        className="nav-tab nav-link",
                        title="DFC",
                    ),
                    dcc.Link(
                        "Balanço",
                        href="/balanco",
                        id="tab-balanco",
                        className="nav-tab nav-link",
                        title="Balanço Patrimonial",
                    ),
                ],
            ),
            html.Button(
                [
                    html.Span(className="toggle-sidebar-bar"),
                    html.Span(className="toggle-sidebar-bar"),
                    html.Span(className="toggle-sidebar-bar"),
                ],
                id="toggle-sidebar-btn",
                className="toggle-sidebar-btn",
                title="Abrir / Fechar barra lateral",
                n_clicks=0,
            ),
        ],
    )


# SIDEBAR: Perspective Tabs, Filters & Dataset Metadata
def build_sidebar(years, scenarios, perspectives, perspective_metrics, metric_labels):
    """Build the right-hand filter sidebar shared across all pages."""
    min_y, max_y = min(years), max(years)
    n_scenarios = len(scenarios)

    return html.Aside(
        className="sidebar",
        children=[
            # Brand header
            html.Div(
                [
                    html.Div("Nour", className="brand"),
                    html.Div(
                        dcc.Checklist(
                            id="toggle-simplified-view",
                            options=[
                                {
                                    "label": "Visão simplificada",
                                    "value": "simplified",
                                }
                            ],
                            value=[],
                            persistence=True,
                            persistence_type="session",
                            className="simplified-view-toggle",
                        ),
                        className="header-toggle-container",
                        title="Ocultar subtítulos e descrições dos gráficos para uma visualização simplificada",
                    ),
                ],
                className="brand-lockup",
            ),
            # Panel 1: Stakeholder perspective switcher (Dashboard only)
            panel(
                "Perspetiva",
                [
                    dcc.Tabs(
                        id="perspective",
                        value="gestao",
                        className="segmented",
                        parent_className="segmented-parent",
                        content_className="segmented-content",
                        children=[
                            dcc.Tab(
                                label=label,
                                value=key,
                                className="segment",
                                selected_className="segment--on",
                            )
                            for key, label in perspectives.items()
                        ],
                    ),
                    html.P(
                        list(perspectives.values())[0],
                        id="perspective-summary",
                        className="panel-note",
                    ),
                ],
                id="sidebar-panel-perspective",
            ),
            # Panel 2: Year and Monte Carlo scenario slice controls
            panel(
                "Recorte",
                [
                    row(
                        "Anos da concessão",
                        dcc.RangeSlider(
                            id="years",
                            min=min_y,
                            max=max_y,
                            step=1,
                            value=[min_y, max_y],
                            marks=None,
                            tooltip={"placement": "bottom"},
                        ),
                        dcc.Input(
                            id="years-input",
                            type="text",
                            value=f"{min_y}-{max_y}",
                            debounce=True,
                            className="readout-input",
                            placeholder=f"{min_y}-{max_y}",
                        ),
                        label_id="years-row-label",
                        control_id="years-slider-container",
                        range_id="years-range-container",
                        dropdown_control=dcc.Dropdown(
                            id="single-year-dropdown",
                            options=[{"label": f"Ano {y}", "value": y} for y in years],
                            value=min_y,
                            clearable=False,
                            className="dash-dropdown",
                        ),
                        dropdown_id="single-year-container",
                    ),
                    row(
                        "Cenários simulados",
                        dcc.RangeSlider(
                            id="scenarios",
                            min=1,
                            max=n_scenarios,
                            step=1,
                            value=[1, n_scenarios],
                            marks=None,
                            tooltip={"placement": "bottom"},
                        ),
                        dcc.Input(
                            id="scenarios-input",
                            type="text",
                            value=f"1-{n_scenarios}",
                            debounce=True,
                            className="readout-input",
                            placeholder=f"1-{n_scenarios}",
                        ),
                        label_id="scenarios-row-label",
                        control_id="scenarios-slider-container",
                        range_id="scenarios-range-container",
                        dropdown_control=dcc.Dropdown(
                            id="single-scenario-dropdown",
                            options=[
                                {
                                    "label": (
                                        f"Cenário {m.group()}"
                                        if (m := re.search(r"\d+", str(s)))
                                        else f"Cenário {idx}"
                                    ),
                                    "value": s,
                                }
                                for idx, s in enumerate(scenarios, start=1)
                            ],
                            value=scenarios[0] if scenarios else 1,
                            clearable=False,
                            className="dash-dropdown",
                        ),
                        dropdown_id="single-scenario-container",
                    ),
                ],
                id="sidebar-panel-recorte",
            ),
            # Panel 3: Distribution metric selector (Dashboard only)
            panel(
                "Indicadores",
                [
                    row(
                        "Distribuição",
                        dcc.Dropdown(
                            id="distribution-metric",
                            options=[
                                {"label": label, "value": key}
                                for key, label in metric_labels.items()
                                if key in perspective_metrics["gestao"]
                            ],
                            value="margem_ebitda",
                            clearable=False,
                        ),
                    )
                ],
                id="sidebar-panel-indicador",
            ),
            # Dataset provenance metadata
            html.Div(
                [
                    html.Dl(
                        [
                            html.Dt("Base"),
                            html.Dd("Dados formatados CTI"),
                            html.Dt("Atualização"),
                            html.Dd("Leitura direta do arquivo local"),
                            html.Dt("Cobertura"),
                            html.Dd(
                                f"{n_scenarios} cenários · {max_y - min_y + 1} anos"
                            ),
                        ],
                        className="meta-list",
                    )
                ],
                className="meta-list brand-lockup",
            ),
        ],
    )


# MAIN LAYOUT: Complete Application DOM Tree
def create_main_layout(
    years, scenarios, perspectives, perspective_metrics, metric_labels, data
):
    """Build the complete root layout tree (Navbar, Page Containers, and Sidebar)."""
    dashboard_div = html.Div(
        id="dashboard-page",
        className="dashboard",
        children=[
            html.Main(
                className="main",
                children=[
                    html.Div(
                        id="dashboard-content",
                        className="content",
                        style={"width": "100%", "boxSizing": "border-box"},
                    )
                ],
            ),
        ],
    )

    return html.Div(
        className="app-container",
        children=[
            dcc.Location(id="url", refresh=False),
            dcc.Store(id="simplified-view-active-store"),
            dcc.Store(id="sidebar-collapsed-store", data=False),
            build_navbar(),
            html.Div(
                className="pages-container",
                children=[
                    dashboard_div,
                    build_dre_page(years=years, scenarios=scenarios),
                    build_dfc_page(years=years, scenarios=scenarios, data=data),
                    build_balanco_page(years=years, scenarios=scenarios, data=data),
                ],
            ),
            build_sidebar(
                years, scenarios, perspectives, perspective_metrics, metric_labels
            ),
        ],
    )
