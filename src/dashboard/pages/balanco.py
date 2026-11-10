"""Balance Sheet (Balanço Patrimonial) page.

Contains the Balance Sheet row schema, derived cell resolver, HTML table builder,
page layout, table update callback, and Excel export callback in a single module.
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

# SCHEMA: Balance Sheet Accounting Lines
BALANCO_ROWS = (
    ("ATIVO", "BAL Total do Ativo", "total"),
    ("1. ATIVO CIRCULANTE", None, "section"),
    ("Caixa e Equivalentes de Caixa", "BAL Disponivel", "item"),
    (
        "Contas a Receber (Partes Relacionadas)",
        "BAL Contas a Receber Partes Relacionadas",
        "item",
    ),
    ("Contas a Receber (Clientes)", "BAL Contas a Receber Clientes", "item"),
    ("Contas a Receber SWAP", "BAL Contas a Receber SWAP", "item"),
    ("Estoques", "BAL Estoques Diversos", "item"),
    ("Outros Créditos / Ativos Circulantes", "BAL Outros Creditos", "item"),
    ("TOTAL ATIVO CIRCULANTE", "BAL Ativo Circulante", "total"),
    ("2. ATIVO NÃO CIRCULANTE", None, "section"),
    ("Outorga da Concessão", "BAL Outorga da Concessao", "item"),
    ("Realizável a Longo Prazo", "BAL Realizavel a Longo Prazo", "item"),
    ("At Fiscal Diferido", "BAL At Fiscal Diferido", "item"),
    ("Créditos Tributários", "BAL Creditos Tributarios", "item"),
    ("Outros Créditos LP", "BAL Outros Creditos LP", "item"),
    ("Permanente", "BAL Permanente", "item"),
    ("Investimentos - Imobilizados", "BAL Investimentos Imobilizado", "item"),
    ("Investimentos - Intangível", "BAL Investimentos Intangivel", "item"),
    ("Diferido", "BAL Diferido", "item"),
    ("Depreciação Acumulada (Conta redutora)", "BAL Depreciacao Acumulada", "item"),
    (
        "Amortização - Intangível (Conta redutora)",
        "BAL Amortizacao Intangivel",
        "item",
    ),
    (
        "Amortização - Acumulada (Conta redutora)",
        "BAL Amortizacao Acumulada",
        "item",
    ),
    ("TOTAL ATIVO NÃO CIRCULANTE", "__TOTAL_ATIVO_NAO_CIRCULANTE__", "total"),
    ("PASSIVO E PATRIMÔNIO LÍQUIDO", "BAL Total do Passivo", "total"),
    ("1. PASSIVO CIRCULANTE", None, "section"),
    ("Fornecedores", "BAL Fornecedores", "item"),
    ("Empréstimos", "BAL Emprestimos", "item"),
    (
        "Obrigações Trabalhistas e Sociais",
        "BAL Encargos Sociais e Trabalhistas",
        "item",
    ),
    ("Tributos a pagar", "BAL Tributos a pagar", "item"),
    ("Contas a pagar", "BAL Tributos a pagar", "item"),
    ("Impostos a Recolher", "BAL Impostos", "item"),
    (
        "Obrigações com o Poder Concedente",
        "BAL Obrigacoes com o Poder Concedente",
        "item",
    ),
    ("Outros Débitos", "BAL Outros Debitos", "item"),
    ("Provisão Manutenção", "BAL Provisao Manutencao", "item"),
    ("Encargos Sociais e Trabalhistas", "BAL Tributos a pagar", "item"),
    ("TOTAL PASSIVO CIRCULANTE", "BAL Passivo Circulante", "total"),
    ("2. PASSIVO NÃO CIRCULANTE", None, "section"),
    ("Outros Débitos de longo prazo", "BAL Outros deb", "item"),
    (
        "Empréstimos e financiamentos bancários de longo prazo",
        "BAL Emprest",
        "item",
    ),
    ("Provisões para Contingências", "BAL Prov para Contingencias", "item"),
    ("TOTAL PASSIVO NÃO CIRCULANTE", "__TOTAL_PASSIVO_NAO_CIRCULANTE__", "total"),
    ("3. PATRIMÔNIO LÍQUIDO", None, "section"),
    ("Capital Social", "BAL Capital Social", "item"),
    ("Dividendos Antecipados", "BAL Dividendos Antecipados", "item"),
    ("Reservas de Capital", "BAL Reservas de Capital", "item"),
    ("Reservas Legais", "BAL Reservas Legais", "item"),
    ("Reserva de Retenção de Lucros", "BAL Reserva de Retencao de Lucros", "item"),
    ("Resultado Acumulado", "BAL Resultado Acumulado", "item"),
    ("Resultado do Período", "BAL Resultado do Periodo", "item"),
    ("TOTAL PATRIMÔNIO LÍQUIDO", "BAL Patrimonio Liquido", "total"),
)


# HELPER: Balance Sheet Cell Resolver
def balanco_cell_value(balance_sheet, year, account):
    """Resolve raw or synthetic subtotal cells for a given year and account key."""
    if year not in balance_sheet.index:
        return 0.0
    if account == "__TOTAL_ATIVO_NAO_CIRCULANTE__":
        total_assets = (
            balance_sheet.at[year, "BAL Total do Ativo"]
            if "BAL Total do Ativo" in balance_sheet.columns
            else 0.0
        )
        current_assets = (
            balance_sheet.at[year, "BAL Ativo Circulante"]
            if "BAL Ativo Circulante" in balance_sheet.columns
            else 0.0
        )
        return (0.0 if pd.isna(total_assets) else total_assets) - (
            0.0 if pd.isna(current_assets) else current_assets
        )
    if account == "__TOTAL_PASSIVO_NAO_CIRCULANTE__":
        parts = (
            (
                balance_sheet.at[year, "BAL Outros deb"]
                if "BAL Outros deb" in balance_sheet.columns
                else 0.0
            ),
            (
                balance_sheet.at[year, "BAL Emprest"]
                if "BAL Emprest" in balance_sheet.columns
                else 0.0
            ),
            (
                balance_sheet.at[year, "BAL Prov para Contingencias"]
                if "BAL Prov para Contingencias" in balance_sheet.columns
                else 0.0
            ),
        )
        return sum(0.0 if pd.isna(v) else v for v in parts)
    return balance_sheet.at[year, account] if account in balance_sheet.columns else 0.0


# TABLE: Multi-Year Balance Sheet Table
def build_balanco_table(data, years, scenario):
    """Build the multi-year Balance Sheet HTML table for a single simulated scenario."""
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

    balance_sheet = data.loc[data["Cenário"].eq(target_scenario)].set_index("Ano")
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
                        + (
                            [html.Td("") for _ in columns]
                            if kind == "section"
                            else [
                                html.Td(
                                    brl(
                                        balanco_cell_value(balance_sheet, year, account)
                                    )
                                )
                                for year in columns
                            ]
                        ),
                        className=("dfc-total" if kind in {"total", "section"} else ""),
                    )
                    for label, account, kind in BALANCO_ROWS
                ]
            ),
        ],
        className="dfc-table",
    )


# PAGE LAYOUT: Balance Sheet Page Container
def build_balanco_page(years=YEARS, scenarios=SCENARIOS, data=DATA):
    """Build the DOM tree for the `/balanco` page."""
    header_card = html.Div(
        style=STATEMENT_HEADER_CARD_STYLE,
        children=[
            html.H2("Balanço Patrimonial", style=STATEMENT_TITLE_STYLE),
            html.P(
                "Posição patrimonial e financeira da concessão ao final de cada exercício. Apresenta a composição dos ativos (circulante, realizável a longo prazo e permanente), passivos exigíveis e patrimônio líquido.",
                style=STATEMENT_SUBTITLE_STYLE,
            ),
        ],
    )

    table_card = build_statement_card(
        "Tabela Balanço Patrimonial",
        [
            html.Div(
                build_balanco_table(data, years, scenarios),
                id="balanco-table-content",
                className="dfc-table-wrap",
            ),
        ],
        export_button_id="export-balanco-btn",
    )

    return html.Div(
        id="balanco-page",
        className="balanco-page",
        style={"display": "none"},
        children=[
            dcc.Download(id="download-balanco"),
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


# CALLBACK: Update Balance Sheet Table
@callback(
    Output("balanco-table-content", "children"),
    Input("years-input", "value"),
    Input("scenarios-input", "value"),
    Input("single-scenario-dropdown", "value"),
    Input("url", "pathname"),
)
def render_balanco_table(years, scenarios, single_scenario_val, pathname):
    """Re-render the Balance Sheet table when selected years or scenario change."""
    clean_path = (pathname or "/").rstrip("/") or "/"
    selected_years = get_selected_years(years, YEARS)
    if clean_path == "/balanco" and single_scenario_val is not None:
        single_scenario = single_scenario_val
    else:
        chosen_scenarios = get_selected_scenarios(scenarios, SCENARIOS)
        single_scenario = chosen_scenarios[0] if chosen_scenarios else SCENARIOS[0]
    return build_balanco_table(DATA, selected_years, single_scenario)


# CALLBACK: Export Balance Sheet to Excel
@callback(
    Output("download-balanco", "data"),
    Input("export-balanco-btn", "n_clicks"),
    State("years-input", "value"),
    State("scenarios-input", "value"),
    State("single-scenario-dropdown", "value"),
    State("url", "pathname"),
    prevent_initial_call=True,
)
def export_balanco_excel(n_clicks, years, scenarios, single_scenario_val, pathname):
    """Generate and download the Balance Sheet Excel spreadsheet for the active selection."""
    if not n_clicks:
        return no_update

    clean_path = (pathname or "/").rstrip("/") or "/"
    selected_years = get_selected_years(years, YEARS)

    if clean_path == "/balanco" and single_scenario_val is not None:
        single_scenario = single_scenario_val
    else:
        chosen_scenarios = get_selected_scenarios(scenarios, SCENARIOS)
        single_scenario = chosen_scenarios[0] if chosen_scenarios else SCENARIOS[0]

    balance_sheet = DATA.loc[DATA["Cenário"].eq(single_scenario)].set_index("Ano")
    year_columns = [f"Ano {year}" for year in selected_years]

    rows = []
    for label, account, kind in BALANCO_ROWS:
        values = [label]
        for year_label in year_columns:
            if kind == "section":
                values.append(None)
                continue
            val = balanco_cell_value(balance_sheet, year_label, account)
            if pd.isna(val):
                val = 0.0
            values.append(float(val))

        rows.append({"valores": values, "tipo": kind})

    workbook_bytes = create_excel(
        "Balanço Patrimonial",
        f"Cenário: {single_scenario}",
        ["Descrição da Conta"] + year_columns,
        rows,
        "Balanço",
    )

    return dcc.send_bytes(workbook_bytes, f"Balanco_{single_scenario}.xlsx")
