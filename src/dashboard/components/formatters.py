"""Number and currency formatters for Brazilian Portuguese (pt-BR) display."""

import pandas as pd


# FORMATTER: Compact currency (R$ mi / bi)
def money(value):
    """Format numeric values into Brazilian Real (R$) with magnitude suffix.

    Values >= 1 billion format as 'R$ X,XX bi'.
    Values < 1 billion format as 'R$ X,XX mi'.
    Missing values return '—'.
    """
    if pd.isna(value):
        return "—"
    scale, suffix = (1e9, "bi") if abs(value) >= 1e9 else (1e6, "mi")
    return (
        f"R$ {value / scale:,.2f} {suffix}".replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


# FORMATTER: Compact currency in millions (1 decimal)
def money_millions(value):
    """Format values >= 1M as 'R$ X,X mi' (one decimal place), fallback to money()."""
    if value is None or pd.isna(value):
        return "—"
    if abs(value) >= 1_000_000:
        formatted = f"{value / 1_000_000:,.1f}"
        formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
        return f"R$ {formatted} mi"
    return money(value)


# FORMATTER: Full currency with accounting parentheses
def brl(value):
    """Format exact currency in pt-BR, wrapping negatives in parentheses: 'R$ (1.234,56)'."""
    if pd.isna(value):
        return "—"
    value = float(value)
    formatted = (
        f"{abs(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    )
    if value < 0:
        return f"R$ ({formatted})"
    return f"R$ {formatted}"


# FORMATTER: Full currency with minus sign (DRE)
def brl_signed(value):
    """Format exact currency in pt-BR with leading minus sign for negatives."""
    if pd.isna(value):
        return "R$ 0,00"
    text = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {text}"


# FORMATTER: Decimal ratio to percentage (0.154 -> '15,4%')
def percent(value):
    """Format decimal floats (e.g. 0.154) as pt-BR percentage strings ('15,4%')."""
    return "—" if pd.isna(value) else f"{value:.1%}".replace(".", ",")


# FORMATTER: Percentage points (15.4 -> '15,4%')
def percent_points(value):
    """Format already-scaled percentage numbers (0–100) as '15,4%'."""
    if value is None or pd.isna(value):
        return "—"
    return f"{value:.1f}%".replace(".", ",")


# FORMATTER: Coverage multiple (1.76 -> '1,76x')
def ratio(value):
    """Format coverage multiples (e.g. 1.76 -> '1,76x') using pt-BR comma decimal."""
    return "—" if pd.isna(value) else f"{value:.2f}x".replace(".", ",")
