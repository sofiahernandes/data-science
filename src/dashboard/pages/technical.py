"""Technical / Controllership ('Técnica') perspective page.

Each section is a standalone function below. To remove, reorder, or add a section on
this page, edit the list inside `render(ctx)`.
"""

from dash import html

from charts import create_distribution_chart, create_risk_chart
from components import chart, page_header, section
from metrics_kpi.chart_descriptions import (
    get_distribution_description,
    get_risk_description,
)
from metrics_kpi.dynamic_insights import compute_dynamic_insights
from metrics_kpi.risk_analysis import compute_risk_probabilities
from metrics_kpi.technical_control import build_technical_controls_tiles


# PAGE ENTRYPOINT: Technical View
def render(ctx):
    """Render the Technical ('Visão Técnica') dashboard perspective."""
    risk_long, risk_labels, risk = compute_risk_probabilities(ctx.operating)

    sections = [
        financial_health_section(ctx),
        control_readings_section(ctx, risk),
        financial_risk_section(ctx, risk_long, risk_labels, risk),
        scenario_distribution_section(ctx),
    ]

    return html.Div(
        [
            page_header("Visão Técnica", ctx.subtitle),
            html.Div(
                sections,
                className="technical-main-layout",
                style={"display": "flex", "flexDirection": "column", "gap": "24px"},
            ),
        ],
        className="statement-container",
        style={"paddingBottom": "40px"},
    )


# SECTION: Financial Health & Controls (KPI Tiles)
def financial_health_section(ctx):
    """Render liquidity, profitability, and solvency KPI cards."""
    tiles = build_technical_controls_tiles(ctx.latest, ctx.prev)
    return section(
        "Saúde financeira e controles",
        "Painel de controle contábil e auditoria financeira prudencial. "
        "Avalia a suficiência de liquidez corrente, os índices de cobertura de obrigações de curto prazo, "
        "a proporção de capital de terceiros frente aos recursos próprios e o retorno dos ativos operacionais (ROA) "
        "para garantir aderência a covenants e diretrizes de tesouraria.",
        [html.Div(tiles, className="metrics-grid")],
    )


# SECTION: Control Readings (Dynamic Insights)
def control_readings_section(ctx, risk):
    """Render automated compliance and solvency insight cards."""
    _, technical_insights, _ = compute_dynamic_insights(
        ctx.latest,
        ctx.prev,
        risk,
        ctx.latest_year,
        ctx.selected_metric,
        ctx.metric_labels,
    )
    return section(
        "Leituras para controle",
        "Alertas técnicos de conformidade e solvência patrimonial baseados na mediana e dispersão das projeções. "
        "Evidencia a margem de folga do capital circulante líquido, a dependência de passivos onerosos e a faixa de incerteza "
        "estatística para subsidiar o controle interno e a governança orçamentária.",
        [html.Div(technical_insights, className="insights-grid")],
    )


# SECTION: Financial Risk Matrix (Monte Carlo Heatmap)
def financial_risk_section(ctx, risk_long, risk_labels, risk):
    """Render the Monte Carlo risk probability heatmap and prudential description."""
    risk_fig = create_risk_chart(risk_long, risk_labels)
    desc_risk = get_risk_description(
        ctx.latest, risk, ctx.latest_year, perspective="tecnica"
    )
    return section(
        "Risco financeiro",
        "Matriz quantitativa de vulnerabilidade estrutural calibrada pelas simulações de Monte Carlo. "
        "Calcula a probabilidade empírica de rompimento de limites prudenciais, como liquidez abaixo de 1,0x, "
        "saldo de caixa descoberto, prejuízo contábil e destruição de valor, para embasar testes de estresse "
        "e dimensionamento de garantias.",
        [
            html.Div(
                [chart(risk_fig), desc_risk],
                className="chart-wrapper",
            )
        ],
    )


# SECTION: Scenario Distribution (Violin / Box Plot)
def scenario_distribution_section(ctx):
    """Render the continuous statistical distribution chart for the selected indicator."""
    distribution_fig = create_distribution_chart(
        ctx.operating, ctx.selected_metric, ctx.metric_labels, ctx.colors
    )
    desc_dist = get_distribution_description(
        ctx.latest,
        ctx.selected_metric,
        ctx.metric_labels,
        ctx.latest_year,
        perspective="tecnica",
    )
    return section(
        "Distribuição de cenários",
        "Distribuição estatística contínua, com Box Plot e Densidade de Violino, do indicador financeiro selecionado "
        "ao longo da concessão. Permite examinar a simetria de resultados, a amplitude interquartil (IQR) e os riscos "
        "de cauda, como outliers, para calibração de bandas de controle e limites de compliance.",
        [
            html.Div(
                [chart(distribution_fig), desc_dist],
                className="chart-wrapper",
            )
        ],
    )
