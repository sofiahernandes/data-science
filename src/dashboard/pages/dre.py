"""Income Statement (DRE — Demonstração do Resultado do Exercício) page.

Contains the DRE row schema, HTML table builder, page layout, Top-10 scenarios chart,
and Excel export callback in a single self-contained module.
"""

from dash import Input, Output, State, callback, dcc, html, no_update
import pandas as pd
import plotly.express as px

from components.formatters import brl_signed
from components.ui import (
    STATEMENT_CONTAINER_STYLE,
    STATEMENT_CONTENT_STYLE,
    STATEMENT_HEADER_CARD_STYLE,
    STATEMENT_SUBTITLE_STYLE,
    STATEMENT_TITLE_STYLE,
    build_statement_card,
    build_statement_filter_field,
)
from context import (
    DATA,
    SCENARIOS,
    YEARS,
    get_selected_scenarios,
    get_selected_years,
)
from exports import create_excel

# SCHEMA: DRE Accounting Lines
DRE_ROWS = (
    ("(+) Receita Bruta", "DRE Receita"),
    ("(-) Tributos", "DRE Tributos"),
    ("(-) Custos", "DRE Custos"),
    ("(-) Depreciação e Amortização", "DRE Depreciacao e Amortizacao"),
    ("(=) Resultado Operacional", "DRE Resultado Operacional"),
    ("(+) Receitas Financeiras", "DRE Receitas Financeiras"),
    ("(-) Despesas Financeiras", "DRE Despesas Financeiras"),
    ("(=) Resultado Financeiro", "DRE Resultado Financeiro"),
    ("( ) Outros Resultados Operacionais", "DRE Outros Resultados Operacionais"),
    (
        "(=) Resultado Antes do Imposto de Renda",
        "DRE Resultado Antes do Imposto de Renda",
    ),
    (
        "(-) Imposto de Renda e Contribuição Social",
        "DRE Imposto de Renda e Contribuicao Social",
    ),
    ("(=) Resultado Líquido", "DRE Resultado Liquido"),
    (
        "(=) Resultado Líquido após Equivalência",
        "DRE Resultado Liquido apos Equivalencia",
    ),
    ("( ) EBITDA", "DRE EBITDA"),
)


# TABLE: Vertical DRE Statement Table
def build_dre_table(dre_data):
    """Build the two-column DRE HTML table (Account Description + Consolidated Value)."""
    return html.Table(
        [
            html.Thead(
                html.Tr(
                    [
                        html.Th("Descrição da Conta", scope="col"),
                        html.Th("Valor Consolidado", scope="col"),
                    ]
                )
            ),
            html.Tbody(
                [
                    html.Tr(
                        [
                            html.Th(dre_row.get("conta", ""), scope="row"),
                            html.Td(
                                dre_row.get("valor", ""),
                                style={"textAlign": "right"},
                            ),
                        ],
                        className=(
                            "dfc-total"
                            if dre_row.get("conta", "").startswith("(=)")
                            or dre_row.get("conta") == "( ) EBITDA"
                            else ""
                        ),
                    )
                    for dre_row in dre_data
                ]
            ),
        ],
        className="dfc-table",
    )


# PAGE LAYOUT: DRE Page Container
def build_dre_page(years=YEARS, scenarios=SCENARIOS):
    """Build the DOM tree for the `/dre` page (header, DRE table, and Top-10 scenarios chart)."""
    header_card = html.Div(
        style=STATEMENT_HEADER_CARD_STYLE,
        children=[
            html.H2(
                "Demonstração do Resultado do Exercício (DRE)",
                style=STATEMENT_TITLE_STYLE,
            ),
            html.P(
                "Estrutura contábil da formação do resultado econômico. Detalha receitas, deduções, custos operacionais, despesas e tributos para mensurar a lucratividade líquida e o EBITDA da concessão.",
                style=STATEMENT_SUBTITLE_STYLE,
            ),
        ],
    )

    # Section 1: DRE Statement Table
    table_card = build_statement_card(
        "Tabela DRE",
        [html.Div(id="tabela-dre-dinamica", className="dfc-table-wrap")],
        export_button_id="export-dre-btn",
    )

    # Section 2: Top 10 Scenarios Line Chart
    top10_options = [
        {"label": "Resultado Líquido", "value": "DRE Resultado Liquido"},
        {"label": "EBITDA", "value": "DRE EBITDA"},
    ]
    chart_filters = html.Div(
        style={"display": "flex", "gap": "16px", "marginBottom": "16px"},
        children=[
            build_statement_filter_field(
                "Métrica de Avaliação",
                dcc.Dropdown(
                    id="grafico-filtro-metrica",
                    options=top10_options,
                    value=top10_options[0]["value"],
                    clearable=False,
                ),
                width="240px",
            )
        ],
    )
    chart_card = build_statement_card(
        "Melhores Cenários",
        [chart_filters, dcc.Graph(id="grafico-top10-cenarios")],
        title_color="var(--ink)",
    )

    return html.Div(
        id="dre-page",
        className="dre-page",
        style={"display": "none"},
        children=[
            dcc.Download(id="download-dre"),
            html.Div(
                style=STATEMENT_CONTAINER_STYLE,
                children=[
                    header_card,
                    html.Div(
                        style=STATEMENT_CONTENT_STYLE,
                        children=[table_card, chart_card],
                    ),
                ],
            ),
        ],
    )


