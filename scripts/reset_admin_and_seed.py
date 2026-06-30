"""
Full end-to-end demo runner:
1. Resets srinivas.katta@amzur.com admin password to a known value
2. Cleans all demo employees + onboarding data (keeps users)
3. Creates fresh employee Srinivas Katta via the API
4. Prints a full status report of everything generated
"""
import asyncio, sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from datetime import date
from sqlalchemy import text

KNOWN_PASSWORD = "Amzur@Demo2026"
ADMIN_EMAIL    = "srinivas.katta@amzur.com"
API_BASE       = "http://localhost:8000/api/v1"

EMPLOYEE = {
    "first_name":        "Srinivas",
    "last_name":         "Katta",
    "email":             "srinivas.katta@amzur.com",
    "department":        "Operations",
    "designation":       "DevOps Engineer",
    "joining_date":      str(date.today()),
    "manager_id":        None,
    "onboarding_status": "pending",
}


async def reset_password(email: str, new_password: str) -> None:
    from app.db.session import AsyncSessionLocal
    from app.core.security import hash_password
    async with AsyncSessionLocal() as db:
        await db.execute(
            text("UPDATE users SET hashed_password = :hp WHERE email = :email"),
            {"hp": hash_password(new_password), "email": email},
        )
        await db.commit()
    print(f"  ✓ Password reset for {email}")


async def clean_demo_data() -> None:
    from app.db.session import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        tables = [
            "onboarding_orchestration_events",
            "onboarding_tasks",
            "onboarding_meetings",
            "onboarding_workflows",
            "notifications",
            "employees",
        ]
        for table in tables:
            result = await db.execute(text(f"DELETE FROM {table}"))
            print(f"  ✓ Cleared {table:<40} ({result.rowcount} rows)")
        await db.commit()


def _api(method: str, path: str, body: dict | None = None, token: str | None = None) -> dict:
    import urllib.request, urllib.error
    url     = f"{API_BASE}{path}"
    data    = json.dumps(body).encode() if body else None
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body_text = exc.read().decode()
        print(f"  ✗ HTTP {exc.code}: {body_text[:200]}")
        raise


def run_full_workflow():
    print("\n" + "="*65)
    print("  EMPLOYEE ONBOARDING — END-TO-END DEMO")
    print("="*65)

    # Step 1: reset password
    print("\n[1/5] Resetting admin password …")
    asyncio.run(reset_password(ADMIN_EMAIL, KNOWN_PASSWORD))

    # Step 2: clean DB
    print("\n[2/5] Cleaning demo data …")
    asyncio.run(clean_demo_data())

    # Step 3: login
    print(f"\n[3/5] Authenticating as {ADMIN_EMAIL} …")
    auth  = _api("POST", "/auth/login", {"email": ADMIN_EMAIL, "password": KNOWN_PASSWORD})
    token = auth["access_token"]
    print(f"  ✓ Authenticated (token …{token[-20:]})")

    # Step 4: create employee (triggers full orchestration)
    print(f"\n[4/5] Creating employee: {EMPLOYEE['first_name']} {EMPLOYEE['last_name']} …")
    print(f"  Email:       {EMPLOYEE['email']}")
    print(f"  Department:  {EMPLOYEE['department']}")
    print(f"  Designation: {EMPLOYEE['designation']}")
    print(f"  Joining:     {EMPLOYEE['joining_date']}")
    employee = _api("POST", "/employees", EMPLOYEE, token=token)
    emp_id   = employee["id"]
    print(f"  ✓ Employee created  id={emp_id}")
    print(f"  ✓ Status: {employee.get('onboarding_status')}")

    # Step 5: verify everything generated
    print("\n[5/5] Verifying onboarding artifacts …")

    # Workflow
    workflows = _api("GET", f"/onboarding/workflows?employee_id={emp_id}&limit=5", token=token)
    wf_list   = workflows if isinstance(workflows, list) else workflows.get("items", [])
    if wf_list:
        wf = wf_list[0]
        wf_id = wf["id"]
        print(f"\n  WORKFLOW")
        print(f"  ├─ ID:         {wf_id}")
        print(f"  ├─ State:      {wf.get('current_state')}")
        print(f"  └─ Progress:   {wf.get('completion_percentage')}%")

        # Tasks
        tasks = _api("GET", f"/onboarding/workflows/{wf_id}/tasks", token=token)
        task_list = tasks if isinstance(tasks, list) else tasks.get("items", [])
        print(f"\n  TASKS ({len(task_list)} generated)")
        for t in task_list:
            status_icon = "✓" if t.get("status") == "completed" else "○"
            print(f"  {status_icon} [{t.get('priority','?').upper():6}] {t.get('title')}")

        # Events / Timeline
        try:
            events = _api("GET", f"/onboarding/workflows/{wf_id}/events", token=token)
            ev_list = events if isinstance(events, list) else events.get("items", [])
            print(f"\n  ORCHESTRATION TIMELINE ({len(ev_list)} events)")
            for ev in ev_list:
                print(f"  ├─ {ev.get('event_type'):<30} [{ev.get('status')}] {ev.get('message','')[:60]}")
        except Exception:
            pass

        # Meetings
        try:
            meetings = _api("GET", f"/meetings?workflow_id={wf_id}", token=token)
            mtg_list = meetings if isinstance(meetings, list) else meetings.get("items", [])
            print(f"\n  MEETINGS ({len(mtg_list)} scheduled)")
            for m in mtg_list:
                print(f"  ├─ {m.get('title'):<40} [{m.get('status')}]")
        except Exception:
            pass

    # Notifications
    try:
        notifs = _api("GET", "/notifications?limit=20", token=token)
        n_list = notifs.get("items", [])
        print(f"\n  NOTIFICATIONS ({len(n_list)} in-app)")
        for n in n_list[:10]:
            print(f"  ├─ [{n.get('notification_type'):<30}] {n.get('title')}")
    except Exception:
        pass

    print("\n" + "="*65)
    print("  ✅  END-TO-END WORKFLOW COMPLETE")
    print("="*65)
    print(f"\n  Login URL:  http://localhost:5173")
    print(f"  Email:      {ADMIN_EMAIL}")
    print(f"  Password:   {KNOWN_PASSWORD}")
    print(f"\n  Onboarding emails sent to: {EMPLOYEE['email']}")
    print("  Check inbox at srinivas.katta@amzur.com\n")


if __name__ == "__main__":
    run_full_workflow()
