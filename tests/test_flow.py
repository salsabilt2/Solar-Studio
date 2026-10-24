from datetime import date, datetime, timedelta, timezone
from io import BytesIO
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pypdf import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from backend import ai, main, reports, solar
from backend.config import settings
from backend.db import SessionLocal
from backend.models import Document, DocumentChunk, Panel, User


def fixture_pdf():
    output = BytesIO()
    pdf = canvas.Canvas(output, pagesize=A4)
    pdf.drawString(50, 700, "JinkoSolar test panel rated power is 440 W.")
    pdf.save()
    return output.getvalue()


def register(client, email="alice@example.com"):
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "name": "Alice Tester", "password": "strong-password-123"},
    )
    assert response.status_code == 200, response.text
    return response.json()


def create_setup(client, project_id, panel_id):
    response = client.post(
        f"/api/v1/projects/{project_id}/setups",
        json={
            "label": "South roof",
            "panel_id": panel_id,
            "latitude": 50.8278,
            "longitude": 12.9214,
            "location_name": "Chemnitz, Germany",
            "orientation": 180,
            "tilt": 30,
            "panel_count": 10,
            "roof_area_m2": 30,
            "loss_pct": 14,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()


def sample_weather():
    start = datetime(2026, 6, 1, tzinfo=timezone.utc)
    sun = [max(0, 720 * (1 - abs(hour - 12) / 7)) for hour in range(24)]
    return {
        "timezone": "UTC",
        "hourly": {
            "time": [int((start + timedelta(hours=hour)).timestamp()) for hour in range(24)],
            "shortwave_radiation": sun,
            "direct_normal_irradiance": sun,
            "diffuse_radiation": [value * 0.2 for value in sun],
            "temperature_2m": [20] * 24,
            "wind_speed_10m": [7.2] * 24,
            "cloud_cover": [10] * 24,
        },
    }


def test_public_preview_uses_selected_settings_and_one_day(client, monkeypatch):
    monkeypatch.setattr(main, "fetch_weather", lambda *args, **kwargs: sample_weather())
    south = client.get("/api/v1/demo?place=Chemnitz&orientation=180&tilt=30&panel_count=10")
    west = client.get("/api/v1/demo?place=Madrid&orientation=270&tilt=20&panel_count=5")
    assert south.status_code == 200
    assert west.status_code == 200
    assert south.json()["location"] == "Chemnitz, Germany"
    assert west.json()["location"] == "Madrid, Spain"
    assert south.json()["rated_kw"] == 4.4
    assert west.json()["rated_kw"] == 2.2
    assert len(south.json()["daily"]) == 1
    assert west.json()["total_kwh"] != south.json()["total_kwh"]
    assert client.get("/api/v1/demo?panel_count=21").status_code == 422


def test_account_project_limits_and_private_data(client):
    register(client)
    panels = client.get("/api/v1/panels").json()
    assert len(panels) == 3
    project = client.post("/api/v1/projects", json={"name": "My roof"}).json()
    assert client.post("/api/v1/projects", json={"name": "Second roof"}).status_code == 409
    assert (
        client.post(
            f"/api/v1/projects/{project['id']}/setups",
            json={
                "label": "Too crowded",
                "panel_id": panels[0]["id"],
                "latitude": 50,
                "longitude": 12,
                "location_name": "Chemnitz",
                "panel_count": 10,
                "roof_area_m2": 5,
            },
        ).status_code
        == 422
    )
    for _ in range(3):
        create_setup(client, project["id"], panels[0]["id"])
    assert (
        client.post(
            f"/api/v1/projects/{project['id']}/setups",
            json={
                "label": "Fourth",
                "panel_id": panels[0]["id"],
                "latitude": 50,
                "longitude": 12,
                "location_name": "Chemnitz",
            },
        ).status_code
        == 409
    )
    alice_project_id = project["id"]
    client.post("/api/v1/auth/logout")
    register(client, "bob@example.com")
    assert client.get(f"/api/v1/projects/{alice_project_id}").status_code == 404
    assert client.get("/api/v1/projects").json() == []
    assert client.get("/api/v1/admin/deleted-users").status_code == 403
    assert client.get("/api/v1/admin/users").status_code == 403


def test_report_locks_project_only_after_email_acceptance(client, monkeypatch):
    register(client)
    panel_id = client.get("/api/v1/panels").json()[0]["id"]
    project = client.post("/api/v1/projects", json={"name": "My roof"}).json()
    setup = create_setup(client, project["id"], panel_id)
    monkeypatch.setattr(reports, "fetch_weather", lambda *args, **kwargs: sample_weather())
    sent = []

    def accept_once(report, recipient, label):
        reports.process_report(report.id)
        sent.append(report.id)

    monkeypatch.setattr(reports, "send_report_email", accept_once)
    response = client.post(f"/api/v1/setups/{setup['id']}/reports", json={})
    assert response.status_code == 200, response.text
    report_id = response.json()["id"]
    result = client.get(f"/api/v1/reports/{report_id}").json()
    assert result["status"] == "ready"
    assert result["total_kwh"] > 0
    assert len(result["daily"]) == 1
    assert len(sent) == 1
    assert client.post(f"/api/v1/setups/{setup['id']}/reports", json={}).json()["id"] == report_id
    assert len(sent) == 1
    assert client.get(f"/api/v1/projects/{project['id']}").json()["status"] == "completed"
    assert (
        client.patch(f"/api/v1/projects/{project['id']}", json={"name": "Changed"}).status_code
        == 409
    )
    assert client.post(f"/api/v1/projects/{project['id']}/copy").status_code == 409
    pdf_response = client.get(f"/api/v1/reports/{report_id}/pdf")
    assert pdf_response.status_code == 200
    pdf_text = PdfReader(BytesIO(pdf_response.content)).pages[0].extract_text()
    assert "Estimated electricity by day" in pdf_text
    assert "JinkoSolar" in pdf_text


def test_failed_email_keeps_project_editable(client, monkeypatch):
    register(client)
    panel_id = client.get("/api/v1/panels").json()[0]["id"]
    project = client.post("/api/v1/projects", json={"name": "My roof"}).json()
    setup = create_setup(client, project["id"], panel_id)
    monkeypatch.setattr(reports, "fetch_weather", lambda *args, **kwargs: sample_weather())

    def fail(*args):
        raise RuntimeError("Provider refused email")

    monkeypatch.setattr(reports, "send_report_email", fail)
    report_id = client.post(f"/api/v1/setups/{setup['id']}/reports", json={}).json()["id"]
    assert client.get(f"/api/v1/reports/{report_id}").json()["status"] == "failed"
    assert client.get(f"/api/v1/projects/{project['id']}").json()["status"] == "active"


def test_solar_estimate_rejects_missing_weather(client):
    from backend.models import Setup
    from backend.solar import estimate

    panel = Panel(maker="Test", model="Test", rated_w=440, area_m2=2, temp_coefficient=-0.003)
    setup = Setup(
        panel=panel,
        latitude=50.8,
        longitude=12.9,
        orientation=180,
        tilt=30,
        panel_count=10,
        loss_pct=14,
    )
    weather = sample_weather()
    result = estimate(setup, weather)
    assert result["total_kwh"] > 0
    assert result["day_curve"][0]["kwh"] == 0
    assert result["rated_kw"] == 4.4
    weather["hourly"]["shortwave_radiation"][12] = None
    with pytest.raises(HTTPException, match="missing hours"):
        estimate(setup, weather)


def test_copy_is_independent_and_requires_an_open_slot(client):
    user = register(client)
    with SessionLocal() as db:
        db.get(User, user["id"]).tier = "unlimited"
        db.commit()
    panel_id = client.get("/api/v1/panels").json()[0]["id"]
    source = client.post("/api/v1/projects", json={"name": "Original"}).json()
    original_setup = create_setup(client, source["id"], panel_id)
    copied = client.post(f"/api/v1/projects/{source['id']}/copy").json()
    assert copied["setups"][0]["id"] != original_setup["id"]
    assert copied["setups"][0]["panel_count"] == 10
    assert copied["setups"][0]["roof_area_m2"] == 30
    assert (
        client.patch(f"/api/v1/projects/{copied['id']}", json={"name": "Experiment"}).status_code
        == 200
    )
    assert client.get(f"/api/v1/projects/{source['id']}").json()["name"] == "Original"


def test_private_document_search_and_download_are_owner_scoped(client, monkeypatch):
    alice = register(client)
    panel_id = client.get("/api/v1/panels").json()[0]["id"]
    with SessionLocal() as db:
        private = Document(
            owner_id=alice["id"],
            filename="alice.pdf",
            pdf_bytes=b"%PDF-test",
            public=False,
            status="ready",
        )
        db.add(private)
        db.flush()
        db.add(
            DocumentChunk(
                document_id=private.id,
                page_number=3,
                content="Alice solar note",
                embedding=[1.0, 0.0],
            )
        )
        db.commit()
        alice_document_id = private.id
    client.post("/api/v1/auth/logout")
    bob = register(client, "bob@example.com")
    with SessionLocal() as db:
        private = Document(
            owner_id=bob["id"],
            filename="bob.pdf",
            pdf_bytes=b"%PDF-test",
            public=False,
            status="ready",
        )
        public = Document(
            owner_id=bob["id"],
            panel_id=panel_id,
            filename="public.pdf",
            pdf_bytes=b"%PDF-test",
            public=True,
            status="ready",
        )
        db.add_all([private, public])
        db.commit()
        bob_private_id, public_id = private.id, public.id
    client.post("/api/v1/auth/logout")
    client.post(
        "/api/v1/auth/login", json={"email": "alice@example.com", "password": "strong-password-123"}
    )
    visible = {item["id"]: item["can_delete"] for item in client.get("/api/v1/ai/documents").json()}
    assert visible == {alice_document_id: True, public_id: False}
    assert client.get(f"/api/v1/ai/documents/{bob_private_id}/pdf").status_code == 404
    assert client.get(f"/api/v1/ai/documents/{alice_document_id}/pdf").status_code == 200
    assert client.delete(f"/api/v1/ai/documents/{public_id}").status_code == 404
    monkeypatch.setattr(ai, "embed", lambda _: [[1.0, 0.0]])
    completion = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="From the note [1]."))]
    )
    fake = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **_: completion))
    )
    monkeypatch.setattr(ai, "client", lambda: fake)
    answer = client.post("/api/v1/ai/ask", json={"question": "What does my note say?"}).json()
    assert [source["document_id"] for source in answer["sources"]] == [alice_document_id]
    with SessionLocal() as db:
        db.get(Panel, panel_id).published = False
        db.commit()
    assert {item["id"] for item in client.get("/api/v1/ai/documents").json()} == {alice_document_id}
    completion.choices[0].message.content = "Unsupported claim [9]."
    assert (
        client.post("/api/v1/ai/ask", json={"question": "Is there a guarantee?"}).json()["sources"]
        == []
    )
    assert client.delete(f"/api/v1/ai/documents/{alice_document_id}").status_code == 200
    assert client.get("/api/v1/ai/documents").json() == []
    assert client.get(f"/api/v1/ai/documents/{alice_document_id}/pdf").status_code == 404
    with SessionLocal() as db:
        assert (
            db.query(DocumentChunk).filter(DocumentChunk.document_id == alice_document_id).count()
            == 0
        )


