"""Dynamic narrative descriptions placed beneath dashboard charts."""

from dash import html
import pandas as pd

from components import money, percent, ratio


# HELPER: Metric-aware value formatter
def format_metric_val(val, metric_name):
    """Format numeric values according to the semantic type of `metric_name`."""
    if pd.isna(val):
        return "—"
    if metric_name == "eva" or metric_name in {
        "receita",
        "ebitda",
        "resultado_liquido",
        "geracao_caixa",
        "divida_total",
        "ativo_total",
        "patrimonio_liquido",
        "caixa",
    }:
        return money(val)
    if metric_name in {
        "margem_ebitda",
        "roa",
        "roe",
        "participacao_capital_terceiros",
        "composicao_endividamento",
        "imobilizacao_pl",
    }:
        return percent(val)
    if "liquidez" in metric_name:
        return ratio(val)
    if abs(val) >= 1000:
        return money(val)
    if abs(val) <= 1:
        return percent(val)
    return ratio(val)


# DESCRIPTION: Revenue & EBITDA Trend Chart
def get_trend_description(latest, prev, latest_year):
    """Build the dynamic narrative paragraph for the Revenue and EBITDA trend chart."""
    rec_val = latest.receita.median() if "receita" in latest.columns else 0
    ebitda_val = latest.ebitda.median() if "ebitda" in latest.columns else 0
    margem_val = (
        latest.margem_ebitda.median()
        if "margem_ebitda" in latest.columns
        else (ebitda_val / rec_val if rec_val else 0)
    )

    has_prev = prev is not None and not prev.empty
    delta_rec = (
        (rec_val - prev.receita.median())
        if has_prev and "receita" in prev.columns
        else None
    )
    delta_ebitda = (
        (ebitda_val - prev.ebitda.median())
        if has_prev and "ebitda" in prev.columns
        else None
    )

    cal_year = 2026 + latest_year

    if delta_rec is not None and delta_ebitda is not None:
        rec_dir = "expansão" if delta_rec >= 0 else "contração"
        ebitda_dir = "aumento" if delta_ebitda >= 0 else "redução"
        trend_text = (
            f"No Ano {latest_year} ({cal_year}), a concessão consolida receita mediana de {money(rec_val)} "
            f"({rec_dir} de {money(abs(delta_rec))} frente ao ano anterior) e EBITDA de {money(ebitda_val)} "
            f"({ebitda_dir} de {money(abs(delta_ebitda))}), mantendo margem operacional em {percent(margem_val)}. "
        )
    else:
        trend_text = (
            f"No Ano {latest_year} ({cal_year}), a concessão atinge receita mediana de {money(rec_val)} "
            f"com geração de EBITDA de {money(ebitda_val)}, estabelecendo uma margem operacional de {percent(margem_val)}. "
        )

    if margem_val >= 0.50:
        diagnosis = (
            "Esse desempenho evidencia forte ganho de escala operacional e alta eficiência de conversão do faturamento "
            "tarifário em resultado antes de amortizações e juros."
        )
    elif margem_val >= 0.20:
        diagnosis = (
            "A trajetória indica consistência operacional, com margens equilibradas e capacidade de absorção "
            "satisfatória dos custos operacionais correntes."
        )
    else:
        diagnosis = (
            "A compressão da margem sinaliza pressão proporcional de custos e despesas, "
            "demandando acompanhamento rigoroso do orçamento para preservar o resultado operacional."
        )

    return html.P(
        [
            html.Strong("Evolução Operacional e Margem: "),
            trend_text + diagnosis,
        ],
        className="chart-description",
    )


