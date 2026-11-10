"""Reusable UI building blocks (cards, sections, charts, sidebar rows, statement cards).

All helpers are optional building blocks: individual pages can use them or compose
standard Dash `html` / `dcc` elements directly whenever a custom layout is needed.
"""

from dash import dcc, html
from dash_iconify import DashIconify
import pandas as pd

from components.formatters import money
from config import COLORS, FONT_STACK


# SIDEBAR CONTROL: Label + input row
def row(
    label,
    control,
    readout=None,
    label_id=None,
    control_id=None,
    dropdown_control=None,
    dropdown_id=None,
    range_id=None,
):
    """Build a two-column control row for the sidebar."""
    control_props = {"className": "row-control"}
    if control_id is not None:
        control_props["id"] = control_id
    right = [html.Div(control, **control_props)]
    if readout is not None:
        right.append(readout)

    range_props = {"className": "row-right"}
    if range_id is not None:
        range_props["id"] = range_id

    children = [
        html.Span(
            label,
            **({"id": label_id} if label_id else {"className": "row-label"}),
        ),
        html.Div(right, **range_props),
    ]
    if dropdown_control is not None:
        dropdown_props = {
            "className": "row-dropdown-container",
            "style": {"display": "none"},
        }
        if dropdown_id is not None:
            dropdown_props["id"] = dropdown_id
        children.append(html.Div(dropdown_control, **dropdown_props))

    return html.Div(children, className="row")


# SIDEBAR CONTROL: Collapsible <details> panel
def panel(
    title,
    children,
    open_by_default=True,
    id=None,
    style=None,
    className="panel",
    **kwargs,
):
    """Build a collapsible HTML5 <details> panel for sidebar grouping."""
    props = {
        "open": open_by_default,
        "className": className,
        **kwargs,
    }
    if id is not None:
        props["id"] = id
    if style is not None:
        props["style"] = style
    return html.Details(
        [html.Summary(title), html.Div(children, className="panel-body")],
        **props,
    )


# BADGE: Period-over-period variation pill
def variation_badge(value, suffix="", formatter=None):
    """Render a positive/negative/neutral delta pill badge."""
    if value is None or pd.isna(value):
        text = "Sem comparação"
        color_class = "badge-neutral"
    else:
        positive = value >= 0
        arrow = "↑" if positive else "↓"
        sign = "+" if positive else "-"

        if formatter == "money":
            formatted = money(abs(value)).replace("R$ ", "")
            text = f"{arrow} {sign}R$ {formatted}"
        else:
            formatted = f"{abs(value):.1f}".replace(".", ",")
            text = f"{arrow} {sign}{formatted} {suffix}".strip()

        color_class = "badge-positive" if positive else "badge-negative"

    return html.Div(text, className=f"investor-badge {color_class}")


# CARD: KPI metric tile
def card(
    label,
    value,
    delta=None,
    subtitle=None,
    icon=None,
    accent_color=None,
):
    """Build a KPI card with label, optional subtitle, icon, value, and variation badge."""
    icon_color = accent_color or COLORS.get("plum", "#501839")

    header_children = []
    if icon:
        header_children.append(
            html.Div(
                DashIconify(
                    icon=icon,
                    width=22,
                    height=22,
                    color=icon_color,
                ),
                className="metric-icon",
            )
        )

    text_children = [html.Div(label, className="metric-label")]
    if subtitle:
        text_children.append(html.Div(subtitle, className="metric-subtitle"))

    header_children.append(html.Div(text_children, className="metric-heading"))

    children = [
        html.Div(header_children, className="metric-header"),
        html.Div(value, className="metric-value"),
    ]

    if delta is not None and not pd.isna(delta):
        if abs(delta) < 1:
            children.append(variation_badge(delta * 100, suffix="p.p."))
        else:
            children.append(variation_badge(delta, formatter="money"))

    return html.Div(
        children,
        className="metric-card",
        style={"--metric-accent": icon_color},
    )


# SECTION: Titled dashboard content block
def section(title, subtitle, children, footer_desc=None):
    """Build a semantic content section with title, subtitle, and child elements."""
    elements = [
        html.Div([html.H2(title), html.P(subtitle, className="section-subtitle")]),
        *children,
    ]
    if footer_desc:
        elements.append(html.P(footer_desc, className="section-description"))
    return html.Section(elements, className="section")


# CHART: Styled Plotly figure wrapper
def chart(figure, class_name="chart-card"):
    """Apply unified theme tokens to a Plotly figure and wrap it in a card."""
    figure.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"family": FONT_STACK, "color": COLORS["ink"], "size": 12},
        title_font={"size": 15, "color": COLORS["ink"], "weight": "bold"},
        margin={"l": 48, "r": 20, "t": 56, "b": 44},
        legend_title_text="",
        legend={"font": {"size": 12}},
        hoverlabel={"font": {"family": FONT_STACK, "size": 12}},
    )
    figure.update_xaxes(gridcolor="#eeeeee", linecolor="#cfcfcf", zeroline=False)
    figure.update_yaxes(gridcolor="#eeeeee", linecolor="#cfcfcf", zeroline=False)
    return html.Div(
        dcc.Graph(figure=figure, config={"displayModeBar": False}, responsive=True),
        className=class_name,
    )


