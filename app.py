"""Helpdesk API and static UI. Demonstration app, not a production multi-user service."""
from __future__ import annotations

import csv
import io
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from db import (
    ASSIGNEES, CATEGORIES, PRIORITY_HOURS, add_event, connection,
    init_db, insert_ticket, now_utc, priority_for, stamp, ticket_dict,
)

BASE = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="NexaDesk | IT Helpdesk Demo", version="2.0.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")


class TicketCreate(BaseModel):
    subject: str = Field(min_length=5, max_length=120)
    description: str = Field(min_length=10, max_length=2000)
    requester: str = Field(min_length=2, max_length=80)
    requester_email: str = Field(min_length=5, max_length=254)
    category: str
    impact: Literal["low", "medium", "high"]
    urgency: Literal["low", "medium", "high"]
    assignee: str | None = None

    @field_validator("subject", "description", "requester")
    @classmethod
    def not_blank(cls, v: str):
        if not v.strip():
            raise ValueError("Cannot be empty")
        return v.strip()

    @field_validator("requester_email")
    @classmethod
    def valid_email(cls, v: str):
        from email.utils import parseaddr
        if not v.strip() or " " in v or "@" not in v or "." not in v.rsplit("@", 1)[-1] or parseaddr(v)[1] != v:
            raise ValueError("Enter a valid email address")
        return v.strip()

    @field_validator("category")
    @classmethod
    def valid_category(cls, v: str):
        if v not in CATEGORIES:
            raise ValueError("Unknown category")
        return v

    @field_validator("assignee")
    @classmethod
    def valid_assignee(cls, v: str | None):
        if v is not None and v not in ASSIGNEES:
            raise ValueError("Unknown technician")
        return v


class TicketUpdate(BaseModel):
    assignee: str | None = None
    impact: Literal["low", "medium", "high"] | None = None
    urgency: Literal["low", "medium", "high"] | None = None

    @field_validator("assignee")
    @classmethod
    def valid_assignee(cls, v: str | None):
        if v is not None and v not in ASSIGNEES:
            raise ValueError("Unknown technician")
        return v


class Transition(BaseModel):
    action: Literal["start", "resolve", "close", "reopen"]
    actor: str = Field(default="Demo Agent", min_length=2, max_length=80)
    resolution: str | None = Field(default=None, max_length=2000)


class NoteCreate(BaseModel):
    actor: str = Field(default="Demo Agent", min_length=2, max_length=80)
    message: str = Field(min_length=2, max_length=2000)


def require_ticket(conn, ticket_id: int) -> dict:
    row = conn.execute("SELECT * FROM tickets WHERE id=?", (ticket_id,)).fetchone()
    if row is None:
        raise HTTPException(404, "Ticket not found")
    return dict(row)


def full_ticket(conn, ticket_id: int) -> dict:
    result = ticket_dict(require_ticket(conn, ticket_id))
    result["events"] = [dict(r) for r in conn.execute("SELECT * FROM events WHERE ticket_id=? ORDER BY created_at DESC,id DESC", (ticket_id,))]
    return result


@app.get("/")
def homepage():
    return FileResponse(BASE / "static" / "index.html")


@app.get("/api/meta")
def meta():
    return {"assignees": ASSIGNEES, "categories": CATEGORIES, "sla_hours": PRIORITY_HOURS,
            "notice": "Fictional demonstration data. No authentication or email notifications."}


@app.get("/api/tickets")
def list_tickets(
    search: str = Query("", max_length=120),
    status: str = Query("all"),
    priority: str = Query("all"),
    category: str = Query("all"),
    assignee: str = Query("all"),
    sort: Literal["newest", "oldest", "priority", "due"] = "newest",
):
    filters = []
    args = []
    if search:
        filters.append("(subject LIKE ? OR requester LIKE ? OR requester_email LIKE ? OR CAST(id AS TEXT) LIKE ?)")
        args.extend([f"%{search}%"] * 4)
    for column, value in (("status", status), ("priority", priority), ("category", category), ("assignee", assignee)):
        if value != "all":
            if column == "status" and value == "active":
                filters.append("status IN ('open', 'in_progress')")
            elif column == "status" and value == "completed":
                filters.append("status IN ('resolved', 'closed')")
            elif column == "assignee" and value == "unassigned":
                filters.append("assignee IS NULL")
            else:
                filters.append(f"{column}=?")
                args.append(value)
    where = " WHERE " + " AND ".join(filters) if filters else ""
    ordering = {"newest": "created_at DESC,id DESC", "oldest": "created_at ASC,id ASC", "priority": "priority ASC, created_at DESC", "due": "due_at ASC"}[sort]
    with connection() as conn:
        rows = conn.execute(f"SELECT * FROM tickets{where} ORDER BY {ordering}", args).fetchall()
    return {"tickets": [ticket_dict(r) for r in rows], "total": len(rows)}


@app.get("/api/tickets/{ticket_id}")
def get_ticket(ticket_id: int):
    with connection() as conn:
        return full_ticket(conn, ticket_id)


@app.post("/api/tickets", status_code=201)
def create_ticket(payload: TicketCreate):
    with connection() as conn:
        ticket_id = insert_ticket(conn, {**payload.model_dump(), "requester_email": str(payload.requester_email)})
        return full_ticket(conn, ticket_id)


