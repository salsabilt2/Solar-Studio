from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from backend.auth import (
    COOKIE_NAME,
    current_user,
    hasher,
    make_token,
    public_user,
    require_role,
    verify_password,
)
from backend.config import settings
from backend.db import get_db
from backend.models import Panel, Project, Setup, User

router = APIRouter(prefix="/api/v1")


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=200)
    name: str = Field(min_length=2, max_length=120)
    invite_code: str = ""
    company_name: str | None = Field(default=None, max_length=160)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class ProfileIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    company_name: str | None = Field(default=None, max_length=160)


class TierIn(BaseModel):
    tier: str = Field(pattern="^(free|unlimited)$")
    role: str = Field(pattern="^(user|company|admin)$")


class PanelIn(BaseModel):
    maker: str = Field(min_length=2, max_length=120)
    model: str = Field(min_length=2, max_length=160)
    rated_w: float = Field(gt=0, le=2000)
    area_m2: float = Field(gt=0, le=5)
    temp_coefficient: float = Field(default=-0.0035, ge=-0.01, le=0)
    datasheet_url: str | None = Field(default=None, max_length=1000)
    published: bool = False


class ProjectIn(BaseModel):
    name: str = Field(min_length=2, max_length=160)


class SetupIn(BaseModel):
    label: str = Field(min_length=2, max_length=160)
    panel_id: int
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    location_name: str = Field(min_length=1, max_length=200)
    orientation: float = Field(default=180, ge=0, lt=360)
    tilt: float = Field(default=30, ge=0, le=90)
    panel_count: int = Field(default=10, ge=1, le=10000)
    roof_area_m2: float | None = Field(default=None, gt=0, le=100000)
    loss_pct: float = Field(default=14, ge=0, le=50)


def get_project(db: Session, project_id: int, owner_id: int) -> Project:
    project = db.scalar(
        select(Project)
        .options(selectinload(Project.setups).selectinload(Setup.panel))
        .where(Project.id == project_id, Project.owner_id == owner_id)
    )
    if not project:
        raise HTTPException(404, "Project not found.")
    return project


def get_setup(db: Session, setup_id: int, owner_id: int) -> Setup:
    setup = db.scalar(
        select(Setup)
        .join(Project)
        .options(selectinload(Setup.panel), selectinload(Setup.project))
        .where(Setup.id == setup_id, Project.owner_id == owner_id)
    )
    if not setup:
        raise HTTPException(404, "Panel setup not found.")
    return setup


def ensure_active(project: Project) -> None:
    if project.status != "active":
        raise HTTPException(409, "This project is read-only. Copy it to make changes.")


def panel_out(panel: Panel) -> dict:
    return {
        key: getattr(panel, key)
        for key in (
            "id",
            "company_id",
            "maker",
            "model",
            "rated_w",
            "area_m2",
            "temp_coefficient",
            "datasheet_url",
            "published",
        )
    }


def setup_out(setup: Setup) -> dict:
    value = {
        key: getattr(setup, key)
        for key in (
            "id",
            "project_id",
            "panel_id",
            "label",
            "latitude",
            "longitude",
            "location_name",
            "orientation",
            "tilt",
            "panel_count",
            "roof_area_m2",
            "loss_pct",
        )
    }
    value["created_at"] = setup.created_at.isoformat()
    value["rated_kw"] = round(setup.panel_count * setup.panel.rated_w / 1000, 3)
    value["area_m2"] = round(setup.panel_count * setup.panel.area_m2, 2)
    value["panel"] = panel_out(setup.panel)
    return value


def project_out(project: Project) -> dict:
    return {
        "id": project.id,
        "name": project.name,
        "status": project.status,
        "created_at": project.created_at.isoformat(),
        "completed_at": project.completed_at.isoformat() if project.completed_at else None,
        "setups": [setup_out(setup) for setup in project.setups],
    }


