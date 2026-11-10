"""Formatted Excel (.xlsx) workbook generator for financial statement exports."""

from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter


# EXPORT: Formatted Excel Workbook Builder
def create_excel(title, subtitle, headers, rows, sheet_name):
    """Build a styled Excel workbook in memory and return its raw bytes."""
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name

    num_columns = len(headers)

    # Title row
    ws.merge_cells(
        start_row=1,
        start_column=1,
        end_row=1,
        end_column=num_columns,
    )
    title_cell = ws.cell(row=1, column=1, value=title)
    title_cell.font = Font(name="Arial", size=16, bold=True, color="FFFFFF")
    title_cell.fill = PatternFill("solid", fgColor="0F172A")
    title_cell.alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[1].height = 32

    # Subtitle row
    ws.merge_cells(
        start_row=2,
        start_column=1,
        end_row=2,
        end_column=num_columns,
    )
    subtitle_cell = ws.cell(row=2, column=1, value=subtitle)
    subtitle_cell.font = Font(name="Arial", size=10, italic=True, color="4E4E4E")

    # Table header row
    header_row = 4
    for col_idx, name in enumerate(headers, start=1):
        cell = ws.cell(row=header_row, column=col_idx, value=name)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="0284C7")
        cell.alignment = Alignment(horizontal="center", vertical="center")

    # Data rows
    total_border = Border(top=Side(style="thin", color="0284C7"))

    for row_idx, record in enumerate(rows, start=5):
        values = record["valores"]
        row_kind = record.get("tipo", "item")

        for col_idx, value in enumerate(values, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.alignment = Alignment(
                vertical="center",
                horizontal=(
                    "left"
                    if col_idx == 1 or (headers[0] == "" and col_idx == 2)
                    else "right"
                ),
            )

            # Keep financial values as numeric cells with Brazilian currency formatting
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                cell.number_format = "R$ #,##0.00;[Red](R$ #,##0.00);-"

            if row_kind == "section":
                cell.font = Font(bold=True, color="0F172A")
                cell.fill = PatternFill("solid", fgColor="CEE7F6")
            elif row_kind == "total":
                cell.font = Font(bold=True, color="0F172A")
                cell.border = total_border

    # Auto-fit column widths
    for col_idx in range(1, num_columns + 1):
        col_letter = get_column_letter(col_idx)
        max_len = max(
            len(str(ws.cell(row=r, column=col_idx).value or ""))
            for r in range(1, ws.max_row + 1)
        )
        ws.column_dimensions[col_letter].width = min(max(max_len + 4, 16), 38)

    ws.freeze_panes = "B5"
    ws.auto_filter.ref = f"A4:{get_column_letter(num_columns)}{ws.max_row}"
    ws.sheet_view.showGridLines = False

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()