# DESCRIPTION: Cash Generation vs EVA Chart
def get_value_cash_description(latest, prev, latest_year):
    """Build the dynamic narrative paragraph for the Cash Generation vs EVA chart."""
    cash_val = latest.geracao_caixa.median() if "geracao_caixa" in latest.columns else 0
    eva_val = latest.eva.median() if "eva" in latest.columns else 0
    cal_year = 2026 + latest_year

    cash_status = "positiva" if cash_val >= 0 else "deficitária"
    eva_status = "criação" if eva_val >= 0 else "destruição"

    base_text = (
        f"No Ano {latest_year} ({cal_year}), a geração de caixa operacional mediana é {cash_status} em {money(cash_val)}, "
        f"enquanto o Valor Econômico Agregado (EVA) registra {eva_status} de valor de {money(eva_val)}. "
    )

    if cash_val >= 0 and eva_val >= 0:
        diagnosis = (
            "O alinhamento superavitário entre caixa e EVA comprova a maturidade do negócio: o projeto não apenas sustenta "
            "suas necessidades de liquidez corrente, mas também remunera os acionistas acima da taxa mínima de atratividade (WACC)."
        )
    elif cash_val >= 0 and eva_val < 0:
        diagnosis = (
            "Embora o caixa operacional preserve a solvência imediata da concessão, o EVA negativo evidencia que o retorno do capital "
            "investido ainda não cobre integralmente o custo de oportunidade (WACC), exigindo disciplina na alocação de novos investimentos."
        )
    elif cash_val < 0 and eva_val >= 0:
        diagnosis = (
            "A despeito da agregação de valor econômico, a geração de caixa deficitária aponta descasamento temporário de liquidez "
            "(pressão de capital de giro ou concentração de investimentos), recomendando suporte preventivo de tesouraria."
        )
    else:
        diagnosis = (
            "O duplo déficit — consumo de caixa operacional e destruição de valor econômico — impõe intervenção tática imediata para "
            "revisão de despesas de capital e recomposição da liquidez financeira."
        )

    return html.P(
        [
            html.Strong("Dinâmica de Caixa e Criação de Valor: "),
            base_text + diagnosis,
        ],
        className="chart-description",
    )


# DESCRIPTION: Monte Carlo Risk Heatmap
def get_risk_description(latest, risk, latest_year, perspective="gestao"):
    """Build the dynamic narrative paragraph for the Monte Carlo risk heatmap."""
    cal_year = 2026 + latest_year

    cash_risk, liquidity_risk, loss_risk, eva_risk = 0.0, 0.0, 0.0, 0.0
    if risk is not None and not risk.empty:
        risk_row = risk.loc[risk["ano_calendario"].eq(cal_year)]
        if not risk_row.empty:
            r = risk_row.iloc[0]
            cash_risk = float(r.get("caixa_negativo", 0.0))
            liquidity_risk = float(r.get("liquidez_critica", 0.0))
            loss_risk = float(r.get("prejuizo", 0.0))
            eva_risk = float(r.get("eva_negativo", 0.0))

    if perspective == "tecnica":
        liq_val = (
            latest.liquidez_corrente.median()
            if "liquidez_corrente" in latest.columns
            else 0
        )
        liq_status = "confortável (≥ 1,0x)" if liq_val >= 1 else "em estresse (< 1,0x)"
        risk_text = (
            f"No Ano {latest_year} ({cal_year}), a liquidez corrente mediana situa-se em {ratio(liq_val)} ({liq_status}). "
            f"A matriz de estresse calcula probabilidade de {liquidity_risk:.0%} para quebra de liquidez (< 1,0x), "
            f"{cash_risk:.0%} para caixa a descoberto e {loss_risk:.0%} para resultado contábil negativo. "
        )
        if liquidity_risk >= 0.15 or cash_risk >= 0.15:
            conclusion = (
                "A expressiva probabilidade de eventos críticos requer governança reforçada da tesouraria, monitoramento diário do fluxo projetado "
                "e negociação prévia de linhas de crédito rotativo para resguardar a solvência de curto prazo."
            )
        else:
            conclusion = (
                "A reduzida probabilidade de quebra atesta solidez prudencial, garantindo margem técnica adequada para cumprimento "
                "das obrigações correntes e respeito integral aos limites normativos."
            )
        return html.P(
            [
                html.Strong("Mapeamento de Risco e Solvência Prudencial: "),
                risk_text + conclusion,
            ],
            className="chart-description",
        )

    # Default perspective: management ('gestao')
    risk_text = (
        f"No Ano {latest_year} ({cal_year}), as simulações probabilísticas apontam {cash_risk:.0%} de cenários com caixa negativo, "
        f"{liquidity_risk:.0%} sob liquidez crítica (< 1,0x), {loss_risk:.0%} em prejuízo contábil e {eva_risk:.0%} em destruição de valor (EVA negativo). "
    )
    if cash_risk >= 0.15 or liquidity_risk >= 0.20:
        conclusion = (
            "A concentração de cenários com déficit financeiro alerta para a necessidade de planos de contingência executivos, "
            "preservação de colchão de segurança e disciplina estrita na liberação de desembolsos discricionários."
        )
    else:
        conclusion = (
            "O reduzido risco de déficit financeiro nos cenários modelados comprova a estabilidade do fluxo operacional "
            "e respalda a execução com segurança do planejamento plurianual da concessão."
        )

    return html.P(
        [
            html.Strong("Diagnóstico Estocástico de Risco: "),
            risk_text + conclusion,
        ],
        className="chart-description",
    )


