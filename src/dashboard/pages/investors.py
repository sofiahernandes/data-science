"""Investor ('Investidores') perspective page.

Each section and custom panel is a standalone function with a banner comment so any
colleague can locate, edit, or remove a specific graph without touching other files.
"""

from dash import dcc, html
from dash_iconify import DashIconify
import pandas as pd
import plotly.graph_objects as go

from components import card, money, money_millions, page_header, percent_points


# PAGE ENTRYPOINT: Investor View
def render(ctx):
    """Render the Investor ('Visão do Investidor') dashboard perspective."""
    return html.Div(
        [
            page_header(
                "Visão do Investidor",
                "Rentabilidade, geração de caixa e criação de valor para o capital investido.",
                margin_bottom="16px",
            ),
            investor_summary_section(ctx),
            investor_detailed_section(ctx),
        ],
        className="statement-container",
        style={"paddingBottom": "40px"},
    )


# SECTION: Investor Summary (Top KPI Cards)
def investor_summary_section(ctx):
    """Render the four headline investor KPI cards (Net Profit, Net Revenue, Net Margin, Net Debt/EBITDA)."""
    metrics = _compute_investor_metrics(ctx.latest)
    prev_metrics = (
        _compute_investor_metrics(ctx.prev)
        if ctx.prev is not None and not ctx.prev.empty
        else {}
    )

    def calc_delta(curr, prev_val):
        if curr is None or prev_val is None or pd.isna(curr) or pd.isna(prev_val):
            return None
        return curr - prev_val

    net_profit = metrics.get("lucro_liquido", 0)
    net_revenue = metrics.get("receita_liquida", 0)
    net_margin = metrics.get("margem_liquida", 0)
    net_debt_ebitda = metrics.get("divida_ebitda", 0)

    investor_tiles = [
        card(
            "Lucro Líquido",
            money(net_profit),
            calc_delta(net_profit, prev_metrics.get("lucro_liquido")),
            subtitle="Resultado após despesas e impostos",
            icon="andrsrxn:wallet",
        ),
        card(
            "Receita Líquida",
            money(net_revenue),
            calc_delta(net_revenue, prev_metrics.get("receita_liquida")),
            subtitle="Receita após deduções e impostos",
            icon="cuida:sort-ascending-duotone",
        ),
        card(
            "Margem Líquida",
            f"{net_margin:.1f}%".replace(".", ","),
            calc_delta(net_margin, prev_metrics.get("margem_liquida")),
            subtitle="Rentabilidade líquida sobre a receita",
            icon="codicon:graph",
        ),
        card(
            "Dívida Líquida / EBITDA",
            f"{net_debt_ebitda:.1f}x".replace(".", ","),
            calc_delta(net_debt_ebitda, prev_metrics.get("divida_ebitda")),
            subtitle="Alavancagem financeira da operação",
            icon="codex:money",
        ),
    ]

    return html.Section(
        [
            html.H2("Resumo para o investidor"),
            html.P(
                "Visão consolidada dos principais indicadores de "
                "rentabilidade, resultado, margem e alavancagem "
                "financeira no período selecionado.",
                className="section-subtitle",
            ),
            html.Div(investor_tiles, className="metrics-grid"),
        ],
        className="section-investor",
    )