# CALLBACK: Update DRE Table
@callback(
    Output("tabela-dre-dinamica", "children"),
    Input("years-input", "value"),
    Input("scenarios-input", "value"),
    Input("single-year-dropdown", "value"),
    Input("url", "pathname"),
)
def update_dre_table(years, scenarios, single_year_val, pathname):
    """Recompute the median DRE statement for the selected year and scenario range."""
    clean_path = (pathname or "/").rstrip("/") or "/"

    if clean_path == "/dre" and single_year_val is not None:
        target_year = int(single_year_val)
    else:
        selected_years = get_selected_years(years, YEARS)
        target_year = selected_years[0] if selected_years else min(YEARS)

    chosen_scenarios = get_selected_scenarios(scenarios, SCENARIOS)

    filtered_df = DATA[
        (DATA.ano_num == target_year) & DATA["Cenário"].isin(chosen_scenarios)
    ].copy()

    if filtered_df.empty:
        return build_dre_table([])

    median_row = filtered_df.median(numeric_only=True)

    dre_vertical = [
        {
            "conta": label,
            "valor": brl_signed(median_row.get(column, 0)),
        }
        for label, column in DRE_ROWS
    ]
    return build_dre_table(dre_vertical)


# CALLBACK: Update Top-10 Scenarios Line Chart
@callback(
    Output("grafico-top10-cenarios", "figure"),
    Input("single-year-dropdown", "value"),
    Input("years-input", "value"),
    Input("grafico-filtro-metrica", "value"),
)
def update_top10_scenarios_chart(single_year_val, years_input_val, selected_metric):
    """Build the Top-10 scenarios line chart for the selected year and DRE metric."""
    year_col = (
        "ano_num"
        if "ano_num" in DATA.columns
        else ("Ano" if "Ano" in DATA.columns else DATA.columns[0])
    )
    scenario_col = "Cenário" if "Cenário" in DATA.columns else DATA.columns[1]

    target_metric = selected_metric if selected_metric else "DRE Resultado Liquido"
    metric_label = (
        "Resultado Líquido" if target_metric == "DRE Resultado Liquido" else "EBITDA"
    )

    working_df = DATA.copy()

    if single_year_val is not None:
        effective_year = int(single_year_val)
    else:
        selected_years = get_selected_years(years_input_val, YEARS)
        effective_year = selected_years[0] if selected_years else 1

    working_df = working_df[working_df[year_col] == effective_year]

    if working_df.empty or target_metric not in working_df.columns:
        return px.line(title="Sem dados disponíveis para esta seleção")

    # Extract numeric scenario ID (without the "Cenário " prefix)
    scenario_num = (
        pd.to_numeric(
            working_df[scenario_col].astype(str).str.extract(r"(\d+)", expand=False),
            errors="coerce",
        )
        .fillna(0)
        .astype(int)
    )
    working_df["Cenario_Num"] = scenario_num.astype(str)

    # Sort descending and keep the top 10 scenarios
    top10 = working_df.sort_values(by=target_metric, ascending=False).head(10)

    fig = px.line(
        top10,
        x="Cenario_Num",
        y=target_metric,
        markers=True,
        text=top10[target_metric].apply(lambda v: f"{v:,.0f}".replace(",", ".")),
        labels={
            "Cenario_Num": "Cenário",
            target_metric: f"{metric_label} (R$)",
        },
    )

    fig.update_traces(
        line_color="#7a4665",
        line_width=3,
        marker=dict(size=10, color="#7a4665", symbol="circle"),
        textposition="top center",
    )

    # Keep the X axis ordered by the Top-10 ranking
    fig.update_xaxes(
        type="category",
        categoryorder="array",
        categoryarray=top10["Cenario_Num"].tolist(),
    )

    fig.update_layout(
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font_family="sans-serif",
        xaxis_title="Cenário",
        yaxis_title=f"{metric_label} (R$)",
        margin=dict(t=40, b=20, l=20, r=20),
    )

    return fig


# CALLBACK: Export DRE to Excel
@callback(
    Output("download-dre", "data"),
    Input("export-dre-btn", "n_clicks"),
    State("years-input", "value"),
    State("scenarios-input", "value"),
    State("single-year-dropdown", "value"),
    State("url", "pathname"),
    prevent_initial_call=True,
)
def export_dre_excel(n_clicks, years, scenarios, single_year_val, pathname):
    """Generate and download the DRE Excel spreadsheet for the active selection."""
    if not n_clicks:
        return no_update

    clean_path = (pathname or "/").rstrip("/") or "/"

    if clean_path == "/dre" and single_year_val is not None:
        target_year = int(single_year_val)
    else:
        selected_years = get_selected_years(years, YEARS)
        target_year = selected_years[0] if selected_years else min(YEARS)

    chosen_scenarios = get_selected_scenarios(scenarios, SCENARIOS)

    filtered_df = DATA[
        (DATA.ano_num == target_year) & DATA["Cenário"].isin(chosen_scenarios)
    ].copy()

    median_row = filtered_df.median(numeric_only=True)

    rows = []
    for label, column in DRE_ROWS:
        value = median_row.get(column, 0)
        if pd.isna(value):
            value = 0.0
        rows.append(
            {
                "valores": [label, float(value)],
                "tipo": (
                    "total"
                    if label.startswith("(=)") or label == "( ) EBITDA"
                    else "item"
                ),
            }
        )

    workbook_bytes = create_excel(
        "Demonstração do Resultado do Exercício",
        f"Ano {target_year} | Mediana de {len(chosen_scenarios)} cenário(s)",
        ["Descrição da Conta", "Valor Consolidado"],
        rows,
        "DRE",
    )

    return dcc.send_bytes(workbook_bytes, f"DRE_Ano_{target_year}.xlsx")
