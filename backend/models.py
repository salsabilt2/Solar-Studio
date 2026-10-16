from datetime import datetime, timezone

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="user")
    tier: Mapped[str] = mapped_column(String(20), default="free")
    company_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Panel(Base):
    __tablename__ = "panels"
    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    maker: Mapped[str] = mapped_column(String(120))
    model: Mapped[str] = mapped_column(String(160))
    rated_w: Mapped[float] = mapped_column(Float)
    area_m2: Mapped[float] = mapped_column(Float)
    temp_coefficient: Mapped[float] = mapped_column(Float, default=-0.0035)
    datasheet_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    published: Mapped[bool] = mapped_column(Boolean, default=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    company: Mapped[User | None] = relationship()


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    owner: Mapped[User] = relationship()
    setups: Mapped[list["Setup"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


class Setup(Base):
    __tablename__ = "setups"
    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    panel_id: Mapped[int] = mapped_column(ForeignKey("panels.id"))
    label: Mapped[str] = mapped_column(String(160))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    location_name: Mapped[str] = mapped_column(String(200))
    orientation: Mapped[float] = mapped_column(Float, default=180)
    tilt: Mapped[float] = mapped_column(Float, default=30)
    panel_count: Mapped[int] = mapped_column(Integer, default=10)
    roof_area_m2: Mapped[float | None] = mapped_column(Float, nullable=True)
    loss_pct: Mapped[float] = mapped_column(Float, default=14)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    project: Mapped[Project] = relationship(back_populates="setups")
    panel: Mapped[Panel] = relationship()
    reports: Mapped[list["Report"]] = relationship(
        back_populates="setup", cascade="all, delete-orphan"
    )


class WeatherCache(Base):
    __tablename__ = "weather_cache"
    __table_args__ = (UniqueConstraint("cache_key"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    cache_key: Mapped[str] = mapped_column(String(180), index=True)
    source: Mapped[str] = mapped_column(String(100), default="Open-Meteo historical")
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    payload: Mapped[dict] = mapped_column(JSON)


class Report(Base):
    __tablename__ = "reports"
    __table_args__ = (UniqueConstraint("setup_id", "start_date", "end_date"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    setup_id: Mapped[int] = mapped_column(ForeignKey("setups.id"), index=True)
    start_date: Mapped[str] = mapped_column(String(10))
    end_date: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(24), default="pending")
    email_status: Mapped[str] = mapped_column(String(24), default="pending")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    total_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    daily: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    setup: Mapped[Setup] = relationship(back_populates="reports")


class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    panel_id: Mapped[int | None] = mapped_column(ForeignKey("panels.id"), nullable=True)
    filename: Mapped[str] = mapped_column(String(255))
    pdf_bytes: Mapped[bytes] = mapped_column(LargeBinary)
    public: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(24), default="pending")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    index_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), index=True)
    page_number: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float] | None] = mapped_column(
        Vector(1536).with_variant(JSON, "sqlite"), nullable=True
    )
    document: Mapped[Document] = relationship()


class AiUsage(Base):
    __tablename__ = "ai_usage"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    cost_usd: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