# SECTION: Detailed Investor View (4 Custom Panels)
def investor_detailed_section(ctx):
    """Render the 2x2 grid of custom investor panels and the closing analytical note."""
    # Top row: Performance Indicators (left) and Asset Composition (right)
    top_row = html.Div(
        [
            performance_panel(ctx.latest, ctx.prev),
            asset_composition_panel(ctx.latest),
        ],
        className="investor-top-grid",
    )

    # Bottom row: Result Evolution and Cash Flow stacked full-width
    bottom_row = html.Div(
        [
            evolution_result_panel(ctx.operating),
            cash_flow_panel(ctx.operating),
        ],
        className="investor-bottom-grid",
    )

    main_row = html.Div(
        [top_row, bottom_row],
        className="investor-main-layout",
        style={
            "width": "100%",
            "display": "flex",
            "flexDirection": "column",
            "gap": "24px",
        },
    )

    return html.Section(
        [
            html.H2("Visão detalhada"),
            html.P(
                "Acompanhamento da rentabilidade, evolução dos "
                "resultados, geração de caixa e composição patrimonial.",
                className="section-subtitle",
            ),
            main_row,
            html.P(
                [
                    html.Strong("Análise para o investidor: "),
                    (
                        "Os indicadores detalhados permitem avaliar "
                        "a capacidade de geração de resultado, o retorno "
                        "sobre o capital investido, a evolução da receita "
                        "e a sustentabilidade do fluxo de caixa ao longo "
                        "dos períodos analisados."
                    ),
                ],
                className="chart-description",
            ),
        ],
        className="section",
    )


# PANEL 1: Performance Indicators (Net Margin Gauge + ROE/ROIC/EBITDA)
def performance_panel(latest, prev):
    """Build the semicircular Net Margin gauge paired with ROE, ROIC, and EBITDA rows."""
    margin = _median_value(latest, "investor_margem_liquida")
    roe = _median_value(latest, "roe")
    roic = _median_value(latest, "roic")
    ebitda = _median_value(latest, "ebitda")

    margin_prev = _median_value(prev, "investor_margem_liquida")
    roe_prev = _median_value(prev, "roe")
    roic_prev = _median_value(prev, "roic")
    ebitda_prev = _median_value(prev, "ebitda")

    roe = roe * 100 if roe is not None else None
    roe_prev = roe_prev * 100 if roe_prev is not None else None
    roic = roic * 100 if roic is not None else None
    roic_prev = roic_prev * 100 if roic_prev is not None else None

    margin_delta = _calculate_variation(margin, margin_prev, percentage_points=True)
    roe_delta = _calculate_variation(roe, roe_prev, percentage_points=True)
    roic_delta = _calculate_variation(roic, roic_prev, percentage_points=True)
    ebitda_delta = _calculate_variation(ebitda, ebitda_prev)

    # Clamp gauge between 0% and 100% and map to semicircle (-180deg to 0deg)
    gauge_value = margin if margin is not None and not pd.isna(margin) else 0
    gauge_percent = max(0, min(100, gauge_value))
    needle_angle = -180 + (gauge_percent * 1.8)
    gauge_angle = gauge_percent * 1.8

    gauge = html.Div(
        [
            html.Div(
                [
                    html.Div(
                        className="gauge-arc",
                        style={
                            "background": (
                                f"conic-gradient("
                                f"from 270deg at 50% 100%, "
                                f"#a57592 0deg {gauge_angle}deg, "
                                f"#e5e7eb {gauge_angle}deg 180deg, "
                                f"transparent 180deg 360deg"
                                f")"
                            )
                        },
                        children=[html.Div(className="gauge-inner-cover")],
                    ),
                    html.Div(
                        className="gauge-needle",
                        style={"transform": f"rotate({needle_angle}deg)"},
                    ),
                    html.Div(className="gauge-needle-center"),
                    html.Span("0%", className="gauge-scale gauge-scale-min"),
                    html.Span("100%", className="gauge-scale gauge-scale-max"),
                ],
                className="gauge-meter",
            ),
            html.Div(percent_points(margin), className="gauge-value"),
            html.Div("Margem Líquida", className="gauge-label"),
            _investor_variation_badge(margin_delta, "p.p."),
        ],
        className="gauge-container",
    )

    indicators = [
        _performance_item(
            DashIconify(icon="lucide:trending-up", width=24, color="#501839"),
            "ROE",
            percent_points(roe),
            roe_delta,
            "p.p.",
            "#501839",
        ),
        _performance_item(
            DashIconify(icon="lucide:coins", width=24, color="#501839"),
            "ROIC",
            percent_points(roic),
            roic_delta,
            "p.p.",
            "#501839",
        ),
        _performance_item(
            DashIconify(icon="lucide:badge-dollar-sign", width=24, color="#501839"),
            "EBITDA",
            money_millions(ebitda),
            ebitda_delta,
            "%",
            "#501839",
        ),
    ]

    return html.Div(
        [
            html.Div(
                [
                    html.Span(
                        DashIconify(
                            icon="material-symbols:target",
                            width=20,
                            color="#501839",
                        ),
                        className="panel-header-icon",
                    ),
                    html.H3(
                        "Indicadores de Desempenho", className="panel-header-title"
                    ),
                ],
                className="panel-header",
            ),
            html.Div(
                [
                    html.Div(gauge, className="performance-gauge-wrapper"),
                    html.Div(className="performance-divider"),
                    html.Div(indicators, className="performance-indicators"),
                ],
                className="performance-body",
            ),
        ],
        className="performance-panel-container",
    )