# INSIGHT: Narrative diagnosis card
def insight(title, text, tone="neutral"):
    """Build an analytical insight card with semantic tone ('neutral', 'positive', 'alert')."""
    return html.Div(
        [html.H3(title), html.P(text)],
        className=f"insight-card insight-{tone}",
    )


# PAGE HEADER: Top title banner card
def page_header(title, subtitle, margin_bottom="24px"):
    """Build the top header banner shared by perspective views, with the simplified-view toggle in the top-right corner."""
    return html.Div(
        className="statement-header-card",
        children=[
            html.H1(title, className="statement-title"),
            html.P(subtitle, className="statement-subtitle"),
        ],
        style={"marginBottom": margin_bottom},
    )


# STATEMENT HELPERS: DRE / DFC / Balance Sheet cards
STATEMENT_CONTAINER_STYLE = {
    "backgroundColor": "transparent",
    "display": "flex",
    "flexDirection": "column",
    "gap": "24px",
}

STATEMENT_HEADER_CARD_STYLE = {
    "backgroundColor": "var(--white)",
    "padding": "20px",
    "borderRadius": "var(--radius-lg)",
    "border": "1px solid #e2e8f0",
    "textAlign": "center",
    "boxShadow": "var(--shadow-sm)",
    "position": "relative",
    "overflow": "hidden",
}

STATEMENT_TITLE_STYLE = {
    "color": "var(--ink)",
    "margin": "0 0 8px 0",
    "fontWeight": "600",
    "fontFamily": "inherit",
    "fontSize": "1.75rem",
    "letterSpacing": "-0.025em",
    "lineHeight": "1.15",
}

STATEMENT_SUBTITLE_STYLE = {
    "opacity": "1",
    "margin": "0 auto",
    "fontSize": "0.95rem",
    "fontFamily": "inherit",
    "textWrap": "balance",
    "maxWidth": "760px",
    "lineHeight": "1.4",
}

STATEMENT_CONTENT_STYLE = {
    "display": "flex",
    "flexDirection": "column",
    "gap": "24px",
    "width": "100%",
}

STATEMENT_CARD_STYLE = {
    "backgroundColor": "rgba(255, 255, 255, 0.9)",
    "backdropFilter": "blur(20px) saturate(180%)",
    "WebkitBackdropFilter": "blur(20px) saturate(180%)",
    "borderRadius": "var(--radius-lg)",
    "border": "1px solid var(--line)",
    "padding": "24px",
    "boxShadow": "var(--shadow-sm)",
}

SECTION_TITLE_STYLE = {
    "color": "var(--ink)",
    "fontSize": "1.25rem",
    "marginBottom": "18px",
    "fontWeight": "600",
    "letterSpacing": "-0.02em",
    "fontFamily": "inherit",
}

FILTER_LABEL_STYLE = {
    "fontSize": "0.95rem",
    "color": "var(--ink)",
    "marginBottom": "6px",
    "display": "block",
}


def build_export_button(button_id):
    """Build the 'Exportar Excel' button for financial statement cards."""
    return html.Button(
        [
            DashIconify(icon="akar-icons:download", width=20, color="white"),
            html.Span("Exportar Excel"),
        ],
        id=button_id,
        n_clicks=0,
        className="export-excel-btn",
    )


def build_statement_filter_field(
    label: str, control, width: str = "220px", margin_bottom: str = None
):
    """Build a labeled filter control inside a financial statement card."""
    style = {"width": width}
    if margin_bottom:
        style["marginBottom"] = margin_bottom
    return html.Div(
        style=style,
        children=[
            html.Label(label, style=FILTER_LABEL_STYLE),
            control,
        ],
    )


def build_statement_card(
    title: str,
    children: list,
    title_color: str = None,
    export_button_id: str = None,
):
    """Build a card container with header title and optional Excel export button."""
    title_style = dict(SECTION_TITLE_STYLE)
    if title_color:
        title_style["color"] = title_color

    header = html.Div(
        [
            html.H3(title, style={**title_style, "marginBottom": "0"}),
            *([build_export_button(export_button_id)] if export_button_id else []),
        ],
        style={
            "display": "flex",
            "justifyContent": "space-between",
            "alignItems": "center",
            "gap": "16px",
            "marginBottom": "18px",
        },
    )

    return html.Div(
        style=STATEMENT_CARD_STYLE,
        children=[header, *children],
    )