@router.post("/auth/register")
def register(payload: RegisterIn, response: Response, db: Session = Depends(get_db)):
    if (not settings.allow_public_signup or settings.invite_code) and (
        not settings.invite_code or payload.invite_code != settings.invite_code
    ):
        raise HTTPException(403, "An invitation is required.")
    email = str(payload.email).lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "Email is already registered.")
    user = User(
        email=email,
        name=payload.name.strip(),
        password_hash=hasher.hash(payload.password),
        role="company" if payload.company_name else "user",
        company_name=payload.company_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    response.set_cookie(
        COOKIE_NAME,
        make_token(user),
        httponly=True,
        secure=settings.app_env == "production",
        samesite="lax",
        max_age=7 * 86400,
    )
    return public_user(user)


@router.post("/auth/login")
def login(payload: LoginIn, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == str(payload.email).lower()))
    if not user or user.deleted_at or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Email or password is incorrect.")
    response.set_cookie(
        COOKIE_NAME,
        make_token(user),
        httponly=True,
        secure=settings.app_env == "production",
        samesite="lax",
        max_age=7 * 86400,
    )
    return public_user(user)


@router.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie(COOKIE_NAME)
    return {"ok": True}


@router.get("/me")
def me(user: User = Depends(current_user)):
    return public_user(user)