# PANEL 2: Asset Composition (Donut Chart + Custom Legend)
def asset_composition_panel(data):
    """Build the Asset Composition donut chart and breakdown legend."""
    columns = [
        "BAL Ativo Circulante",
        "BAL Realizavel a Longo Prazo",
        "BAL Permanente",
    ]

    if data is None or data.empty:
        return html.Div("Dados insuficientes...", className="investor-panel")

    missing = [col for col in columns if col not in data.columns]
    if missing:
        return html.Div(
            f"Colunas não encontradas: {', '.join(missing)}",
            className="investor-panel",
        )

    df = data[columns].copy()
    for col in columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=columns)
    if df.empty:
        return html.Div("Valores indisponíveis...", className="investor-panel")

    current_assets = df["BAL Ativo Circulante"].median()
    long_term_receivables = df["BAL Realizavel a Longo Prazo"].median()
    permanent_assets = df["BAL Permanente"].median()

    labels = ["Ativo Circulante", "Realizavel a Longo Prazo", "Ativo Permanente"]
    values = [current_assets, long_term_receivables, permanent_assets]
    total = sum(values)

    if total <= 0 or any(pd.isna(v) or v < 0 for v in values):
        return html.Div("Valores inconsistentes...", className="investor-panel")

    colors = ["#501839", "#a57592", "#63aee7"]
    percentages = [(v / total) * 100 for v in values]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.70,
                sort=False,
                marker=dict(colors=colors),
                textinfo="none",
                hovertemplate="%{label}<br>Valor: R$ %{value:,.2f}<br>Participação: %{percent:.1%}<extra></extra>",
            )
        ]
    )

    fig.update_layout(
        height=260,
        showlegend=False,
        margin=dict(l=5, r=5, t=5, b=5),
        annotations=[
            dict(
                text=(
                    f"<b>{money_millions(total)}</b><br>"
                    "<span style='font-size:11px'>Total do Ativo</span>"
                ),
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=15, color="#111111"),
            )
        ],
    )

    legend_items = [
        html.Div(
            [
                html.Span(className="legend-dot", style={"backgroundColor": color}),
                html.Span(label, className="legend-label"),
                html.Span(
                    f"{pct:.1f}%".replace(".", ","),
                    className="legend-value",
                ),
            ],
            className="legend-item",
        )
        for label, pct, color in zip(labels, percentages, colors)
    ]

    return html.Div(
        [
            html.Div(
                [
                    DashIconify(
                        icon="energy-icons:chart-pie-slice-20",
                        width=20,
                        color="#501839",
                    ),
                    html.H3("Composição do Ativo", className="investor-panel-title"),
                ],
                className="panel-header",
                style={
                    "display": "flex",
                    "alignItems": "center",
                    "gap": "10px",
                    "marginBottom": "15px",
                },
            ),
            html.Div(
                [
                    dcc.Graph(
                        figure=fig,
                        config={"displayModeBar": False, "responsive": True},
                        className="investor-graph",
                        style={"height": "260px", "width": "100%"},
                    ),
                    html.Div(legend_items, className="legend-container"),
                ],
                className="asset-composition-grid",
            ),
        ],
        className="investor-panel",
    )


