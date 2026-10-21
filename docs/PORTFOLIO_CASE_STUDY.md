# NexaDesk Glass — IT Helpdesk & Ticket Management — Portfolio Case Study

**Repository:** https://github.com/muratpalak/IT-Helpdesk-Ticket-Management  
**Status:** Local demonstration / portfolio project  
**Technical focus:** FastAPI · SQLite · JavaScript · Ticket workflow  
**Automated workflow:** [GitHub Actions](https://github.com/muratpalak/IT-Helpdesk-Ticket-Management/actions/workflows/tests.yml)

## Context and problem

This project explores **incident lifecycle and service desk workflow** through a reproducible portfolio exercise. Its examples are not represented as an employer deployment or production customer implementation.

## Implemented capabilities

- Ticket creation, assignment, status transitions and reopen workflow
- Impact/urgency to P1–P4 priority mapping
- Resolution notes and event history
- Search, filtering, metrics and CSV export

## Reproducible review

Read the repository [README](../README.md) for supported platforms and installation prerequisites. Where the necessary runtime tools are installed, reproduce the checks using:

```bash
python3 -m pip install -r requirements.txt pytest httpx && python3 -m pytest -q tests
```

The associated CI workflow provides evidence of the configured automated checks; it is **not** a guarantee of full feature coverage, security accreditation or production availability.

## Boundaries and honest limitations

Local portfolio demo with fictional tickets; no authentication, RBAC or production-ready data controls.

## Relevance to IT roles

Service desk workflows, incident categorisation, ticket quality and SLA awareness.

## Deutsche Kurzfassung

**Projekt:** Lokales Service-Desk-Demo mit Ticketaufnahme, Priorisierung, Zuweisung, Statusworkflow und CSV-Export.  
**Schwerpunkt:** Incident lifecycle and service desk workflow.  
**Nachweis:** Quellcode, Installationsanleitung, definierte Tests und GitHub-Actions-Protokolle.  
**Einordnung:** Portfolio-/Demonstrationsprojekt; keine Behauptung eines Produktiveinsatzes.