@router.patch("/me")
def update_me(
    payload: ProfileIn, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    user.name = payload.name.strip()
    if user.role == "company":
        user.company_name = payload.company_name
    db.commit()
    return public_user(user)


@router.delete("/me")
def delete_me(
    response: Response, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    user.deleted_at = datetime.now(timezone.utc)
    db.commit()
    response.delete_cookie(COOKIE_NAME)
    return {"ok": True}


@router.get("/admin/deleted-users")
def deleted_users(_: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    users = db.scalars(select(User).where(User.deleted_at.is_not(None))).all()
    return [{**public_user(user), "deleted_at": user.deleted_at.isoformat()} for user in users]


@router.get("/admin/users")
def admin_users(_: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    users = db.scalars(
        select(User).where(User.deleted_at.is_(None)).order_by(User.created_at.desc()).limit(100)
    ).all()
    return [public_user(user) for user in users]


@router.patch("/admin/users/{user_id}")
def set_user_tier(
    user_id: int,
    payload: TierIn,
    _: User = Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Account not found.")
    user.tier, user.role = payload.tier, payload.role
    db.commit()
    return public_user(user)


@router.get("/panels")
def list_panels(db: Session = Depends(get_db)):
    panels = db.scalars(
        select(Panel).where(Panel.published.is_(True), Panel.deleted_at.is_(None))
    ).all()
    return [panel_out(panel) for panel in panels]


@router.get("/company/panels")
def company_panels(
    user: User = Depends(require_role("company", "admin")), db: Session = Depends(get_db)
):
    return [
        panel_out(panel)
        for panel in db.scalars(
            select(Panel).where(Panel.company_id == user.id, Panel.deleted_at.is_(None))
        ).all()
    ]


@router.post("/company/panels")
def create_panel(
    payload: PanelIn,
    user: User = Depends(require_role("company", "admin")),
    db: Session = Depends(get_db),
):
    panel = Panel(**payload.model_dump(), company_id=user.id)
    db.add(panel)
    db.commit()
    db.refresh(panel)
    return panel_out(panel)


@router.patch("/company/panels/{panel_id}")
def update_panel(
    panel_id: int,
    payload: PanelIn,
    user: User = Depends(require_role("company", "admin")),
    db: Session = Depends(get_db),
):
    panel = db.get(Panel, panel_id)
    if not panel or panel.company_id != user.id or panel.deleted_at:
        raise HTTPException(404, "Panel not found.")
    for key, value in payload.model_dump().items():
        setattr(panel, key, value)
    db.commit()
    return panel_out(panel)


@router.delete("/company/panels/{panel_id}")
def delete_panel(
    panel_id: int,
    user: User = Depends(require_role("company", "admin")),
    db: Session = Depends(get_db),
):
    panel = db.get(Panel, panel_id)
    if not panel or panel.company_id != user.id:
        raise HTTPException(404, "Panel not found.")
    panel.deleted_at = datetime.now(timezone.utc)
    panel.published = False
    db.commit()
    return {"ok": True}


@router.get("/projects")
def list_projects(
    status: str | None = None, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    query = (
        select(Project)
        .options(selectinload(Project.setups).selectinload(Setup.panel))
        .where(Project.owner_id == user.id)
    )
    if status in ("active", "completed"):
        query = query.where(Project.status == status)
    return [
        project_out(project)
        for project in db.scalars(query.order_by(Project.created_at.desc())).all()
    ]


@router.post("/projects")
def create_project(
    payload: ProjectIn, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    db.scalar(select(User).where(User.id == user.id).with_for_update())
    if (
        user.tier == "free"
        and db.scalar(select(func.count(Project.id)).where(Project.owner_id == user.id)) >= 1
    ):
        raise HTTPException(409, "Free accounts can have one project.")
    project = Project(owner_id=user.id, name=payload.name.strip())
    db.add(project)
    db.commit()
    return project_out(get_project(db, project.id, user.id))


@router.get("/projects/{project_id}")
def read_project(
    project_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    return project_out(get_project(db, project_id, user.id))


@router.patch("/projects/{project_id}")
def update_project(
    project_id: int,
    payload: ProjectIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    project = get_project(db, project_id, user.id)
    ensure_active(project)
    project.name = payload.name.strip()
    db.commit()
    return project_out(project)


@router.delete("/projects/{project_id}")
def delete_project(
    project_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    project = get_project(db, project_id, user.id)
    db.delete(project)
    db.commit()
    return {"ok": True}


@router.post("/projects/{project_id}/copy")
def copy_project(
    project_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    db.scalar(select(User).where(User.id == user.id).with_for_update())
    if (
        user.tier == "free"
        and db.scalar(select(func.count(Project.id)).where(Project.owner_id == user.id)) >= 1
    ):
        raise HTTPException(409, "Free accounts need an open project slot to copy.")
    source = get_project(db, project_id, user.id)
    target = Project(owner_id=user.id, name=f"{source.name} — copy")
    db.add(target)
    db.flush()
    for setup in source.setups:
        db.add(
            Setup(
                **{
                    key: getattr(setup, key)
                    for key in (
                        "panel_id",
                        "label",
                        "latitude",
                        "longitude",
                        "location_name",
                        "orientation",
                        "tilt",
                        "panel_count",
                        "roof_area_m2",
                        "loss_pct",
                    )
                },
                project_id=target.id,
            )
        )
    db.commit()
    return project_out(get_project(db, target.id, user.id))


@router.post("/projects/{project_id}/setups")
def create_setup(
    project_id: int,
    payload: SetupIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    project = get_project(db, project_id, user.id)
    db.scalar(select(Project).where(Project.id == project.id).with_for_update())
    ensure_active(project)
    setup_count = db.scalar(select(func.count(Setup.id)).where(Setup.project_id == project.id))
    if user.tier == "free" and setup_count >= 3:
        raise HTTPException(409, "Free accounts can have three setups.")
    panel = db.get(Panel, payload.panel_id)
    if not panel or not panel.published or panel.deleted_at:
        raise HTTPException(422, "Choose an available panel.")
    if payload.roof_area_m2 and payload.panel_count * panel.area_m2 > payload.roof_area_m2:
        raise HTTPException(422, "These panels need more roof space than you entered.")
    setup = Setup(project_id=project_id, **payload.model_dump())
    db.add(setup)
    db.commit()
    db.refresh(setup)
    return setup_out(get_setup(db, setup.id, user.id))


@router.patch("/setups/{setup_id}")
def update_setup(
    setup_id: int,
    payload: SetupIn,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    setup = get_setup(db, setup_id, user.id)
    ensure_active(setup.project)
    panel = db.get(Panel, payload.panel_id)
    if not panel or not panel.published or panel.deleted_at:
        raise HTTPException(422, "Choose an available panel.")
    if payload.roof_area_m2 and payload.panel_count * panel.area_m2 > payload.roof_area_m2:
        raise HTTPException(422, "These panels need more roof space than you entered.")
    for key, value in payload.model_dump().items():
        setattr(setup, key, value)
    db.commit()
    db.refresh(setup)
    return setup_out(get_setup(db, setup.id, user.id))


@router.delete("/setups/{setup_id}")
def delete_setup(setup_id: int, user: User = Depends(current_user), db: Session = Depends(get_db)):
    setup = get_setup(db, setup_id, user.id)
    ensure_active(setup.project)
    db.delete(setup)
    db.commit()
    return {"ok": True}
