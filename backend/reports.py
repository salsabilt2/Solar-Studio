"""Saved reports, delivery, and scheduled catch-up."""

import smtplib
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from email.message import EmailMessage
from io import BytesIO

import httpx
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy import and_, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from backend.auth import current_user
from backend.config import settings
from backend.db import SessionLocal, get_db
from backend.models import Document, Project, Report, Setup, User, utcnow
from backend.routes import get_setup, panel_out, setup_out
from backend.solar import default_dates, estimate, fetch_weather, geocode, validate_dates

router = APIRouter(prefix="/api/v1")


class ReportIn(BaseModel):
    start_date: date | None = None
    end_date: date | None = None


def report_out(report: Report) -> dict:
    return {
        "id": report.id,
        "setup_id": report.setup_id,
        "start_date": report.start_date,
        "end_date": report.end_date,
        "status": report.status,
        "email_status": report.email_status,
        "error": report.error,
        "total_kwh": report.total_kwh,
        "daily": report.daily,
        "snapshot": report.snapshot,
        "created_at": report.created_at.isoformat(),
    }


def owned_report(db: Session, report_id: int, user_id: int) -> Report:
    report = db.scalar(
        select(Report)
        .join(Setup)
        .join(Project)
        .options(selectinload(Report.setup).selectinload(Setup.panel))
        .where(Report.id == report_id, Project.owner_id == user_id)
    )
    if not report:
        raise HTTPException(404, "Report not found.")
    return report


def send_report_email(report: Report, recipient: str, label: str) -> None:
    subject = f"Your Solar Studio report — {label}"
    body = (
        f"Solar Studio estimated {report.total_kwh:.2f} kWh for {label} "
        f"from {report.start_date} to {report.end_date}.\n\n"
        "This is an estimate based on historical weather, not measured output.\n"
        f"View the chart: {settings.public_url}/app/reports/{report.id}\n"
    )
    if settings.resend_api_key and settings.email_from:
        try:
            response = httpx.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {settings.resend_api_key}",
                    "Idempotency-Key": f"solar-report-{report.id}",
                },
                json={
                    "from": settings.email_from,
                    "to": [recipient],
                    "subject": subject,
                    "text": body,
                },
                timeout=20,
            )
            response.raise_for_status()
            return
        except httpx.HTTPError as exc:
            raise RuntimeError("Email provider did not accept this report.") from exc
    if settings.app_env != "production" and settings.smtp_host and settings.email_from:
        message = EmailMessage()
        message["From"], message["To"], message["Subject"] = settings.email_from, recipient, subject
        message.set_content(body)
        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
                server.send_message(message)
        except (smtplib.SMTPException, OSError) as exc:
            raise RuntimeError("Email provider did not accept this report.") from exc
        return
    raise RuntimeError("Email delivery is not configured.")


def process_report(report_id: int) -> None:
    with SessionLocal() as db:
        claim = db.execute(
            update(Report)
            .where(
                Report.id == report_id,
                Report.email_status != "sent",
                or_(
                    Report.status != "running",
                    Report.started_at.is_(None),
                    Report.started_at < utcnow() - timedelta(minutes=15),
                ),
            )
            .values(status="running", started_at=utcnow(), error=None)
        )
        db.commit()
        if not claim.rowcount:
            return
        report = db.get(Report, report_id)
        try:
            setup = db.scalar(
                select(Setup)
                .options(selectinload(Setup.panel), selectinload(Setup.project))
                .where(Setup.id == report.setup_id)
            )
            if not setup:
                raise RuntimeError("Panel setup no longer exists.")
            owner = db.get(User, setup.project.owner_id)
            if not owner or owner.deleted_at:
                raise RuntimeError("Account is unavailable.")
            if report.daily is None:
                weather = fetch_weather(
                    db,
                    setup,
                    date.fromisoformat(report.start_date),
                    date.fromisoformat(report.end_date),
                )
                result = estimate(setup, weather)
                report.daily = result["daily"]
                report.total_kwh = result["total_kwh"]
                report.snapshot = {
                    "setup": setup_out(setup),
                    "panel": panel_out(setup.panel),
                    "source": result["source"],
                    "model": result["model"],
                    "timezone": result["timezone"],
                    "rated_kw": result["rated_kw"],
                    "area_m2": result["area_m2"],
                }
                db.commit()
            send_report_email(report, owner.email, setup.label)
            report.email_status, report.status = "sent", "ready"
            setup.project.status, setup.project.completed_at = "completed", utcnow()
            db.commit()
        except (HTTPException, RuntimeError, httpx.HTTPError, OSError) as exc:
            report.status, report.email_status = "failed", "failed"
            report.error = exc.detail if isinstance(exc, HTTPException) else str(exc)
            db.commit()


