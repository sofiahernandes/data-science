"""Shared dataset singleton, filter parsing helpers, and page rendering context.

`build_context()` prepares the filtered DataFrame slice and metadata for the active
sidebar selection. Individual perspective pages receive this `DashboardContext` and
build only the charts and sections they actually display.
"""

from dataclasses import dataclass
from pathlib import Path
import re

import pandas as pd

from config import (
    COLORS,
    METRIC_LABELS,
    PERSPECTIVE_METRICS,
    PERSPECTIVES,
)
from data_loader import load_data

# DATASET INITIALIZATION (SINGLETON IN MEMORY)
ROOT = Path(__file__).resolve().parents[1]

DATA_PATH = next(
    (
        path
        for path in (
            ROOT / "data" / "processed" / "Dados_Formatados_CTI.csv",
            ROOT / "src" / "data" / "processed" / "Dados_Formatados_CTI.csv",
        )
        if path.exists()
    ),
    ROOT / "src" / "data" / "processed" / "Dados_Formatados_CTI.csv",
)

DATA = load_data(DATA_PATH)
YEARS = sorted(DATA.ano_num.unique())
SCENARIOS = sorted(DATA["Cenário"].dropna().unique())


# FILTER PARSING HELPERS
def parse_selection_string(text):
    """Parse a range/list selection string into a sorted list of integers.

    Examples:
        '12'       -> [12]
        '12-15'    -> [12, 13, 14, 15]
        '15-18;19' -> [15, 16, 17, 18, 19]
        '1, 2, 5-8'-> [1, 2, 5, 6, 7, 8]
    """
    if text is None:
        return []
    cleaned = str(text).replace(",", ";").replace("–", "-").replace("—", "-")
    tokens = [t.strip() for t in cleaned.split(";") if t.strip()]
    selected = set()
    for token in tokens:
        range_match = re.match(r"^(\d+)\s*-\s*(\d+)$", token)
        if range_match:
            start = int(range_match.group(1))
            end = int(range_match.group(2))
            if start <= end:
                selected.update(range(start, end + 1))
            else:
                selected.update(range(end, start + 1))
            continue
        num_match = re.match(r"^\d+$", token)
        if num_match:
            selected.add(int(num_match.group()))
            continue
    return sorted(selected)


def get_selected_years(years_val, all_years=YEARS):
    """Resolve a slider range, list, or text string into valid concession year numbers."""
    if isinstance(years_val, str):
        nums = parse_selection_string(years_val)
    elif isinstance(years_val, (list, tuple)):
        if (
            len(years_val) == 2
            and all(isinstance(x, (int, float)) for x in years_val)
            and years_val[0] in all_years
            and years_val[1] in all_years
        ):
            first, last = int(years_val[0]), int(years_val[1])
            nums = list(range(min(first, last), max(first, last) + 1))
        else:
            nums = [int(x) for x in years_val if str(x).isdigit()]
    else:
        return list(all_years)

    valid_set = set(all_years)
    result = set()
    for n in nums:
        if n in valid_set:
            result.add(n)
        elif (n - 2026) in valid_set:
            result.add(n - 2026)
    res_list = sorted(result)
    return res_list if res_list else list(all_years)


def get_selected_scenarios(scenarios_val, all_scenarios=SCENARIOS):
    """Resolve a slider range, list, or text string into valid scenario labels."""
    if isinstance(scenarios_val, str):
        nums = parse_selection_string(scenarios_val)
    elif isinstance(scenarios_val, (list, tuple)):
        if any(isinstance(x, str) and not x.isdigit() for x in scenarios_val):
            return [s for s in scenarios_val if s in all_scenarios]
        if len(scenarios_val) == 2 and all(
            isinstance(x, (int, float)) for x in scenarios_val
        ):
            first, last = int(scenarios_val[0]), int(scenarios_val[1])
            nums = list(range(min(first, last), max(first, last) + 1))
        else:
            nums = [int(x) for x in scenarios_val if str(x).isdigit()]
    else:
        return list(all_scenarios)

    if not nums:
        return list(all_scenarios)

    num_to_scen = {}
    for s in all_scenarios:
        m = re.search(r"\d+", str(s))
        if m:
            num_to_scen[int(m.group())] = s

    for idx, s in enumerate(all_scenarios, start=1):
        if idx not in num_to_scen:
            num_to_scen[idx] = s

    result = [num_to_scen[n] for n in nums if n in num_to_scen]
    return result if result else list(all_scenarios)


# PAGE RENDERING CONTEXT
@dataclass
class DashboardContext:
    """Filtered data slice and filter metadata passed to each perspective page."""

    filtered: pd.DataFrame
    operating: pd.DataFrame
    latest: pd.DataFrame
    prev: pd.DataFrame
    latest_year: int
    prev_year: int
    selected_years: list
    chosen_scenarios: list
    perspective: str
    selected_metric: str
    subtitle: str
    colors: dict
    metric_labels: dict

    @property
    def empty(self) -> bool:
        return self.filtered.empty

    def delta(self, metric: str):
        """Return the year-over-year median difference for `metric` (or None if unavailable)."""
        if (
            self.prev is None
            or self.prev.empty
            or metric not in self.latest.columns
            or metric not in self.prev.columns
        ):
            return None
        return self.latest[metric].median() - self.prev[metric].median()


def build_context(
    years,
    scenarios,
    selected_metric="margem_ebitda",
    perspective="gestao",
) -> DashboardContext:
    """Filter the master dataset and assemble the `DashboardContext` for a page render."""
    selected_years = get_selected_years(years, YEARS)
    chosen_scenarios = get_selected_scenarios(scenarios, SCENARIOS)
    perspective = perspective if perspective in PERSPECTIVES else "gestao"
    allowed_metrics = PERSPECTIVE_METRICS[perspective]
    selected_metric = (
        selected_metric if selected_metric in allowed_metrics else allowed_metrics[0]
    )

    filtered = DATA[
        DATA.ano_num.isin(selected_years) & DATA["Cenário"].isin(chosen_scenarios)
    ].copy()

    if filtered.empty:
        return DashboardContext(
            filtered=filtered,
            operating=filtered,
            latest=filtered,
            prev=filtered,
            latest_year=1,
            prev_year=0,
            selected_years=selected_years,
            chosen_scenarios=chosen_scenarios,
            perspective=perspective,
            selected_metric=selected_metric,
            subtitle="",
            colors=COLORS,
            metric_labels=METRIC_LABELS,
        )

    # Separate operating years from the terminal liquidation year (Year 12)
    operating = filtered[~filtered.encerramento]
    if operating.empty:
        operating = filtered

    latest_year = int(operating.ano_num.max())
    latest = operating[operating.ano_num.eq(latest_year)]
    prev_year = max(
        [y for y in selected_years if y < latest_year], default=latest_year - 1
    )
    prev = operating[operating.ano_num.eq(prev_year)]

    subtitle = " · ".join(
        [
            PERSPECTIVES[perspective],
            f"Ano {latest_year} ({2026 + latest_year})",
            f"{len(chosen_scenarios):,} cenários".replace(",", "."),
            "Mediana do Recorte",
        ]
    )

    return DashboardContext(
        filtered=filtered,
        operating=operating,
        latest=latest,
        prev=prev,
        latest_year=latest_year,
        prev_year=prev_year,
        selected_years=selected_years,
        chosen_scenarios=chosen_scenarios,
        perspective=perspective,
        selected_metric=selected_metric,
        subtitle=subtitle,
        colors=COLORS,
        metric_labels=METRIC_LABELS,
    )
