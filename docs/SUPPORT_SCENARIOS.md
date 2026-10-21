# IT Helpdesk — reproducible support scenarios

**Purpose:** fictional service-desk exercises demonstrating software workflow, *not* real customer incidents or evidence of employment. The application stores and tracks a ticket; it does **not** repair the user's Wi-Fi or administer an enterprise network.

## Scenario 1 — Device cannot get a Wi-Fi IP address

**Symptom:** A colleague reports that a laptop connects to the office SSID but cannot obtain a usable IP address. Work is blocked.

**Triage:** Collect device/SSID, affected users, first occurrence, and business impact. Create a fictitious *Network* ticket with impact `high` and urgency `high`. The demo priority matrix maps that pair to **P1**; SLA targets are illustrative, not a company agreement.

**Support workflow in NexaDesk:**
1. Create a ticket with requester, clear subject, description, category and impact/urgency.
2. Assign a technician. The application rejects starting work while unassigned.
3. Move `Open → In progress`; record troubleshooting notes and the next action.
4. For a simulated resolution, write a concrete summary such as “Checked adapter settings, renewed DHCP lease in an authorized test environment, and verified the assigned IP and target connectivity.” This describes a *hypothetical operator action*; NexaDesk itself performs no DHCP operations.
5. Move `Resolved → Closed`, verify that resolution and event history persist, and optionally reopen for regression.

**Evidence:** [`tests/test_app.py`](../tests/test_app.py) contains `test_end_to_end_lifecycle`, `test_priority_matrix`, `test_update_and_notes` and `test_search_filters_and_csv`. Use [`README.md`](../README.md) for installation and run `python3 -m pytest -q tests` after installing dependencies.

**Verification:** correct calculated priority, valid assignment and state transitions, mandatory resolution details, history entry and CSV output. Re-test the device independently before claiming a real incident is resolved.

## Scenario 2 — Multiple incidents require prioritization

**Symptom:** Several requests arrive at once: a small cosmetic issue, a single-user sign-in issue, and an urgent work-blocking network incident.

**Approach:** Enter the requests with different impact and urgency values. Compare P1–P4 classifications, search/filter results, technician assignment and active/completed views. Review dashboard counts and export non-sensitive test ticket data.

**Verification:** automated tests cover the matrix, search, filters and CSV endpoint; the demo only represents a workflow model.

## Kurzfassung / Türkçe özet

**DE:** Zwei fiktive Helpdesk-Fälle zeigen Priorisierung, Ticketzuweisung, Bearbeitungsstatus, Lösungsdokumentation und nachvollziehbare Tests. Das System behebt selbst keine WLAN-Störung.

**TR:** İki kurgusal destek senaryosu; önceliklendirme, atama, durum yönetimi, çözüm kaydı ve raporlamayı gösterir. Uygulama ağ arızasını kendisi gidermez.

**Security:** Local-only demo without authentication/RBAC. Never expose it publicly or enter real employee/customer data.
