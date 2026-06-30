-- =============================================================================
-- DEMO DATABASE CLEANUP + FRESH SEED
-- Run against Supabase via psql or the Supabase SQL editor.
-- Deletes all demo onboarding data, keeps admin users intact,
-- then creates one fresh employee record for Srinivas Katta.
-- The Python seed script (seed_employee.py) must be run AFTER this SQL
-- to trigger the full LangGraph onboarding orchestration via the API.
-- =============================================================================

BEGIN;

-- ── 1. Delete dependent data in FK order ────────────────────────────────────

-- Orchestration events (reference workflows + employees)
DELETE FROM onboarding_orchestration_events;

-- Tasks (reference workflows)
DELETE FROM onboarding_tasks;

-- Meetings (reference employees + workflows)
DELETE FROM onboarding_meetings;

-- Workflows (reference employees)
DELETE FROM onboarding_workflows;

-- Notifications (per-user; clear all in-app notifications)
DELETE FROM notifications;

-- Employees (all demo employees; admin users live in `users`, not here)
DELETE FROM employees;

-- ── 2. Verify admin users are intact ────────────────────────────────────────
-- (No delete — admin accounts live in `users` table only)
DO $$
DECLARE
  admin_count INT;
BEGIN
  SELECT COUNT(*) INTO admin_count
  FROM users
  WHERE role IN ('admin', 'hr_admin');

  IF admin_count = 0 THEN
    RAISE WARNING 'No admin users found. Ensure at least one admin account exists in the users table.';
  ELSE
    RAISE NOTICE 'Admin users intact: %', admin_count;
  END IF;
END $$;

COMMIT;

-- ── 3. Summary ───────────────────────────────────────────────────────────────
SELECT
  (SELECT COUNT(*) FROM employees)                    AS employees,
  (SELECT COUNT(*) FROM onboarding_workflows)         AS workflows,
  (SELECT COUNT(*) FROM onboarding_tasks)             AS tasks,
  (SELECT COUNT(*) FROM onboarding_meetings)          AS meetings,
  (SELECT COUNT(*) FROM notifications)                AS notifications,
  (SELECT COUNT(*) FROM onboarding_orchestration_events) AS orchestration_events,
  (SELECT COUNT(*) FROM users WHERE role IN ('admin','hr_admin')) AS admin_users;
