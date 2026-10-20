"""Integration tests for real ticket lifecycle and domain rules."""
import pytest
from fastapi.testclient import TestClient

import db
from app import app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test-helpdesk.db")
    with TestClient(app) as client:
        yield client


def sample(**overrides):
    return {
        "subject": "Cannot connect to company Wi-Fi",
        "description": "Laptop does not receive an IP address from the access point.",
        "requester": "Demo Tester",
        "requester_email": "tester@example.com",
        "category": "Network",
        "impact": "high",
        "urgency": "high",
        "assignee": None,
        **overrides,
    }


def create(client, **overrides):
    response = client.post("/api/tickets", json=sample(**overrides))
    assert response.status_code == 201, response.text
    return response.json()


def test_seed_and_dashboard(client):
    d = client.get("/api/dashboard").json()
    assert d["total"] == 10
    assert d["open"] + d["in_progress"] + d["resolved"] + d["closed"] == 10
    assert d["priorities"]["P1"] >= 1
    assert len(client.get("/api/tickets").json()["tickets"]) == 10


def test_priority_matrix(client):
    for impact, urgency, expected in [
        ("high", "high", "P1"), ("high", "medium", "P2"),
        ("medium", "high", "P2"), ("medium", "medium", "P3"),
        ("low", "high", "P3"), ("medium", "low", "P3"),
        ("low", "low", "P4"),
    ]:
        assert create(client, impact=impact, urgency=urgency)["priority"] == expected


def test_end_to_end_lifecycle(client):
    ticket = create(client)
    tid = ticket["id"]
    assert ticket["priority"] == "P1"
    assert ticket["status"] == "open"
    assert client.post(f"/api/tickets/{tid}/transition", json={"action": "start"}).status_code == 409
    assigned = client.patch(f"/api/tickets/{tid}", json={"assignee": "Alex Morgan"})
    assert assigned.status_code == 200
    started = client.post(f"/api/tickets/{tid}/transition", json={"action": "start"})
    assert started.json()["status"] == "in_progress"
    assert client.post(f"/api/tickets/{tid}/transition", json={"action": "close"}).status_code == 409
    assert client.post(f"/api/tickets/{tid}/transition", json={"action": "resolve", "resolution": "Done"}).status_code == 422
    resolution = "Restarted DHCP service and verified lease with ipconfig."
    resolved = client.post(f"/api/tickets/{tid}/transition", json={"action":"resolve","resolution":resolution})
    assert resolved.json()["resolution"] == resolution
    assert resolved.json()["status"] == "resolved"
    closed = client.post(f"/api/tickets/{tid}/transition", json={"action":"close"})
    assert closed.json()["status"] == "closed"
    assert closed.json()["closed_at"] is not None
    assert client.patch(f"/api/tickets/{tid}", json={"urgency":"low"}).status_code == 409
    reopened = client.post(f"/api/tickets/{tid}/transition", json={"action":"reopen"})
    assert reopened.json()["status"] == "open"
    assert reopened.json()["resolution"] is None
    assert any(e["event_type"] == "close" for e in reopened.json()["events"])


def test_update_and_notes(client):
    ticket = create(client, urgency="medium")
    tid = ticket["id"]
    assert ticket["priority"] == "P2"
    result = client.patch(f"/api/tickets/{tid}", json={"urgency":"low"}).json()
    assert result["priority"] == "P3"
    note = client.post(f"/api/tickets/{tid}/notes", json={"message":"Escalated to office network team.","actor":"Alex Morgan"})
    assert note.status_code == 201
    assert note.json()["events"][0]["message"] == "Escalated to office network team."
    assert len(note.json()["events"]) >= 3


def test_search_filters_and_csv(client):
    t = create(client, subject="Special demo VPN request", assignee="Alex Morgan")
    search = client.get("/api/tickets", params={"search":"Special demo VPN"}).json()
    assert search["total"] == 1 and search["tickets"][0]["id"] == t["id"]
    assert client.get("/api/tickets", params={"priority":"P1"}).json()["total"] >= 1
    assert client.get("/api/tickets", params={"assignee":"unassigned"}).json()["total"] >= 1
    csv_response = client.get("/api/export.csv")
    assert csv_response.status_code == 200
    assert "HD-" in csv_response.text
    assert "text/csv" in csv_response.headers["content-type"]


def test_invalid_and_missing_input(client):
    assert client.get("/api/tickets/999999").status_code == 404
    assert client.post("/api/tickets",json=sample(category="Unknown")).status_code == 422
    assert client.post("/api/tickets",json=sample(requester_email="not-an-email")).status_code == 422
    assert client.post("/api/tickets",json=sample(subject="   ")).status_code == 422


def test_glass_mode_quick_filters(client):
    all_tickets = client.get("/api/tickets").json()["tickets"]
    active = client.get("/api/tickets", params={"status": "active"}).json()["tickets"]
    completed = client.get("/api/tickets", params={"status": "completed"}).json()["tickets"]
    assert all(t["status"] in ("open", "in_progress") for t in active)
    assert all(t["status"] in ("resolved", "closed") for t in completed)
    assert len(active) + len(completed) == len(all_tickets)
    assert client.get("/api/tickets", params={"status": "in_progress"}).json()["total"] == 2


def test_update_impact_urgency_reject_null(client):
    ticket = create(client)
    assert client.patch(f"/api/tickets/{ticket['id']}", json={"impact": None}).status_code == 422
    assert client.patch(f"/api/tickets/{ticket['id']}", json={"urgency": None}).status_code == 422