def test_invitation_is_required_when_public_signup_is_disabled(client, monkeypatch):
    monkeypatch.setattr(settings, "allow_public_signup", False)
    monkeypatch.setattr(settings, "invite_code", "")
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "no-invite@example.com",
            "name": "No Invite",
            "password": "strong-password-123",
        },
    )
    assert response.status_code == 403
    monkeypatch.setattr(settings, "invite_code", "test-invitation")
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "invited@example.com",
            "name": "Invited User",
            "password": "strong-password-123",
            "invite_code": "test-invitation",
        },
    )
    assert response.status_code == 200


def test_administrator_can_find_and_upgrade_an_account(client):
    admin = register(client)
    with SessionLocal() as db:
        db.get(User, admin["id"]).role = "admin"
        db.commit()
    users = client.get("/api/v1/admin/users")
    assert users.status_code == 200
    assert users.json()[0]["id"] == admin["id"]
    changed = client.patch(
        f"/api/v1/admin/users/{admin['id']}",
        json={"tier": "unlimited", "role": "admin"},
    )
    assert changed.status_code == 200
    assert changed.json()["tier"] == "unlimited"


def test_cross_site_mutation_origin_is_rejected(client):
    register(client)
    response = client.post(
        "/api/v1/auth/logout", headers={"Origin": "https://another-site.example"}
    )
    assert response.status_code == 403
    assert client.get("/api/v1/me").status_code == 200


