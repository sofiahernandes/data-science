"""Pure Plotly figure builders (`data -> go.Figure`).

Each function here builds one chart figure without Dash layout wrappers, so any page
can call the ones it needs and wrap them with `chart(...)` or `dcc.Graph(...)`.
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# CHART: Mean EVA by Concession Year (Bar)
def create_eva_figure(operating):
    """Build the mean EVA by year bar chart displaying concession years on the X axis."""
    if operating is None or operating.empty or "eva" not in operating.columns:
        fig = go.Figure()
        fig.update_layout(
            title="EVA Médio por Ano (Aguardando base de dados)",
            height=320,
            plot_bgcolor="white",
            paper_bgcolor="white",
        )
        return fig

    # Group by concession year and compute mean EVA in millions
    mean_eva = operating.groupby("ano_num")["eva"].mean() / 1_000_000
    years = [int(y) for y in mean_eva.index]

    fig = go.Figure(
        data=[
            go.Bar(
                x=years,
                y=mean_eva.values,
                marker_color="#501839",
                hovertemplate="<b>Ano %{x}</b><br>EVA Médio: R$ %{y:,.2f} mi<extra></extra>",
            )
        ]
    )
    fig.update_layout(
        title="EVA Médio por Ano (Criação de Valor)",
        xaxis_title="Ano da Concessão",
        yaxis_title="R$ milhões",
        height=320,
        margin=dict(l=40, r=20, t=40, b=30),
        plot_bgcolor="white",
        paper_bgcolor="white",
        xaxis=dict(
            type="category",  # Treat each year as a discrete category so all tick labels appear
            tickmode="linear",
        ),
    )
    return fig


# CHART: Revenue Area & EBITDA Line Trend
def create_trend_chart(by_year, colors):
    """Build the Revenue area chart with an overlaid EBITDA line trace."""
    trend = px.area(
        by_year,
        x="ano_calendario",
        y="receita",
        title="Receita ao longo da concessão",
        labels={"ano_calendario": "Ano calendário", "receita": "Receita"},
        color_discrete_sequence=[colors["teal"]],
    )
    trend.add_trace(
        go.Scatter(
            x=by_year.ano_calendario,
            y=by_year.ebitda,
            mode="lines+markers",
            name="EBITDA",
            line={"color": colors["amber"], "width": 3},
            marker={"size": 7},
        )
    )
    trend.update_yaxes(tickprefix="R$ ", tickformat="~s")
    return trend


# CHART: Monte Carlo Risk Probability Heatmap
def create_risk_chart(risk_long, risk_labels=None):
    """Build the Monte Carlo risk probability heatmap across calendar years."""
    if risk_long.empty:
        return go.Figure().update_layout(title="Mapa de risco · probabilidade por ano")

    risk_matrix = risk_long.pivot(
        index="Evento", columns="ano_calendario", values="Probabilidade"
    )

    risk_fig = px.imshow(
        risk_matrix,
        text_auto=".0%",
        color_continuous_scale=["white", "#501839"],
        title="Mapa de risco · probabilidade por ano",
        aspect="auto",
        labels=dict(x="Ano calendário", y="", color="Probabilidade"),
    )

    # Show every year on the X axis and hide the colorbar (cells already display values)
    risk_fig.update_xaxes(type="category")
    risk_fig.update_layout(coloraxis_showscale=False)

    return risk_fig


# CHART: EVA (Line) vs Cash Generation (Bars) Dual-Axis
def create_value_cash_chart(by_year, colors):
    """Build the dual-axis chart comparing Cash Generation (bars) and EVA (line)."""
    if by_year.empty:
        return go.Figure()
    value_fig = make_subplots(specs=[[{"secondary_y": True}]])

    value_fig.add_trace(
        go.Bar(
            x=by_year["ano_calendario"],
            y=by_year["geracao_caixa"],
            name="Geração de caixa",
            marker_color=colors.get("sky", "#55a9e8"),
        ),
        secondary_y=False,
    )
    value_fig.add_trace(
        go.Scatter(
            x=by_year["ano_calendario"],
            y=by_year["eva"],
            name="EVA",
            mode="lines+markers",
            line=dict(color=colors.get("plum", "#501839"), width=3),
        ),
        secondary_y=True,
    )

    value_fig.update_layout(
        title="EVA e Geração de caixa",
        plot_bgcolor="white",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    value_fig.update_xaxes(
        title_text="Ano calendário", type="category", showgrid=True, gridcolor="#e5e7eb"
    )
    value_fig.update_yaxes(
        tickprefix="R$ ",
        tickformat="~s",
        secondary_y=False,
        showgrid=True,
        gridcolor="#e5e7eb",
    )
    value_fig.update_yaxes(
        tickprefix="R$ ", tickformat="~s", secondary_y=True, showgrid=False
    )

    return value_fig


# CHART: Scenario Distribution Violin / Box Plot
def create_distribution_chart(operating, selected_metric, metric_labels, colors):
    """Build the violin and box plot showing scenario distribution by year."""
    distribution = px.violin(
        operating,
        x="ano_calendario",
        y=selected_metric,
        box=True,
        points=False,
        title=f"Densidade e distribuição dos cenários · {metric_labels.get(selected_metric, selected_metric)}",
        labels={
            "ano_calendario": "Ano calendário",
            selected_metric: metric_labels.get(selected_metric, selected_metric),
        },
        color_discrete_sequence=[colors.get("plum", "#501839")],
    )

    distribution.update_layout(plot_bgcolor="white")
    distribution.update_xaxes(type="category", showgrid=True, gridcolor="#e5e7eb")

    if selected_metric in {"margem_ebitda", "roa", "roe", "composicao_endividamento"}:
        distribution.update_yaxes(tickformat=".0%", showgrid=True, gridcolor="#e5e7eb")
    else:
        distribution.update_yaxes(showgrid=True, gridcolor="#e5e7eb")

    return distribution
