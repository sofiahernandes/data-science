"""Cash Flow Statement (DFC — Demonstração dos Fluxos de Caixa) page.

Contains the DFC row schema, HTML table builder, page layout, table update callback,
and Excel export callback in a single self-contained module.
"""

from dash import Input, Output, State, callback, dcc, html, no_update
import pandas as pd

from components.formatters import brl
from components.ui import (
    STATEMENT_CONTAINER_STYLE,
    STATEMENT_CONTENT_STYLE,
    STATEMENT_HEADER_CARD_STYLE,
    STATEMENT_SUBTITLE_STYLE,
    STATEMENT_TITLE_STYLE,
    build_statement_card,
)
from context import (
    DATA,
    SCENARIOS,
    YEARS,
    get_selected_scenarios,
    get_selected_years,
)
from exports import create_excel

# SCHEMA: DFC Accounting Lines
DFC_ROWS = (
    ("Recebimentos de Receita", "FLU Receita"),
    ("(-) Tributos", "FLU Tributos"),
    ("(-) Custos", "FLU Custos"),
    ("(-) Investimentos", "FLU Investimentos"),
    ("Entradas Financeiras", "FLU Entradas"),
    ("(-) Despesas Financeiras", "FLU Despesas Financeiras"),
    ("Resultado Financeiro", "FLU Resultado Financeiro"),
    (
        "(-) Imposto de Renda e Contribuição Social",
        "FLU Imposto de Renda e Contribuicao Social",
    ),
    ("(-) Distribuição para Acionistas", "FLU Distribuicao para Acionista"),
    ("GERAÇÃO DE CAIXA", "FLU Geracao de Caixa"),
    ("Saldo Inicial de Caixa", "FLU Saldo Inicial"),
    ("Saldo Final de Caixa", "FLU Saldo Final"),
)


# TABLE: Multi-Year DFC Statement Table
def build_dfc_table(data, years, scenario):
    """Build the multi-year DFC HTML table for a single simulated scenario."""
    if isinstance(scenario, (list, tuple, set)):
        target_scenario = (
            next(iter(scenario))
            if len(scenario) > 0
            else (
                data["Cenário"].dropna().iloc[0]
                if "Cenário" in data.columns
                else "Cenário 1"
            )
        )
    else:
        target_scenario = scenario

    cash_flow = data.loc[data["Cenário"].eq(target_scenario)].set_index("Ano")
    columns = [f"Ano {year}" for year in years]

    return html.Table(
        [
            html.Thead(
                html.Tr(
                    [html.Th("Conta", scope="col")]
                    + [html.Th(year, scope="col") for year in columns]
                )
            ),
            html.Tbody(
                [
                    html.Tr(
                        [html.Th(label, scope="row")]
                        + [
                            html.Td(
                                brl(
                                    cash_flow.at[year, account]
                                    if (
                                        year in cash_flow.index
                                        and account in cash_flow.columns
                                    )
                                    else 0.0
                                )
                            )
                            for year in columns
                        ],
                        className=(
                            "dfc-total"
                            if account in {"FLU Geracao de Caixa", "FLU Saldo Final"}
                            else ""
                        ),
                    )
                    for label, account in DFC_ROWS
                ]
            ),
        ],
        className="dfc-table",
    )


# PAGE LAYOUT: DFC Page Container
def build_dfc_page(years=YEARS, scenarios=SCENARIOS, data=DATA):
    """Build the DOM tree for the `/dfc` page."""
    header_card = html.Div(
        style=STATEMENT_HEADER_CARD_STYLE,
        children=[
            html.H2(
                "Demonstração dos Fluxos de Caixa (DFC)",
                style=STATEMENT_TITLE_STYLE,
            ),
            html.P(
                "Mapeamento direto das entradas e saídas financeiras da concessão. Demonstra a geração de caixa operacional, dispêndios de Capex, serviço da dívida e saldo disponível para acionistas.",
                style=STATEMENT_SUBTITLE_STYLE,
            ),
        ],
    )

    table_card = build_statement_card(
        "Tabela DFC",
        [
            html.Div(
                build_dfc_table(data, years, scenarios),
                id="dfc-table-content",
                className="dfc-table-wrap",
            ),
        ],
        export_button_id="export-dfc-btn",
    )

    return html.Div(
        id="dfc-page",
        className="dfc-page",
        style={"display": "none"},
        children=[
            dcc.Download(id="download-dfc"),
            html.Div(
                style=STATEMENT_CONTAINER_STYLE,
                children=[
                    header_card,
                    html.Div(
                        style=STATEMENT_CONTENT_STYLE,
                        children=[table_card],
                    ),
                ],
            ),
        ],
    )


# CALLBACK: Update DFC Table
@callback(
    Output("dfc-table-content", "children"),
    Input("years-input", "value"),
    Input("scenarios-input", "value"),
    Input("single-scenario-dropdown", "value"),
    Input("url", "pathname"),
)
def render_dfc_table(years, scenarios, single_scenario_val, pathname):
    """Re-render the DFC table when selected years or scenario change."""
    clean_path = (pathname or "/").rstrip("/") or "/"
    selected_years = get_selected_years(years, YEARS)
    if clean_path == "/dfc" and single_scenario_val is not None:
        single_scenario = single_scenario_val
    else:
        chosen_scenarios = get_selected_scenarios(scenarios, SCENARIOS)
        single_scenario = chosen_scenarios[0] if chosen_scenarios else SCENARIOS[0]
    return build_dfc_table(DATA, selected_years, single_scenario)


# CALLBACK: Export DFC to Excel
@callback(
    Output("download-dfc", "data"),
    Input("export-dfc-btn", "n_clicks"),
    State("years-input", "value"),
    State("scenarios-input", "value"),
    State("single-scenario-dropdown", "value"),
    State("url", "pathname"),
    prevent_initial_call=True,
)
def export_dfc_excel(n_clicks, years, scenarios, single_scenario_val, pathname):
    """Generate and download the DFC Excel spreadsheet for the active selection."""
    if not n_clicks:
        return no_update

    clean_path = (pathname or "/").rstrip("/") or "/"
    selected_years = get_selected_years(years, YEARS)

    if clean_path == "/dfc" and single_scenario_val is not None:
        single_scenario = single_scenario_val
    else:
        chosen_scenarios = get_selected_scenarios(scenarios, SCENARIOS)
        single_scenario = chosen_scenarios[0] if chosen_scenarios else SCENARIOS[0]

    cash_flow = DATA.loc[DATA["Cenário"].eq(single_scenario)].set_index("Ano")
    year_columns = [f"Ano {year}" for year in selected_years]

    rows = []
    for label, account in DFC_ROWS:
        values = [label]
        for year_label in year_columns:
            val = (
                cash_flow.at[year_label, account]
                if year_label in cash_flow.index and account in cash_flow.columns
                else 0.0
            )
            if pd.isna(val):
                val = 0.0
            values.append(float(val))

        row_kind = (
            "total"
            if account in {"FLU Geracao de Caixa", "FLU Saldo Final"}
            else "item"
        )
        rows.append({"valores": values, "tipo": row_kind})

    workbook_bytes = create_excel(
        "Demonstração dos Fluxos de Caixa",
        f"Cenário: {single_scenario}",
        ["Descrição da Conta"] + year_columns,
        rows,
        "DFC",
    )

    return dcc.send_bytes(workbook_bytes, f"DFC_{single_scenario}.xlsx")