# DESCRIPTION: Scenario Distribution Violin / Box Plot
def get_distribution_description(
    latest, selected_metric, metric_labels, latest_year, perspective="gestao"
):
    """Build the dynamic narrative paragraph for the scenario distribution chart."""
    cal_year = 2026 + latest_year
    metric_name = metric_labels.get(selected_metric, selected_metric)

    values = (
        latest[selected_metric].dropna()
        if (selected_metric in latest.columns and not latest.empty)
        else pd.Series([0])
    )

    if values.empty:
        return html.P(
            "Sem dados disponíveis para a métrica selecionada.",
            className="chart-description",
        )

    p10, p25, p50, p75, p90 = values.quantile([0.10, 0.25, 0.50, 0.75, 0.90])
    iqr = p75 - p25

    p50_fmt = format_metric_val(p50, selected_metric)
    p10_fmt = format_metric_val(p10, selected_metric)
    p25_fmt = format_metric_val(p25, selected_metric)
    p75_fmt = format_metric_val(p75, selected_metric)
    p90_fmt = format_metric_val(p90, selected_metric)
    iqr_fmt = format_metric_val(iqr, selected_metric)

    if perspective == "tecnica":
        return html.P(
            [
                html.Strong(f"Dispersão Estatística e Solvência ({metric_name}): "),
                (
                    f"No Ano {latest_year} ({cal_year}), a métrica consolida mediana de {p50_fmt}. "
                    f"O miolo estatístico da simulação (intervalo interquartil Q1–Q3) abrange de {p25_fmt} a {p75_fmt} "
                    f"(amplitude interquartil de {iqr_fmt}). Os limites de cauda P10 e P90 registram {p10_fmt} e {p90_fmt}, "
                    "fornecendo referências quantitativas indispensáveis para testes de estresse prudenciais, calibração de limites operacionais e auditoria contábil."
                ),
            ],
            className="chart-description",
        )

    if perspective == "investidores":
        return html.P(
            [
                html.Strong(
                    f"Sensibilidade de Retorno sob Incerteza ({metric_name}): "
                ),
                (
                    f"No Ano {latest_year} ({cal_year}), o indicador apresenta mediana de {p50_fmt}. "
                    f"A faixa central de 50% dos cenários simulados situa-se entre {p25_fmt} (Q1) e {p75_fmt} (Q3), "
                    f"enquanto o intervalo de confiança de 80% (P10 a P90) estende-se de {p10_fmt} a {p90_fmt}. "
                    "Essa amplitude quantifica o prêmio de risco do ativo e a probabilidade de flutuação dos retornos frente a oscilações macroeconômicas e operacionais."
                ),
            ],
            className="chart-description",
        )

    # Default perspective: management ('gestao')
    return html.P(
        [
            html.Strong(f"Dispersão Operacional dos Cenários ({metric_name}): "),
            (
                f"No Ano {latest_year} ({cal_year}), a mediana observada é de {p50_fmt}. "
                f"Metade dos cenários simulados (intervalo interquartil Q1–Q3) concentra-se entre {p25_fmt} e {p75_fmt} "
                f"(amplitude de {iqr_fmt}), e os cenários limítrofes P10 e P90 balizam o intervalo entre {p10_fmt} e {p90_fmt}. "
                "Essa variabilidade mensura o grau de previsibilidade das metas operacionais e orienta a margem de segurança na gestão dos contratos."
            ),
        ],
        className="chart-description",
    )