# PANEL 3: Result Evolution (Revenue / Net Profit / Margin Bar+Line)
def evolution_result_panel(data):
    """Build the multi-trace Result Evolution bar and line chart across concession years."""
    columns = [
        "Ano",
        "investor_receita_liquida",
        "investor_lucro_liquido",
        "investor_margem_liquida",
    ]

    if data is None or data.empty:
        return html.Div("Dados insuficientes...", className="investor-panel")

    missing = [col for col in columns if col not in data.columns]
    if missing:
        return html.Div(
            f"Colunas não encontradas: {', '.join(missing)}",
            className="investor-panel",
        )

    df = data[columns].copy()
    df["ano_num"] = pd.to_numeric(
        df["Ano"].astype(str).str.extract(r"(\d+)")[0],
        errors="coerce",
    )

    metric_cols = [
        "investor_receita_liquida",
        "investor_lucro_liquido",
        "investor_margem_liquida",
    ]
    for col in metric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = (
        df.dropna(subset=["ano_num"])
        .groupby("ano_num", as_index=False)[metric_cols]
        .median()
        .sort_values("ano_num")
    )

    if df.empty:
        return html.Div(
            "Não existem dados válidos para montar o gráfico.",
            className="investor-panel",
        )

    years = [f"Ano {int(y)}" for y in df["ano_num"]]
    revenue = df["investor_receita_liquida"] / 1_000_000
    net_profit = df["investor_lucro_liquido"] / 1_000_000
    margin = df["investor_margem_liquida"]

    # Nour brand palette (matches charts/__init__.py and style.css tokens)
    ink = "#111111"
    plum = "#501839"
    plum_weak = "#f1d6e6"
    sky = "#63aee7"
    grid_gray = "#e5e7eb"

    series_configs = [
        {
            "name": "Receita",
            "values": revenue,
            "yaxis_title": "R$ milhões",
            "hover_fmt": "R$ %{y:,.1f} mi",
        },
        {
            "name": "Lucro Líquido",
            "values": net_profit,
            "yaxis_title": "R$ milhões",
            "hover_fmt": "R$ %{y:,.1f} mi",
        },
        {
            "name": "Margem",
            "values": margin,
            "yaxis_title": "%",
            "hover_fmt": "%{y:.1f}%",
        },
    ]

    fig = go.Figure()
    for idx, cfg in enumerate(series_configs):
        fig.add_trace(
            go.Bar(
                x=years,
                y=cfg["values"],
                name=cfg["name"],
                marker=dict(
                    color=sky,
                    line=dict(color=sky, width=0),
                ),
                opacity=0.95,
                visible=(idx == 0),
                hovertemplate=f"<b>%{{x}}</b><br>{cfg['hover_fmt']}<extra></extra>",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=years,
                y=cfg["values"],
                name="Evolução",
                mode="lines+markers",
                line=dict(color=plum, width=3),
                marker=dict(
                    size=8,
                    color=plum,
                    line=dict(color=plum, width=2),
                ),
                visible=(idx == 0),
                hovertemplate=f"<b>%{{x}}</b><br>{cfg['hover_fmt']}<extra></extra>",
            )
        )

    buttons = []
    for idx, cfg in enumerate(series_configs):
        visibility = [False] * (len(series_configs) * 2)
        visibility[idx * 2] = True
        visibility[idx * 2 + 1] = True
        buttons.append(
            dict(
                label=cfg["name"],
                method="update",
                args=[
                    {"visible": visibility},
                    {"yaxis.title.text": cfg["yaxis_title"]},
                ],
            )
        )

    fig.update_layout(
        height=370,
        autosize=True,
        showlegend=False,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(
            family="Inter, Segoe UI, Arial, sans-serif",
            color=ink,
            size=12,
        ),
        margin=dict(l=55, r=25, t=70, b=45),
        xaxis=dict(
            title=dict(text="Anos", font=dict(color=ink, size=12)),
            showgrid=False,
            showline=True,
            linecolor="#d1d5db",
            linewidth=1,
            zeroline=False,
            tickfont=dict(color=ink, size=11),
        ),
        yaxis=dict(
            title=dict(text="R$ milhões", font=dict(color=ink, size=12)),
            rangemode="tozero",
            showgrid=True,
            gridcolor=grid_gray,
            gridwidth=1,
            showline=False,
            zeroline=False,
            tickfont=dict(color=ink, size=11),
        ),
        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                buttons=buttons,
                active=0,
                x=1,
                y=1.20,
                xanchor="right",
                yanchor="top",
                bgcolor=plum_weak,
                bordercolor=plum,
                borderwidth=1,
                font=dict(
                    family="Inter, Segoe UI, Arial, sans-serif",
                    color=plum,
                    size=11,
                ),
                pad=dict(l=8, r=8, t=6, b=6),
                showactive=True,
            )
        ],
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#ffffff",
            bordercolor=plum,
            font=dict(color=ink, size=12),
        ),
    )

    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Span(
                                DashIconify(
                                    icon="uis:graph-bar",
                                    width=24,
                                    color=plum,
                                ),
                                className="panel-header-icon",
                            ),
                            html.H3(
                                "Evolução do Resultado",
                                className="panel-header-title",
                            ),
                        ],
                        className="panel-header",
                    ),
                ],
                className="panel-header-wrapper",
            ),
            dcc.Graph(
                id="investor-evolution-chart",
                figure=fig,
                config={"displayModeBar": False, "responsive": True},
                style={"width": "100%", "height": "390px"},
            ),
        ],
        className="investor-panel",
    )