@router.get("/locations")
def search_locations(q: str):
    return geocode(q)


@router.post("/setups/{setup_id}/weather/refresh")
def refresh_weather(
    setup_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    setup = get_setup(db, setup_id, user.id)
    start, end = default_dates()
    payload = fetch_weather(db, setup, start, end, force=True)
    return {
        "hours": len(payload["hourly"]["time"]),
        "source": "Open-Meteo historical",
        "refreshed_at": utcnow().isoformat(),
    }


@router.get("/setups/{setup_id}/estimate")
def get_estimate(
    setup_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    setup = get_setup(db, setup_id, user.id)
    default_start, default_end = default_dates()
    start, end = start_date or default_start, end_date or default_end
    return estimate(setup, fetch_weather(db, setup, start, end))


@router.post("/setups/{setup_id}/reports")
def create_report(
    setup_id: int,
    payload: ReportIn,
    tasks: BackgroundTasks,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    setup = get_setup(db, setup_id, user.id)
    default_start, default_end = default_dates()
    start, end = payload.start_date or default_start, payload.end_date or default_end
    validate_dates(start, end)
    report = db.scalar(
        select(Report).where(
            Report.setup_id == setup.id,
            Report.start_date == str(start),
            Report.end_date == str(end),
        )
    )
    if report:
        if report.email_status != "sent":
            tasks.add_task(process_report, report.id)
        return report_out(report)
    report = Report(setup_id=setup.id, start_date=str(start), end_date=str(end))
    db.add(report)
    try:
        db.commit()
        db.refresh(report)
    except IntegrityError:
        db.rollback()
        report = db.scalar(
            select(Report).where(
                Report.setup_id == setup.id,
                Report.start_date == str(start),
                Report.end_date == str(end),
            )
        )
        if not report:
            raise
    tasks.add_task(process_report, report.id)
    return report_out(report)


@router.get("/reports")
def list_reports(user: User = Depends(current_user), db: Session = Depends(get_db)):
    reports = db.scalars(
        select(Report)
        .join(Setup)
        .join(Project)
        .where(Project.owner_id == user.id)
        .order_by(Report.created_at.desc())
    ).all()
    return [report_out(report) for report in reports]


@router.get("/reports/{report_id}")
def get_report(report_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return report_out(owned_report(db, report_id, user.id))


@router.post("/reports/{report_id}/retry")
def retry_report(
    report_id: int,
    tasks: BackgroundTasks,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    report = owned_report(db, report_id, user.id)
    if report.email_status != "sent":
        tasks.add_task(process_report, report.id)
    return report_out(report)


@router.get("/reports/{report_id}/pdf")
def download_report(
    report_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    report = owned_report(db, report_id, user.id)
    if not report.daily or not report.snapshot:
        raise HTTPException(409, "This report is not ready.")
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setFillColor(colors.HexColor("#0b302b"))
    pdf.rect(0, A4[1] - 165, A4[0], 165, fill=1, stroke=0)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 30)
    pdf.drawString(48, A4[1] - 80, "Solar Studio")
    pdf.setFont("Helvetica", 13)
    pdf.drawString(48, A4[1] - 110, "Historical electricity estimate")
    pdf.setFillColor(colors.HexColor("#0b302b"))
    pdf.setFont("Helvetica-Bold", 24)
    pdf.drawString(48, A4[1] - 225, f"{report.total_kwh:.1f} kWh")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(48, A4[1] - 250, f"{report.start_date} to {report.end_date}")
    setup = report.snapshot["setup"]
    panel = report.snapshot["panel"]
    pdf.drawString(48, A4[1] - 278, f"{setup['label'][:35]}  |  {setup['location_name'][:35]}")
    pdf.setFont("Helvetica", 10)
    details = [
        f"Panel: {panel['maker']} {panel['model']} ({panel['rated_w']} W)",
        f"{setup['panel_count']} panels  |  Rated {report.snapshot['rated_kw']} kW  |  Area {report.snapshot['area_m2']} m2",
        f"Direction {setup['orientation']} degrees  |  Slope {setup['tilt']} degrees  |  Loss {setup['loss_pct']}%",
    ]
    if setup.get("roof_area_m2"):
        details.append(f"Usable roof space: {setup['roof_area_m2']} m2")
    for line_no, line in enumerate(details):
        pdf.drawString(48, A4[1] - 307 - line_no * 18, line[:92])
    daily = report.daily
    if len(daily) > 62:
        grouped = defaultdict(float)
        for day in daily:
            grouped[day["date"][:7]] += day["kwh"]
        bars = [(period, amount) for period, amount in sorted(grouped.items())]
        chart_title = "Estimated electricity by month"
    else:
        bars = [(day["date"], day["kwh"]) for day in daily]
        chart_title = "Estimated electricity by day"
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(48, 437, chart_title)
    chart_left, chart_bottom, chart_width, chart_height = 48, 233, 500, 170
    pdf.setStrokeColor(colors.HexColor("#d6dfd3"))
    pdf.line(chart_left, chart_bottom, chart_left + chart_width, chart_bottom)
    maximum = max((amount for _, amount in bars), default=1) or 1
    step = chart_width / max(len(bars), 1)
    pdf.setFillColor(colors.HexColor("#d7a849"))
    for index, (_, amount) in enumerate(bars):
        pdf.rect(
            chart_left + index * step + 1,
            chart_bottom,
            max(step - 2, 0.8),
            chart_height * amount / maximum,
            fill=1,
            stroke=0,
        )
    pdf.setFillColor(colors.HexColor("#526d66"))
    pdf.setFont("Helvetica", 9)
    if bars:
        pdf.drawString(chart_left, chart_bottom - 18, bars[0][0])
        pdf.drawCentredString(
            chart_left + chart_width / 2, chart_bottom - 18, bars[len(bars) // 2][0]
        )
        pdf.drawRightString(chart_left + chart_width, chart_bottom - 18, bars[-1][0])
    pdf.drawString(48, 170, f"Weather: {report.snapshot['source']}")
    pdf.drawString(48, 153, f"Calculation: {report.snapshot['model']}")
    pdf.drawString(48, 136, f"Timezone: {report.snapshot['timezone']}")
    pdf.drawString(
        48, 119, f"Report saved: {report.created_at.date()} | {len(daily)} days included"
    )
    pdf.setFillColor(colors.HexColor("#526d66"))
    pdf.drawString(
        48,
        75,
        "Estimate only. Actual production may differ due to shade, installation and equipment.",
    )
    pdf.save()
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=solar-report-{report.id}.pdf"},
    )


def run_due_jobs(db: Session) -> dict:
    from backend.ai import index_document

    start, end = default_dates()
    refreshed = 0
    active_setups = db.scalars(select(Setup).join(Project).where(Project.status == "active")).all()
    for setup in active_setups:
        try:
            fetch_weather(db, setup, end, end, force=True)
            refreshed += 1
        except HTTPException:
            continue
    pending = db.scalars(select(Report).where(Report.email_status != "sent")).all()
    for report in pending:
        process_report(report.id)
    documents = db.scalars(
        select(Document.id).where(
            or_(
                Document.status == "pending",
                and_(
                    Document.status == "processing",
                    Document.index_started_at < utcnow() - timedelta(minutes=15),
                ),
            )
        )
    ).all()
    for document_id in documents:
        index_document(document_id)
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    setups = db.scalars(
        select(Setup).join(Project).where(Project.status == "active", Setup.created_at <= cutoff)
    ).all()
    created = 0
    for setup in setups:
        if db.scalar(select(Report).where(Report.setup_id == setup.id)):
            continue
        report = Report(setup_id=setup.id, start_date=str(start), end_date=str(end))
        db.add(report)
        db.commit()
        process_report(report.id)
        created += 1
    return {
        "weather_refreshed": refreshed,
        "retried": len(pending),
        "documents_recovered": len(documents),
        "created": created,
    }
