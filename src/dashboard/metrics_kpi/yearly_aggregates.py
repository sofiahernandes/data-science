"""Yearly median aggregations for multi-year time-series charts."""


# AGGREGATION: Yearly Medians Across Scenarios
def compute_yearly_medians(operating):
    """Compute annual median values for time-series charts across operating years."""
    if operating.empty:
        return operating

    return operating.groupby(["ano_num", "ano_calendario"], as_index=False).agg(
        receita=("receita", "median"),
        ebitda=("ebitda", "median"),
        margem_ebitda=("margem_ebitda", "median"),
        roe=("roe", "median"),
        liquidez_corrente=("liquidez_corrente", "median"),
        capital_terceiros=("participacao_capital_terceiros", "median"),
        eva=("eva", "median"),
        geracao_caixa=("geracao_caixa", "median"),
    )
