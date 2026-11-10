"""Shared UI components and value formatters for the Nour dashboard."""

from components.formatters import (
    brl,
    brl_signed,
    money,
    money_millions,
    percent,
    percent_points,
    ratio,
)
from components.ui import (
    build_export_button,
    build_statement_card,
    build_statement_filter_field,
    card,
    chart,
    insight,
    page_header,
    panel,
    row,
    section,
    variation_badge,
)

__all__ = [
    "brl",
    "brl_signed",
    "build_export_button",
    "build_statement_card",
    "build_statement_filter_field",
    "card",
    "chart",
    "insight",
    "money",
    "money_millions",
    "page_header",
    "panel",
    "percent",
    "percent_points",
    "ratio",
    "row",
    "section",
    "variation_badge",
]
