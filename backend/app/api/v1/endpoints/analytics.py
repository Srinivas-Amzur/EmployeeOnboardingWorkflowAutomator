"""
Analytics endpoints for dashboard statistics.
"""

import csv
from io import BytesIO, StringIO
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from ...dependencies import DbSession, get_current_user
from ....core.security import TokenData
from ....services.analytics import AnalyticsService

router = APIRouter(tags=["analytics"], prefix="/analytics")


@router.get("/dashboard")
async def get_dashboard_stats(
    db: DbSession,
    current_user: Annotated[TokenData, Depends(get_current_user)],
) -> dict:
    """
    Return aggregated statistics for the main dashboard.

    Includes workflow counts by state, task counts by status,
    employee counts, and average completion percentage.
    """
    service = AnalyticsService(db)
    return await service.get_dashboard_stats()


@router.get("/export")
async def export_analytics_report(
    db: DbSession,
    current_user: Annotated[TokenData, Depends(get_current_user)],
    report_type: Annotated[str, Query(pattern="^(workflow|employee|audit)$")],
    export_format: Annotated[str, Query(pattern="^(csv|pdf)$")],
):
    """Export analytics report as CSV or PDF."""
    service = AnalyticsService(db)
    dataset = await service.get_report_dataset(
        report_type=report_type,
        viewer_user_id=current_user.user_id,
        viewer_email=current_user.email,
        viewer_role=current_user.role,
    )

    if export_format == "csv":
        content = _render_csv(dataset)
        filename = f"{report_type}_report.csv"
        media_type = "text/csv"
    else:
        content = _render_pdf(dataset)
        filename = f"{report_type}_report.pdf"
        media_type = "application/pdf"

    return StreamingResponse(
        BytesIO(content),
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _render_csv(dataset: dict) -> bytes:
    output = StringIO()
    writer = csv.writer(output)

    writer.writerow([dataset.get("title", "Report")])
    writer.writerow([])
    writer.writerow(["Summary"])
    for key, value in dataset.get("summary", {}).items():
        writer.writerow([key, value])

    rows = dataset.get("rows", [])
    if rows:
        writer.writerow([])
        headers = list(rows[0].keys())
        writer.writerow(headers)
        for row in rows:
            writer.writerow([row.get(column, "") for column in headers])

    return output.getvalue().encode("utf-8")


def _render_pdf(dataset: dict) -> bytes:
    output = BytesIO()
    pdf = canvas.Canvas(output, pagesize=letter)
    _, height = letter
    y = height - 48

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(48, y, dataset.get("title", "Report"))
    y -= 28

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(48, y, "Summary")
    y -= 20
    pdf.setFont("Helvetica", 10)
    for key, value in dataset.get("summary", {}).items():
        if y < 60:
            pdf.showPage()
            y = height - 48
            pdf.setFont("Helvetica", 10)
        pdf.drawString(48, y, f"{key}: {value}")
        y -= 14

    y -= 8
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(48, y, "Rows")
    y -= 18
    pdf.setFont("Helvetica", 9)

    for row in dataset.get("rows", [])[:120]:
        if y < 60:
            pdf.showPage()
            y = height - 48
            pdf.setFont("Helvetica", 9)
        row_text = " | ".join(f"{key}: {value}" for key, value in row.items())
        truncated = row_text[:160]
        pdf.drawString(48, y, truncated)
        y -= 12

    pdf.save()
    return output.getvalue()
