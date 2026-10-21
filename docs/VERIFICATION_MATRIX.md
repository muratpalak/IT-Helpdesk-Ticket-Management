# Verification matrix — NexaDesk Glass

**Data:** synthetic tickets only. **Status vocabulary:** *automated* means the listed test is included in the repository and is run by its configured test command. Inspect the latest GitHub Actions run for its actual result. *Manual review* is an instruction, not a claim it has passed.

| ID | Situation / input | Expected behaviour | Evidence |
| --- | --- | --- | --- |
| HD-01 | Wi-Fi incident impact=high, urgency=high | P1; calendar-hour target generated | `tests/test_app.py::test_priority_matrix` (automated) |
| HD-02 | Start ticket without assignment | HTTP 409, state unchanged | `tests/test_app.py::test_end_to_end_lifecycle` (automated) |
| HD-03 | Assign, start, resolve and close with meaningful resolution | Correct state; event history retained | `tests/test_app.py::test_end_to_end_lifecycle` (automated) |
| HD-04 | Change impact/urgency while open | Recalculate P-level and target time | `tests/test_app.py::test_update_and_notes` (automated) |
| HD-05 | Wrong category, malformed email or blank subject | Reject with HTTP 422 | `tests/test_app.py::test_invalid_and_missing_input` (automated) |
| HD-06 | Search and filter while exporting CSV | Matching records and CSV response | `tests/test_app.py::test_search_filters_and_csv` (automated) |
| HD-07 | No notes or invalid workflow operations | No silent closure or lost history | `tests/test_recruiter_regressions.py` (new regression coverage) |
| HD-08 | Browser at 375px wide | Check navigation, layout and keyboard accessibility | Manual review; **not yet certified** |

## Running the checks

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt pytest httpx
python -m pytest -q tests
```

**Expected**: exit code 0 and no failed tests on a compatible environment. **Actual**: follow the repository's latest Actions run; do not treat this matrix as a test report.

## Support-case reasoning (simulation)

**Symptoms:** A notebook intermittently fails to obtain Wi-Fi access. **Triage:** determine one device vs many, check link state, DHCP assignment, SSID, network scope and authorised access. **Record:** impact/urgency → P-level, technician, notes, verification/closure. **Escalation:** network infrastructure fault affecting multiple users.

**Privacy:** Any person, address or ticket in the demo is invented, not from an employer.