def test_weather_rejects_missing_edge_hour(client, monkeypatch):
    from backend.models import Setup

    weather = sample_weather()
    for field in weather["hourly"].values():
        field.pop(0)
    monkeypatch.setattr(
        solar.httpx,
        "get",
        lambda *args, **kwargs: SimpleNamespace(
            raise_for_status=lambda: None, json=lambda: weather
        ),
    )
    setup = Setup(latitude=50.8, longitude=12.9)
    with SessionLocal() as db, pytest.raises(HTTPException, match="incomplete date range"):
        solar.fetch_weather(db, setup, date(2026, 6, 1), date(2026, 6, 1))


def test_document_index_job_status_and_retry(client, monkeypatch):
    register(client)
    monkeypatch.setattr(ai, "client", lambda: object())

    def unavailable(_):
        raise RuntimeError("temporary AI failure")

    monkeypatch.setattr(ai, "embed", unavailable)
    uploaded = client.post(
        "/api/v1/ai/documents",
        files={"file": ("notes.pdf", fixture_pdf(), "application/pdf")},
    )
    assert uploaded.status_code == 200
    document_id = uploaded.json()["id"]
    listed = client.get("/api/v1/ai/documents").json()
    assert listed[0]["status"] == "failed"
    assert "temporary AI failure" not in listed[0]["error"]
    monkeypatch.setattr(ai, "embed", lambda texts: [[1.0, 0.0] for _ in texts])
    retried = client.post(f"/api/v1/ai/documents/{document_id}/retry")
    assert retried.status_code == 200
    assert client.get("/api/v1/ai/documents").json()[0]["status"] == "ready"
    with SessionLocal() as db:
        assert db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).count() > 0


def test_indexing_stops_if_document_is_deleted_during_embedding(client, monkeypatch):
    user = register(client)
    with SessionLocal() as db:
        document = Document(owner_id=user["id"], filename="notes.pdf", pdf_bytes=fixture_pdf())
        db.add(document)
        db.commit()
        document_id = document.id

    def delete_during_embedding(texts):
        with SessionLocal() as db:
            db.delete(db.get(Document, document_id))
            db.commit()
        return [[1.0, 0.0] for _ in texts]

    monkeypatch.setattr(ai, "embed", delete_during_embedding)
    ai.index_document(document_id)
    with SessionLocal() as db:
        assert db.get(Document, document_id) is None
        assert db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).count() == 0
