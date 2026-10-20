"""SQLite persistence, domain rules and reproducible sample records."""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("HELPDESK_DB_PATH", str(BASE_DIR / "helpdesk.db")))
PRIORITY_HOURS = {"P1": 4, "P2": 8, "P3": 24, "P4": 72}
ASSIGNEES = ["Alex Morgan", "Samira Weber", "Jonas Keller", "Mia Schneider"]
CATEGORIES = ["Hardware", "Software", "Network", "Microsoft 365", "Accounts & Access", "Other"]


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def stamp(dt: datetime | None = None) -> str:
    return (dt or now_utc()).astimezone(timezone.utc).isoformat(timespec="seconds")


def priority_for(impact: str, urgency: str) -> str:
    score = {"low": 1, "medium": 2, "high": 3}[impact] + {"low": 1, "medium": 2, "high": 3}[urgency]
    return "P1" if score == 6 else "P2" if score == 5 else "P3" if score >= 3 else "P4"


@contextmanager
def connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=10000")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with connection() as conn:
        conn.executescript("""
          CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            description TEXT NOT NULL,
            requester TEXT NOT NULL,
            requester_email TEXT NOT NULL,
            category TEXT NOT NULL,
            impact TEXT NOT NULL,
            urgency TEXT NOT NULL,
            priority TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'open',
            assignee TEXT,
            resolution TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            due_at TEXT NOT NULL,
            started_at TEXT,
            resolved_at TEXT,
            closed_at TEXT
          );
          CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
            event_type TEXT NOT NULL,
            actor TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT NOT NULL
          );
          CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
          CREATE INDEX IF NOT EXISTS idx_tickets_priority ON tickets(priority);
          CREATE INDEX IF NOT EXISTS idx_events_ticket ON events(ticket_id);
        """)
        count = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
        if not count:
            seed(conn)


def add_event(conn, ticket_id: int, event_type: str, actor: str, message: str, when: str | None = None):
    conn.execute(
        "INSERT INTO events (ticket_id,event_type,actor,message,created_at) VALUES (?,?,?,?,?)",
        (ticket_id, event_type, actor, message, when or stamp()),
    )


def insert_ticket(conn, fields: dict, *, created_at: str | None = None) -> int:
    created = created_at or stamp()
    priority = priority_for(fields["impact"], fields["urgency"])
    due = stamp(datetime.fromisoformat(created) + timedelta(hours=PRIORITY_HOURS[priority]))
    cur = conn.execute("""
        INSERT INTO tickets (subject,description,requester,requester_email,category,
          impact,urgency,priority,status,assignee,created_at,updated_at,due_at)
        VALUES (:subject,:description,:requester,:requester_email,:category,
          :impact,:urgency,:priority,'open',:assignee,:created_at,:created_at,:due_at)
    """, {**fields, "priority": priority, "created_at": created, "due_at": due})
    ticket_id = cur.lastrowid
    add_event(conn, ticket_id, "created", "Service Desk", "Ticket created and priority calculated", created)
    if fields.get("assignee"):
        add_event(conn, ticket_id, "assigned", "Service Desk", f"Assigned to {fields['assignee']}", created)
    return ticket_id


def seed(conn):
    """Seed deterministic scenarios relative to the current date; all fictional."""
    samples = [
       ("Cannot sign in to Microsoft 365", "Outlook and Teams keep asking for credentials after password reset.", "Sofia Meier", "sofia.meier@example.com", "Microsoft 365", "high", "high", "Samira Weber", "in_progress", -1, None),
       ("Office Wi-Fi unavailable on floor 2", "Multiple laptops lose network connectivity; access point has no uplink.", "Daniel Fischer", "daniel.fischer@example.com", "Network", "high", "high", "Alex Morgan", "open", -6, None),
       ("New starter laptop setup", "Prepare Windows laptop, Microsoft 365 account, printer and standard applications.", "Nina Bauer", "nina.bauer@example.com", "Hardware", "medium", "medium", "Jonas Keller", "in_progress", -3, None),
       ("Shared printer not responding", "Finance department printer shows offline for several users.", "Luca Steiner", "luca.steiner@example.com", "Hardware", "medium", "high", "Mia Schneider", "resolved", -22, "Restarted print spooler, updated IP port, printed test page successfully."),
       ("VPN connection fails from home", "VPN client returns an authentication error after connecting.", "Emilia Roth", "emilia.roth@example.com", "Network", "medium", "high", "Alex Morgan", "open", -2, None),
       ("Request for Adobe Acrobat", "Need Acrobat for editing purchase order PDFs.", "Noah Berger", "noah.berger@example.com", "Software", "low", "low", None, "open", -5, None),
       ("Password reset for finance account", "Locked Windows account after failed password attempts.", "Mila Hoffmann", "mila.hoffmann@example.com", "Accounts & Access", "medium", "medium", "Samira Weber", "closed", -52, "Verified user identity and reset account password; user confirmed access."),
       ("Teams microphone not detected", "USB headset works in Windows but isn't selectable in Teams.", "Leon Richter", "leon.richter@example.com", "Microsoft 365", "low", "medium", "Mia Schneider", "resolved", -14, "Set device permissions, updated drivers and confirmed test call."),
       ("Laptop overheating during video calls", "Fan runs continuously and performance drops in meetings.", "Anna Vogel", "anna.vogel@example.com", "Hardware", "medium", "medium", "Jonas Keller", "open", -10, None),
       ("Add user to departmental shared drive", "Grant read access to the marketing drive after manager approval.", "Felix Braun", "felix.braun@example.com", "Accounts & Access", "low", "medium", None, "open", -1, None),
    ]
    for subject, description, requester, email, category, impact, urgency, assignee, status, hours, resolution in samples:
        created = stamp(now_utc() + timedelta(hours=hours))
        fields = dict(subject=subject, description=description, requester=requester, requester_email=email, category=category, impact=impact, urgency=urgency, assignee=assignee)
        tid = insert_ticket(conn, fields, created_at=created)
        if status in ("in_progress", "resolved", "closed"):
            step = stamp(datetime.fromisoformat(created) + timedelta(minutes=20))
            conn.execute("UPDATE tickets SET status='in_progress',started_at=?,updated_at=? WHERE id=?", (step, step, tid))
            add_event(conn, tid, "started", assignee or "Service Desk", "Work started", step)
        if status in ("resolved", "closed"):
            step = stamp(datetime.fromisoformat(created) + timedelta(hours=2))
            conn.execute("UPDATE tickets SET status='resolved',resolution=?,resolved_at=?,updated_at=? WHERE id=?", (resolution, step, step, tid))
            add_event(conn, tid, "resolved", assignee or "Service Desk", resolution or "Resolved", step)
        if status == "closed":
            step = stamp(datetime.fromisoformat(created) + timedelta(hours=4))
            conn.execute("UPDATE tickets SET status='closed',closed_at=?,updated_at=? WHERE id=?", (step, step, tid))
            add_event(conn, tid, "closed", "Service Desk", "Resolution confirmed; ticket closed", step)
    add_event(conn, 1, "note", "Samira Weber", "Investigating cached Microsoft 365 credentials.", stamp(now_utc() - timedelta(minutes=30)))


def ticket_dict(row) -> dict:
    t = dict(row)
    t["reference"] = f"HD-{t['id']:04d}"
    t["sla_state"] = "met" if t["resolved_at"] and t["resolved_at"] <= t["due_at"] else "breached" if (t["resolved_at"] or stamp()) > t["due_at"] else "on_track"
    t["sla_hours"] = PRIORITY_HOURS[t["priority"]]
    return t