# PANEL 4: Cash Flow Breakdown (Operating / Investing / Financing Bars)
def cash_flow_panel(data):
    """Build the grouped bar chart comparing Operating, Investing, and Financing cash flows."""
    required_columns = [
        "FLU Geracao de Caixa",
        "FLU Investimentos",
        "FLU Entradas",
        "FLU Despesas Financeiras",
        "FLU Distribuicao para Acionista",
    ]

    if data is None or data.empty:
        return html.Div("Dados insuficientes...", className="investor-panel")

    missing = [col for col in required_columns if col not in data.columns]
    if missing:
        return html.Div(
            f"Colunas ausentes: {', '.join(missing)}", className="investor-panel"
        )

    df = data.copy()
    df["ano_num"] = pd.to_numeric(
        df.get("ano_num", df["Ano"].astype(str).str.extract(r"(\d+)")[0]),
        errors="coerce",
    )

    for col in required_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["ano_num"])
    if df.empty:
        return html.Div(
            "Não foi possível identificar os anos...", className="investor-panel"
        )

    df["Operacional"] = df["FLU Geracao de Caixa"]
    df["Investimento"] = df["FLU Investimentos"]
    df["Financiamento"] = (
        df["FLU Entradas"]
        + df["FLU Despesas Financeiras"]
        + df["FLU Distribuicao para Acionista"]
    )

    yearly = (
        df.groupby("ano_num")[["Operacional", "Investimento", "Financiamento"]]
        .median()
        .sort_index()
    )
    if yearly.empty:
        return html.Div(
            "Não existem dados para montar o gráfico.", className="investor-panel"
        )

    yearly = yearly / 1_000_000
    years = [f"Ano {int(y)}" for y in yearly.index]

    fig = go.Figure()
    series = [
        ("Operacional", "#501839"),
        ("Investimento", "#63aee7"),
        ("Financiamento", "#a57592"),
    ]

    for name, color in series:
        fig.add_trace(
            go.Bar(
                name=name,
                x=years,
                y=yearly[name],
                marker_color=color,
                hovertemplate=f"<b>{name}</b><br>%{{x}}<br>Valor: %{{y:.2f}} mi<extra></extra>",
            )
        )

    fig.update_layout(
        barmode="group",
        height=350,
        margin=dict(l=15, r=15, t=15, b=35),
        paper_bgcolor="white",
        plot_bgcolor="white",
        showlegend=False,
        font=dict(family="Arial", color="#111111", size=12),
        xaxis=dict(title=None, showgrid=True, gridcolor="#EDF1F5", zeroline=False),
        yaxis=dict(
            title=None,
            range=[-20, 40],
            tickmode="array",
            tickvals=[-20, 0, 20, 40],
            ticktext=["-20 mi", "0", "20 mi", "40 mi"],
            showgrid=True,
            gridcolor="#E8EDF2",
            zeroline=True,
            zerolinecolor="#64748B",
            zerolinewidth=1.5,
        ),
        bargap=0.25,
        bargroupgap=0.08,
    )

    legend = html.Div(
        [
            html.Div(
                [
                    html.Span(
                        className="legend-square", style={"backgroundColor": color}
                    ),
                    html.Span(name),
                ],
                className="legend-item-inline",
            )
            for name, color in series
        ],
        className="legend-inline-container",
    )

    return html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            html.Span(
                                DashIconify(
                                    icon="streamline:graph-arrow-increase",
                                    width=24,
                                    color="#501839",
                                ),
                                className="panel-header-icon",
                            ),
                            html.Span("Fluxo de Caixa", className="panel-header-title"),
                        ],
                        className="panel-header",
                    ),
                    legend,
                ],
                className="cashflow-header-wrapper",
            ),
            dcc.Graph(
                figure=fig,
                config={"displayModeBar": False},
                style={"width": "100%"},
            ),
        ],
        className="investor-panel cashflow-panel",
    )


