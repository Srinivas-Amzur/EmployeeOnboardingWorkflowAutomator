"""
Seed script — creates Srinivas Katta as the single fresh demo employee.

Run AFTER cleanup_and_seed.sql has been applied.

Usage:
    cd backend
    python ../scripts/seed_employee.py

The script authenticates as the admin user, creates the employee via the
REST API (which automatically triggers the full LangGraph onboarding
orchestration, tasks, notifications, meetings, and audit events), then
verifies the result.
"""

from __future__ import annotations

import os
import sys
import json
from datetime import date
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


# ── Configuration ─────────────────────────────────────────────────────────────

API_BASE   = os.getenv("API_BASE",   "http://localhost:8000/api/v1")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@amzur.com")
ADMIN_PWD   = os.getenv("ADMIN_PWD",   "")   # set via env var or prompt below

EMPLOYEE = {
    "first_name":   "Srinivas",
    "last_name":    "Katta",
    "email":        "srinivas.katta@amzur.com",
    "department":   "Operations",
    "designation":  "DevOps Engineer",
    "joining_date": str(date.today()),   # today's date — always fresh
    "manager_id":   None,
    "onboarding_status": "pending",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _post(url: str, body: dict, token: str | None = None) -> dict:
    data    = json.dumps(body).encode()
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(url, data=data, headers=headers, method="POST")
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except HTTPError as exc:
        body_text = exc.read().decode()
        print(f"[ERROR] HTTP {exc.code} {exc.reason} → {body_text}", file=sys.stderr)
        sys.exit(1)
    except URLError as exc:
        print(f"[ERROR] Cannot reach {url}: {exc.reason}", file=sys.stderr)
        sys.exit(1)


def _get(url: str, token: str) -> dict | list:
    headers = {"Accept": "application/json", "Authorization": f"Bearer {token}"}
    req = Request(url, headers=headers, method="GET")
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except HTTPError as exc:
        body_text = exc.read().decode()
        print(f"[ERROR] HTTP {exc.code} {exc.reason} → {body_text}", file=sys.stderr)
        sys.exit(1)
    except URLError as exc:
        print(f"[ERROR] Cannot reach {url}: {exc.reason}", file=sys.stderr)
        sys.exit(1)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    global ADMIN_PWD  # noqa: PLW0603
    if not ADMIN_PWD:
        import getpass
        ADMIN_PWD = getpass.getpass(f"Password for {ADMIN_EMAIL}: ")

    print(f"[1/4] Authenticating as {ADMIN_EMAIL} …")
    auth = _post(f"{API_BASE}/auth/login", {"email": ADMIN_EMAIL, "password": ADMIN_PWD})
    token: str = auth.get("access_token", "")
    if not token:
        print("[ERROR] No access_token in login response.", file=sys.stderr)
        sys.exit(1)
    print("      ✓ Authenticated")

    print(f"[2/4] Creating employee: {EMPLOYEE['first_name']} {EMPLOYEE['last_name']} …")
    employee = _post(f"{API_BASE}/employees", EMPLOYEE, token=token)
    emp_id   = employee.get("id", "")
    print(f"      ✓ Employee created  id={emp_id}")
    print(f"      email       = {employee.get('email')}")
    print(f"      department  = {employee.get('department')}")
    print(f"      designation = {employee.get('designation')}")
    print(f"      status      = {employee.get('onboarding_status')}")
    print(f"      joining     = {employee.get('joining_date')}")

    print("[3/4] Verifying workflows were auto-generated …")
    workflows = _get(f"{API_BASE}/onboarding/workflows?employee_id={emp_id}&limit=5", token=token)
    items     = workflows if isinstance(workflows, list) else workflows.get("items", [])
    if not items:
        print("[WARNING] No workflows found yet — orchestration may still be running.")
    else:
        wf = items[0]
        print(f"      ✓ Workflow  id={wf.get('id')}")
        print(f"      state      = {wf.get('current_state')}")
        print(f"      completion = {wf.get('completion_percentage')}%")

        tasks = _get(f"{API_BASE}/onboarding/workflows/{wf['id']}/tasks", token=token)
        task_list = tasks if isinstance(tasks, list) else tasks.get("items", [])
        print(f"      tasks      = {len(task_list)}")

    print("[4/4] Seed complete.")
    print()
    print("  Next steps:")
    print("  ─ Open the app and log in as admin")
    print("  ─ Navigate to Workflows — Srinivas Katta should be the only employee")
    print("  ─ All pages (Dashboard, Analytics, Audit Logs) should reflect clean data")


if __name__ == "__main__":
    main()
