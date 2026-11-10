# Nour Dashboard — Developer & Editing Guide

This guide explains how the dashboard is organized and how to make common edits without breaking other pages.

---

## Folder Structure

```text
src/dashboard/
├── app.py                  # App entrypoint, URL router, and sidebar sync callbacks
├── config.py               # Color palette, metric labels, and perspective definitions
├── context.py              # Dataset singleton + `build_context()` filter state passed to pages
├── data_loader.py          # CSV ingestion and financial formula calculations
├── layout.py               # Navbar, sidebar, page containers, and `ROUTES` visibility table
├── assets/
│   └── style.css           # Unified stylesheet (automatically loaded by Dash)
├── components/
│   ├── formatters.py       # pt-BR formatters: `money`, `percent`, `ratio`, `brl`, `brl_signed`
│   └── ui.py               # Optional UI helpers: `card`, `section`, `chart`, `insight`, `page_header`
├── charts/
│   └── __init__.py         # Reusable Plotly figure builders (`data -> go.Figure`)
├── metrics_kpi/            # KPI tile builders, risk probabilities, and dynamic chart descriptions
├── exports/
│   └── excel.py            # `create_excel()` workbook generator for DRE, DFC, and Balance Sheet
└── pages/                  # Each page owns its own layout, sections, and callbacks!
    ├── management.py       # 'Gestão' perspective
    ├── technical.py        # 'Técnica' perspective
    ├── investors.py        # 'Investidores' perspective
    ├── dre.py              # '/dre' page (table + Top-10 chart + callbacks + Excel export)
    ├── dfc.py              # '/dfc' page (table + callbacks + Excel export)
    └── balanco.py          # '/balanco' page (table + callbacks + Excel export)
```

---

## Common Tasks

### 1. Find a specific graph or section

Every section and graph has a one-line banner comment that you can search with `Ctrl+F`:

- In Python (`pages/*.py`, `charts/__init__.py`, `metrics_kpi/*.py`):
  ```python
  # SECTION: Value Creation (EVA Bar Chart)
  ```
- In CSS (`assets/style.css`):
  ```css
  /* 9. INVESTOR PERSPECTIVE COMPONENTS */
  ```

### 2. Remove or reorder a section on a perspective page

Open the page file in `pages/` (`management.py`, `technical.py`, or `investors.py`) and edit the list inside `render(ctx)`. You do **not** need to touch `app.py` or any other file:

```python
# pages/management.py
def render(ctx):
    _, _, risk = compute_risk_probabilities(ctx.operating)

    sections = [
        operational_summary_section(ctx),
        management_readings_section(ctx, risk),
        eva_section(ctx),                  # <-- Delete or comment out this line to remove the EVA section
        operation_tracking_section(ctx, risk),
        *build_terminal_liquidation_section(ctx.filtered),
        scenario_distribution_section(ctx),
    ]
```

### 3. Add a custom graph or custom HTML structure to a page

Each page's `render(ctx)` receives a `DashboardContext` (`ctx`) with:

- `ctx.filtered`: DataFrame filtered by the selected years and scenarios (includes Year 12)
- `ctx.operating`: Operating years only (excludes Year 12 liquidation)
- `ctx.latest`: Operating data for the latest selected year (`ctx.latest_year`)
- `ctx.prev`: Operating data for the previous selected year (`ctx.prev_year`)
- `ctx.selected_metric`: Currently selected metric key in the sidebar
- `ctx.colors`, `ctx.metric_labels`, `ctx.subtitle`
- `ctx.delta("receita")`: Helper returning the median change between `ctx.latest` and `ctx.prev`

The helpers in `components` (`section`, `card`, `chart`) are **optional**. If a page needs a completely custom layout, return any `html.Div(...)` or `dcc.Graph(...)` directly inside that page file.

### 4. Edit a financial statement page (DRE, DFC, or Balance Sheet)

Everything for each statement page lives in one file:

- `pages/dre.py` — `DRE_ROWS`, table builder, Top-10 chart, callbacks, and Excel export
- `pages/dfc.py` — `DFC_ROWS`, table builder, callbacks, and Excel export
- `pages/balanco.py` — `BALANCO_ROWS`, table builder, callbacks, and Excel export

### 5. Edit styles

All CSS rules live in `src/dashboard/assets/style.css`, organized into 10 numbered sections. Dash loads this file automatically on startup and hot-reloads it in debug mode.