@app.patch("/api/tickets/{ticket_id}")
def update_ticket(ticket_id: int, payload: TicketUpdate):
    fields = payload.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(400, "No changes supplied")
    if ("impact" in fields and fields["impact"] is None) or ("urgency" in fields and fields["urgency"] is None):
        raise HTTPException(422, "Impact and urgency cannot be null")
    with connection() as conn:
        current = require_ticket(conn, ticket_id)
        if current["status"] == "closed":
            raise HTTPException(409, "Reopen the ticket before editing")
        updated = {**current, **fields}
        p = priority_for(updated["impact"], updated["urgency"])
        # SLA target is recalculated from ticket creation, not from the edit timestamp.
        due = stamp(datetime.fromisoformat(current["created_at"]) + timedelta(hours=PRIORITY_HOURS[p]))
        changed = []
        for key in fields:
            if fields[key] != current[key]:
                changed.append(f"{key}: {current[key] or 'Unassigned'} → {fields[key] or 'Unassigned'}")
        if p != current["priority"]:
            changed.append(f"priority: {current['priority']} → {p}")
        if changed:
            conn.execute("UPDATE tickets SET assignee=?,impact=?,urgency=?,priority=?,due_at=?,updated_at=? WHERE id=?",
                         (updated["assignee"], updated["impact"], updated["urgency"], p, due, stamp(), ticket_id))
            add_event(conn, ticket_id, "updated", "Demo Agent", "; ".join(changed))
        return full_ticket(conn, ticket_id)


@app.post("/api/tickets/{ticket_id}/transition")
def transition(ticket_id: int, payload: Transition):
    allowed = {"open": {"start": "in_progress"},
               "in_progress": {"resolve": "resolved"},
               "resolved": {"close": "closed", "reopen": "in_progress"},
               "closed": {"reopen": "open"}}
    with connection() as conn:
        t = require_ticket(conn, ticket_id)
        new_status = allowed.get(t["status"], {}).get(payload.action)
        if not new_status:
            raise HTTPException(409, f"Cannot {payload.action} a ticket in state {t['status']}")
        if payload.action == "resolve" and (not payload.resolution or len(payload.resolution.strip()) < 10):
            raise HTTPException(422, "Provide a resolution of at least 10 characters")
        if payload.action == "start" and not t["assignee"]:
            raise HTTPException(409, "Assign a technician before starting work")
        now = stamp()
        changes = {"status": new_status, "updated_at": now}
        if payload.action == "start":
            changes["started_at"] = now
        elif payload.action == "resolve":
            changes["resolved_at"] = now
            changes["resolution"] = payload.resolution.strip()
        elif payload.action == "close":
            changes["closed_at"] = now
        elif payload.action == "reopen":
            changes["resolved_at"] = None
            changes["closed_at"] = None
            changes["resolution"] = None
        clauses = ", ".join(f"{k}=?" for k in changes)
        conn.execute(f"UPDATE tickets SET {clauses} WHERE id=?", [*changes.values(), ticket_id])
        msg = payload.resolution.strip() if payload.action == "resolve" else {
            "start": "Investigation started", "close": "Resolution confirmed; ticket closed", "reopen": "Ticket reopened for further work"}[payload.action]
        add_event(conn, ticket_id, payload.action, payload.actor.strip(), msg)
        return full_ticket(conn, ticket_id)


@app.post("/api/tickets/{ticket_id}/notes", status_code=201)
def add_note(ticket_id: int, payload: NoteCreate):
    if not payload.message.strip():
        raise HTTPException(422, "Note cannot be empty")
    with connection() as conn:
        require_ticket(conn, ticket_id)
        add_event(conn, ticket_id, "note", payload.actor.strip(), payload.message.strip())
        conn.execute("UPDATE tickets SET updated_at=? WHERE id=?", (stamp(), ticket_id))
        return full_ticket(conn, ticket_id)


@app.get("/api/dashboard")
def dashboard():
    with connection() as conn:
        rows = [ticket_dict(r) for r in conn.execute("SELECT * FROM tickets ORDER BY created_at DESC")]
    active = [t for t in rows if t["status"] in ("open", "in_progress")]
    return {
        "total": len(rows),
        "open": sum(t["status"] == "open" for t in rows),
        "in_progress": sum(t["status"] == "in_progress" for t in rows),
        "resolved": sum(t["status"] == "resolved" for t in rows),
        "closed": sum(t["status"] == "closed" for t in rows),
        "breached": sum(t["sla_state"] == "breached" for t in active),
        "unassigned": sum(t["assignee"] is None for t in active),
        "priorities": {p: sum(t["priority"] == p for t in rows) for p in PRIORITY_HOURS},
        "categories": {c: sum(t["category"] == c for t in rows) for c in CATEGORIES},
        "recent": rows[:5],
    }


@app.get("/api/export.csv")
def export_csv():
    with connection() as conn:
        rows = [ticket_dict(r) for r in conn.execute("SELECT * FROM tickets ORDER BY id DESC")]
    columns = ["reference", "subject", "requester", "requester_email", "category", "impact", "urgency", "priority", "status", "assignee", "created_at", "due_at", "resolved_at", "closed_at", "sla_state", "resolution"]
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(columns)
    for r in rows:
        # Prevent formula injection when CSV is opened by Excel / spreadsheets.
        writer.writerow(["'" + str(r[k]) if isinstance(r[k], str) and r[k].startswith(("=", "+", "-", "@")) else r[k] for k in columns])
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv; charset=utf-8",
                             headers={"Content-Disposition": 'attachment; filename="helpdesk-tickets.csv"'})
