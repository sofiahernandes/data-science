"""Nour Financial Dashboard — Application Entrypoint & Global Callbacks.

See `src/dashboard/README.md` for a quick guide on how to edit or remove a graph,
customize a perspective page, or add a new route.
"""

import os
from pathlib import Path
import sys

# Ensure both `src/dashboard` and `src/` are importable regardless of working directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dash import Dash, Input, Output, State, ctx, html, no_update

from config import (
    METRIC_LABELS,
    PERSPECTIVE_METRICS,
    PERSPECTIVE_SUMMARIES,
    PERSPECTIVES,
)
from context import (
    DATA,
    SCENARIOS,
    YEARS,
    build_context,
    get_selected_years,
    parse_selection_string,
)
from layout import create_main_layout, resolve_route_visibility

# Import page modules (statement pages register their own `@callback` handlers on import)
from pages import (  # noqa: F401
    balanco as balanco_page,
    dfc as dfc_page,
    dre as dre_page,
    investors as investors_page,
    management as management_page,
    technical as technical_page,
)

# Map each perspective key to its page module
PERSPECTIVE_RENDERERS = {
    "gestao": management_page.render,
    "tecnica": technical_page.render,
    "investidores": investors_page.render,
}

# DASH APPLICATION INITIALIZATION
ASSETS_DIR = Path(__file__).parent / "assets"

app = Dash(
    __name__,
    title="Nour | Painel financeiro",
    assets_folder=str(ASSETS_DIR),
    suppress_callback_exceptions=True,
)
app._favicon = "favicon.ico"

server = app.server


@server.route("/favicon.ico")
def serve_favicon():
    """Serve the custom brand favicon at the root `/favicon.ico` and `/_favicon.ico` paths."""
    return (
        (ASSETS_DIR / "favicon.ico").read_bytes(),
        200,
        {"Content-Type": "image/x-icon"},
    )


app._serve_default_favicon = serve_favicon


@server.route("/dre")
@server.route("/dre/")
@server.route("/dfc")
@server.route("/dfc/")
@server.route("/balanco")
@server.route("/balanco/")
@server.route("/dashboard")
@server.route("/dashboard/")
def serve_spa(*args, **kwargs):
    """Support direct URL access and browser refreshes on SPA routes."""
    return app.index(*args, **kwargs)


app.layout = create_main_layout(
    YEARS, SCENARIOS, PERSPECTIVES, PERSPECTIVE_METRICS, METRIC_LABELS, DATA
)


# PERSPECTIVE DISPATCHER
def render_content(
    years, scenarios, selected_metric="margem_ebitda", perspective="gestao"
):
    """Build the filter context and delegate rendering to the active perspective page."""
    context = build_context(years, scenarios, selected_metric, perspective)

    if context.empty:
        return [
            html.Div("Escolha ao menos um ano e um cenário.", className="empty-state")
        ]

    renderer = PERSPECTIVE_RENDERERS.get(context.perspective, management_page.render)
    return renderer(context)


# CALLBACK: Sidebar Perspective -> Distribution Metric Options
@app.callback(
    Output("distribution-metric", "options"),
    Output("distribution-metric", "value"),
    Input("perspective", "value"),
)
def set_distribution_metrics(perspective):
    """Synchronize the metric dropdown options when the active perspective changes."""
    perspective = perspective if perspective in PERSPECTIVE_METRICS else "gestao"
    metrics = PERSPECTIVE_METRICS[perspective]
    return (
        [{"label": METRIC_LABELS[key], "value": key} for key in metrics],
        metrics[0],
    )


# CALLBACK: Sidebar Perspective -> Summary Note
@app.callback(
    Output("perspective-summary", "children"),
    Input("perspective", "value"),
)
def describe_perspective(perspective):
    """Update the explanatory subtitle below the perspective tabs in the sidebar."""
    return PERSPECTIVE_SUMMARIES.get(perspective, PERSPECTIVE_SUMMARIES["gestao"])


# CALLBACK: Bidirectional Years Slider & Text Input Sync
@app.callback(
    Output("years-input", "value"),
    Output("years", "value"),
    Input("years-input", "value"),
    Input("years", "value"),
    Input("url", "pathname"),
    prevent_initial_call=True,
)
def sync_years(input_val, slider_val, pathname):
    """Keep years slider and text input synchronized without circular updates."""
    triggered_id = ctx.triggered_id
    clean_path = (pathname or "/").rstrip("/") or "/"

    if triggered_id == "years-input":
        if not input_val:
            return no_update, no_update
        selected = get_selected_years(input_val, YEARS)
        if not selected:
            return no_update, no_update
        target_slider = [min(selected), max(selected)]
        if slider_val == target_slider:
            return no_update, no_update
        return no_update, target_slider

    if triggered_id in ("years", "url"):
        first, last = slider_val if slider_val else (min(YEARS), max(YEARS))
        if clean_path == "/dre":
            target_text = str(first)
        else:
            target_text = str(first) if first == last else f"{first}-{last}"

        if input_val == target_text:
            return no_update, no_update
        return target_text, no_update

    return no_update, no_update


