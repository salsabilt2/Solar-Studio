from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend import ai, reports, routes
from backend.auth import hasher
from backend.config import settings
from backend.db import SessionLocal, get_db, init_db
from backend.models import Panel, Setup, User
from backend.solar import default_dates, estimate, fetch_weather

SEED_PANELS = [
    {
        "maker": "JinkoSolar",
        "model": "Tiger Neo JKM440N-54HL4R-B",
        "rated_w": 440,
        "area_m2": 1.762 * 1.134,
        "temp_coefficient": -0.0029,
        "datasheet_url": "https://www.jinkosolar.com/uploads/JKM420-440N-54HL4R-B-F1.3-EN.pdf",
    },
    {
        "maker": "AIKO",
        "model": "Neostar 2P AIKO-A455-MAH54Mw",
        "rated_w": 455,
        "area_m2": 1.757 * 1.134,
        "temp_coefficient": -0.0026,
        "datasheet_url": "https://aikosolar.com/wp-content/uploads/2024/06/Neostar-2P_188-AIKO-A-MAH54Mw_450-485W_1757x1134x30mm_wbbf_DSDr_EN_2405_V1.5.pdf",
    },
    {
        "maker": "Qcells",
        "model": "Q.TRON BLK M-G2+ 440",
        "rated_w": 440,
        "area_m2": 1.722 * 1.134,
        "temp_coefficient": -0.003,
        "datasheet_url": "https://us.qcells.com/wp-content/uploads/2023/10/Qcells_Data_sheet_Q.TRON_BLK_M-G2_series_415-440_2023-09_Rev01_NA.pdf",
    },
]


def seed() -> None:
    with SessionLocal() as db:
        if settings.admin_email and settings.admin_password:
            admin = db.scalar(select(User).where(User.email == settings.admin_email.lower()))
            if not admin:
                db.add(
                    User(
                        email=settings.admin_email.lower(),
                        name="Solar Studio admin",
                        password_hash=hasher.hash(settings.admin_password),
                        role="admin",
                        tier="unlimited",
                    )
                )
        for item in SEED_PANELS:
            if not db.scalar(select(Panel).where(Panel.model == item["model"])):
                db.add(Panel(**item, published=True))
        db.commit()


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.app_env == "production" and (
        settings.secret_key == "local-development-change-me-at-least-32-characters"
        or len(settings.secret_key) < 32
    ):
        raise RuntimeError("Set SECRET_KEY before production startup.")
    if settings.app_env == "production" and settings.allow_public_signup:
        raise RuntimeError("Disable public signup for the production showcase.")
    if settings.app_env == "production" and not settings.invite_code:
        raise RuntimeError("Set INVITE_CODE before production startup.")
    init_db()
    seed()
    yield


app = FastAPI(title="Solar Studio API", version="0.1.0", lifespan=lifespan)
app.include_router(routes.router)
app.include_router(reports.router)
app.include_router(ai.router)


@app.middleware("http")
async def check_browser_origin(request: Request, call_next):
    if request.method in {"POST", "PATCH", "PUT", "DELETE"}:
        origin = request.headers.get("origin")
        allowed = {settings.public_url.rstrip("/"), str(request.base_url).rstrip("/")}
        if origin and origin.rstrip("/") not in allowed:
            return JSONResponse({"detail": "This request came from another site."}, status_code=403)
    return await call_next(request)


@app.get("/api/v1/health")
def health():
    return {"status": "ok"}


DEMO_PLACES = {
    "Chemnitz": (50.8278, 12.9214, "Chemnitz, Germany"),
    "Berlin": (52.52, 13.405, "Berlin, Germany"),
    "Madrid": (40.4168, -3.7038, "Madrid, Spain"),
}


@app.get("/api/v1/demo")
def demo(
    place: Literal["Chemnitz", "Berlin", "Madrid"] = "Chemnitz",
    orientation: int = Query(180, ge=0, le=359),
    tilt: int = Query(30, ge=0, le=90),
    panel_count: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_db),
):
    panel = db.scalar(select(Panel).where(Panel.model == SEED_PANELS[0]["model"]))
    if not panel:
        raise HTTPException(503, "Demo panel is unavailable.")
    latitude, longitude, location_name = DEMO_PLACES[place]
    setup = Setup(
        panel_id=panel.id,
        panel=panel,
        project_id=0,
        label=f"{place} rooftop",
        latitude=latitude,
        longitude=longitude,
        location_name=location_name,
        orientation=orientation,
        tilt=tilt,
        panel_count=panel_count,
        loss_pct=14,
    )
    _, end = default_dates()
    start = end
    result = estimate(setup, fetch_weather(db, setup, start, end))
    return {
        **result,
        "location": setup.location_name,
        "start_date": str(start),
        "end_date": str(end),
    }


@app.post("/api/v1/jobs/run-due")
def run_due(authorization: str = Header(default=""), db: Session = Depends(get_db)):
    if not settings.scheduler_secret or authorization != f"Bearer {settings.scheduler_secret}":
        raise HTTPException(403, "Scheduler access denied.")
    return reports.run_due_jobs(db)


static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")


@app.get("/{path:path}", include_in_schema=False)
def frontend(path: str):
    index = static_dir / "index.html"
    if not index.exists() or path.startswith("api/"):
        raise HTTPException(404, "Page not found.")
    return FileResponse(index)
