"""Terminal concession liquidation section (Year 12 contractual handback)."""

from dash import html

from components import card, money, section


# SECTION: Contractual Liquidation (Year 12)
def build_terminal_liquidation_section(filtered):
    """Build the Year 12 terminal liquidation section when Year 12 is in the filter slice."""
    terminal = filtered[filtered.encerramento] if not filtered.empty else filtered
    if terminal.empty:
        return []

    terminal_tiles = [
        card(label, money(terminal[key].median()))
        for label, key in [
            ("Caixa inicial", "saldo_inicial_caixa"),
            ("Geração de caixa", "geracao_caixa"),
            ("Investimentos", "investimentos"),
            ("Distribuição ao acionista", "distribuicao_acionista"),
            ("Caixa final", "saldo_final_caixa"),
        ]
    ]
    return [
        section(
            "Liquidação contratual",
            "Prestação de contas do encerramento contratual e liquidação financeira no Ano 12 da concessão. "
            "Segrega a apuração extraordinária de reversão de ativos, quitação final de obrigações e desmobilização "
            "patrimonial da trajetória operacional recorrente do projeto.",
            [
                html.Div(terminal_tiles, className="metrics-grid"),
                html.P(
                    "Saldos liquidados não entram nas tendências operacionais. A base não detalha a destinação contratual de cada ativo.",
                    className="notice",
                ),
            ],
        )
    ]
