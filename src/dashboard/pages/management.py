"""Management ('Gestão') perspective page.

Each section is a standalone function below. To remove, reorder, or add a section on
this page, edit the list inside `render(ctx)`.
"""

from dash import html

from charts import (
    create_distribution_chart,
    create_eva_figure,
    create_risk_chart,
    create_trend_chart,
    create_value_cash_chart,
)
from components import chart, page_header, section
from metrics_kpi.chart_descriptions import (
    get_distribution_description,
    get_risk_description,
    get_trend_description,
    get_value_cash_description,
)
from metrics_kpi.dynamic_insights import compute_dynamic_insights
from metrics_kpi.operational_overview import build_operational_overview_tiles
from metrics_kpi.risk_analysis import compute_risk_probabilities
from metrics_kpi.terminal_liquidation import build_terminal_liquidation_section
from metrics_kpi.yearly_aggregates import compute_yearly_medians


# PAGE ENTRYPOINT: Management View
def render(ctx):
    """Render the Management ('Visão do Gestor') dashboard perspective."""
    _, _, risk = compute_risk_probabilities(ctx.operating)

    sections = [
        operational_summary_section(ctx),
        management_readings_section(ctx, risk),
        eva_section(ctx),
        operation_tracking_section(ctx, risk),
        *build_terminal_liquidation_section(ctx.filtered),
        scenario_distribution_section(ctx),
    ]

    return html.Div(
        [
            page_header("Visão do Gestor", ctx.subtitle, margin_bottom="24px"),
            html.Div(
                sections,
                className="management-main-layout",
                style={"display": "flex", "flexDirection": "column"},
            ),
        ],
        className="statement-container",
        style={"paddingBottom": "40px"},
    )


# SECTION: Operational Summary (KPI Tiles)
def operational_summary_section(ctx):
    """Render top-level operational KPI cards (Revenue, EBITDA, Net Result, Cash, Debt)."""
    tiles = build_operational_overview_tiles(ctx.latest, ctx.prev)
    return section(
        "Resumo operacional",
        "Visão consolidada do desempenho econômico-financeiro no exercício selecionado. "
        "Apresenta faturamento bruto, margem operacional, lucro líquido, geração de caixa e perfil da dívida "
        "para avaliar a sustentabilidade do negócio e orientar decisões executivas de curto e médio prazo.",
        [html.Div(tiles, className="metrics-grid")],
    )


# SECTION: Management Readings (Dynamic Insights)
def management_readings_section(ctx, risk):
    """Render automated narrative insight cards for executive decision-making."""
    management_insights, _, _ = compute_dynamic_insights(
        ctx.latest,
        ctx.prev,
        risk,
        ctx.latest_year,
        ctx.selected_metric,
        ctx.metric_labels,
    )
    return section(
        "Leituras para gestão",
        "Diagnóstico executivo automatizado que cruza tração de receitas, eficiência operacional e risco de liquidez. "
        "Identifica desvios frente ao ciclo anterior e aponta sinais de alerta fundamentais para respaldar intervenções táticas da diretoria.",
        [html.Div(management_insights, className="insights-grid")],
    )


# SECTION: Value Creation (EVA Bar Chart)
def eva_section(ctx):
    """Render the annual Economic Value Added (EVA) bar chart."""
    eva_fig = create_eva_figure(ctx.operating)
    return section(
        "Criação de Valor (EVA)",
        "Análise evolutiva do Economic Value Added (EVA) ao longo da concessão, medindo a real criação de valor econômico acima do custo de capital.",
        [
            html.Div(
                [
                    html.Div(
                        [chart(eva_fig) if eva_fig else html.P("EVA indisponível")],
                        className="chart-wrapper",
                    )
                ],
                className="chart-grid",
            )
        ],
    )


# SECTION: Operation Tracking (Trend, EVA/Cash & Risk Charts)
def operation_tracking_section(ctx, risk):
    """Render Revenue/EBITDA trend, Cash vs EVA, and Monte Carlo risk heatmap."""
    by_year = compute_yearly_medians(ctx.operating)
    risk_long, risk_labels, _ = compute_risk_probabilities(ctx.operating)

    # Chart 1: Revenue & EBITDA trend
    trend_fig = create_trend_chart(by_year, ctx.colors)
    desc_trend = get_trend_description(ctx.latest, ctx.prev, ctx.latest_year)

    # Chart 2: Cash generation vs EVA
    value_fig = create_value_cash_chart(by_year, ctx.colors)
    desc_value = get_value_cash_description(ctx.latest, ctx.prev, ctx.latest_year)

    # Chart 3: Monte Carlo risk heatmap
    risk_fig = create_risk_chart(risk_long, risk_labels)
    desc_risk = get_risk_description(
        ctx.latest, risk, ctx.latest_year, perspective="gestao"
    )

    return section(
        "Acompanhamento da operação",
        "Monitoramento evolutivo e probabilístico da concessão ao longo dos anos. "
        "Compara a trajetória de expansão e margens operacionais, o confronto entre liquidez e criação de valor econômico "
        "e o mapeamento estocástico de riscos críticos.",
        [
            html.Div(
                [
                    html.Div([chart(trend_fig), desc_trend], className="chart-wrapper"),
                    html.Div([chart(value_fig), desc_value], className="chart-wrapper"),
                    html.Div([chart(risk_fig), desc_risk], className="chart-wrapper"),
                ],
                className="chart-grid",
            )
        ],
    )


# SECTION: Scenario Distribution (Violin / Box Plot)
def scenario_distribution_section(ctx):
    """Render the Monte Carlo scenario distribution violin/box plot."""
    distribution_fig = create_distribution_chart(
        ctx.operating, ctx.selected_metric, ctx.metric_labels, ctx.colors
    )
    desc_dist = get_distribution_description(
        ctx.latest,
        ctx.selected_metric,
        ctx.metric_labels,
        ctx.latest_year,
        perspective="gestao",
    )
    return section(
        "Distribuição de cenários",
        "Análise estocástica de sensibilidade e dispersão baseada nas iterações de Monte Carlo.",
        [
            html.Div(
                [chart(distribution_fig), desc_dist],
                className="chart-wrapper",
            )
        ],
    )