# CALLBACK: Bidirectional Scenarios Slider & Text Input Sync
@app.callback(
    Output("scenarios-input", "value"),
    Output("scenarios", "value"),
    Input("scenarios-input", "value"),
    Input("scenarios", "value"),
    Input("url", "pathname"),
    prevent_initial_call=True,
)
def sync_scenarios(input_val, slider_val, pathname):
    """Keep scenarios slider and text input synchronized without circular updates."""
    triggered_id = ctx.triggered_id
    clean_path = (pathname or "/").rstrip("/") or "/"

    if triggered_id == "scenarios-input":
        if not input_val:
            return no_update, no_update
        nums = parse_selection_string(input_val)
        valid_nums = [n for n in nums if 1 <= n <= len(SCENARIOS)]
        if not valid_nums:
            return no_update, no_update
        target_slider = [min(valid_nums), max(valid_nums)]
        if slider_val == target_slider:
            return no_update, no_update
        return no_update, target_slider

    if triggered_id in ("scenarios", "url"):
        first, last = slider_val if slider_val else (1, len(SCENARIOS))
        if clean_path in ("/dfc", "/balanco"):
            target_text = str(first)
        else:
            target_text = str(first) if first == last else f"{first}-{last}"

        if input_val == target_text:
            return no_update, no_update
        return target_text, no_update

    return no_update, no_update


# CALLBACK: Main Dashboard Canvas Renderer
@app.callback(
    Output("dashboard-content", "children"),
    Input("years-input", "value"),
    Input("scenarios-input", "value"),
    Input("distribution-metric", "value"),
    Input("perspective", "value"),
)
def render(years, scenarios, selected_metric, perspective):
    """Render the active perspective page into `#dashboard-content`."""
    try:
        return render_content(years, scenarios, selected_metric, perspective)
    except Exception as error:
        app.logger.exception("Dashboard render failed")
        return [
            html.Div(
                f"Não foi possível montar os gráficos: {type(error).__name__}: {error}",
                className="empty-state",
            )
        ]


# CALLBACK: Simplified View Toggle (Clientside)
app.clientside_callback(
    """
    function(value) {
        var isSimplified = Array.isArray(value) && value.length > 0;
        if (typeof document !== 'undefined' && document.body) {
            document.body.classList.toggle('simplified-view-active', isSimplified);
        }
        return isSimplified;
    }
    """,
    Output("simplified-view-active-store", "data"),
    Input("toggle-simplified-view", "value"),
    prevent_initial_call=False,
)


# CALLBACK: Sidebar Collapse Toggle (Clientside)
app.clientside_callback(
    """
    function(n_clicks, isCollapsed) {
        if (n_clicks === undefined || n_clicks === null || n_clicks === 0) {
            return isCollapsed || false;
        }
        var nextState = !isCollapsed;
        if (typeof document !== 'undefined' && document.body) {
            document.body.classList.toggle('sidebar-collapsed', nextState);
        }
        return nextState;
    }
    """,
    Output("sidebar-collapsed-store", "data"),
    Input("toggle-sidebar-btn", "n_clicks"),
    State("sidebar-collapsed-store", "data"),
    prevent_initial_call=True,
)


# CALLBACK: URL Router (Page & Sidebar Visibility)
@app.callback(
    Output("dashboard-page", "style"),
    Output("dre-page", "style"),
    Output("dfc-page", "style"),
    Output("balanco-page", "style"),
    Output("sidebar-panel-perspective", "style"),
    Output("sidebar-panel-indicador", "style"),
    Output("years-row-label", "children"),
    Output("scenarios-row-label", "children"),
    Output("years-range-container", "style"),
    Output("single-year-container", "style"),
    Output("scenarios-range-container", "style"),
    Output("single-scenario-container", "style"),
    Output("tab-dashboard", "className"),
    Output("tab-dre", "className"),
    Output("tab-dfc", "className"),
    Output("tab-balanco", "className"),
    Input("url", "pathname"),
)
def display_page(pathname):
    """Toggle page containers and sidebar controls according to `layout.ROUTES`."""
    return resolve_route_visibility(pathname)


# SERVER-SIDE INITIAL HYDRATION
def _hydrate_dashboard_content(tree, content):
    """Pre-populate `#dashboard-content` at startup to avoid an initial empty flash."""
    if hasattr(tree, "id") and getattr(tree, "id") == "dashboard-content":
        tree.children = content
        return True
    children = getattr(tree, "children", None)
    if children:
        child_list = children if isinstance(children, list) else [children]
        for child in child_list:
            if _hydrate_dashboard_content(child, content):
                return True
    return False


_hydrate_dashboard_content(
    app.layout,
    render([min(YEARS), max(YEARS)], [1, len(SCENARIOS)], "margem_ebitda", "gestao"),
)


if __name__ == "__main__":
    app.run(debug=True)