# INTERNAL HELPERS (Investor View)
def _get_numeric_column(data, column):
    """Extract a numeric Series from `data`, raising ValueError if missing."""
    if column not in data.columns:
        raise ValueError(f"Coluna necessária não encontrada na base: {column}")
    return pd.to_numeric(data[column], errors="coerce")


def _compute_investor_metrics(data):
    """Compute median values for the four headline investor KPIs."""
    return {
        "lucro_liquido": _get_numeric_column(data, "investor_lucro_liquido").median(),
        "receita_liquida": _get_numeric_column(
            data, "investor_receita_liquida"
        ).median(),
        "margem_liquida": _get_numeric_column(data, "investor_margem_liquida").median(),
        "divida_ebitda": _get_numeric_column(data, "investor_divida_ebitda").median(),
    }


def _median_value(data, column):
    """Safely return the median of `column` in `data` (or None if empty/missing)."""
    if data is None or data.empty or column not in data.columns:
        return None
    values = pd.to_numeric(data[column], errors="coerce").dropna()
    if values.empty:
        return None
    return values.median()


def _calculate_variation(current, previous, percentage_points=False):
    """Compute relative (%) or percentage-point (p.p.) variation between two values."""
    if current is None or previous is None or pd.isna(current) or pd.isna(previous):
        return None
    if percentage_points:
        return current - previous
    if previous == 0:
        return None
    return ((current / previous) - 1) * 100


def _investor_variation_badge(value, suffix):
    """Render a variation pill badge with explicit suffix for the performance panel."""
    if value is None or pd.isna(value):
        text = "Sem comparação"
        color_class = "badge-neutral"
    else:
        positive = value >= 0
        arrow = "↑" if positive else "↓"
        color_class = "badge-positive" if positive else "badge-negative"
        formatted = f"{abs(value):.1f}".replace(".", ",")
        sign = "+" if positive else "-"
        text = f"{arrow} {sign}{formatted} {suffix}"

    return html.Div(text, className=f"investor-badge {color_class}")


def _performance_item(icon, label, value, variation, suffix, icon_color):
    """Render a single ROE / ROIC / EBITDA row inside the performance panel."""
    return html.Div(
        [
            html.Div(icon, className="performance-icon", style={"color": icon_color}),
            html.Div(
                [
                    html.Div(label, className="performance-label"),
                    html.Div(value, className="performance-value"),
                ],
                className="performance-text",
            ),
            _investor_variation_badge(variation, suffix),
        ],
        className="performance-item",
    )
