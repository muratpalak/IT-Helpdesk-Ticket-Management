"""Additional deterministic contract checks; no external services or real tickets."""
import pytest
from fastapi.testclient import TestClient
import db
from app import app

@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, 'DB_PATH', tmp_path / 'isolated-regressions.sqlite')
    with TestClient(app) as instance:
        yield instance

def ticket_payload(**overrides):
    return {
        'subject': 'Demo office network connectivity incident',
        'description': 'Sample workstation does not obtain an address on the test network.',
        'requester': 'Example User',
        'requester_email': 'example.user@example.com',
        'category': 'Network',
        'impact': 'medium',
        'urgency': 'medium',
        'assignee': None,
        **overrides,
    }

def test_priority_changes_when_urgency_increases(client):
    created = client.post('/api/tickets', json=ticket_payload())
    assert created.status_code == 201
    assert created.json()['priority'] == 'P3'
    item = created.json()
    updated = client.patch(f"/api/tickets/{item['id']}", json={'urgency': 'high'})
    assert updated.status_code == 200
    assert updated.json()['priority'] == 'P2'
    assert updated.json()['due_at'] != item['due_at']

def test_resolution_requires_assigned_started_ticket(client):
    created = client.post('/api/tickets', json=ticket_payload())
    tid = created.json()['id']
    attempt = client.post(f'/api/tickets/{tid}/transition', json={
        'action': 'resolve', 'resolution': 'Fictional fix verified with a sample user.'
    })
    assert attempt.status_code == 409
    unchanged = client.get(f'/api/tickets/{tid}')
    assert unchanged.status_code == 200
    assert unchanged.json()['status'] == 'open'

def test_invalid_requester_email_is_rejected_without_ticket(client):
    before = client.get('/api/tickets').json()['total']
    response = client.post('/api/tickets', json=ticket_payload(requester_email='invalid address'))
    assert response.status_code == 422
    assert client.get('/api/tickets').json()['total'] == before

def test_note_addition_is_visible_in_ticket_history(client):
    created = client.post('/api/tickets', json=ticket_payload())
    tid = created.json()['id']
    marker = 'Recorded scope: one fictional workstation only.'
    response = client.post(f'/api/tickets/{tid}/notes', json={'actor':'Demo Technician','message':marker})
    assert response.status_code == 201
    assert any(event['message']==marker for event in response.json()['events'])
