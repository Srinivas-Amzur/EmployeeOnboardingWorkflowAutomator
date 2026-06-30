# Security Architecture

# Security Principles

The platform follows enterprise-grade security practices.

Goals:
- protect employee data
- secure authentication
- prevent unauthorized access
- secure file uploads
- protect AI workflows

---

# Authentication

## JWT Authentication

Authentication uses:
- JWT tokens
- httpOnly cookies
- secure cookie handling

Cookie Rules:
- httpOnly=true
- SameSite=Lax
- secure=true in production

---

# Authorization

## RBAC

Supported Roles:
- hr_admin
- it_admin
- manager
- employee

---

# Password Security

Passwords:
- bcrypt hashing
- never plaintext
- minimum length validation

---

# File Upload Security

Rules:
- MIME validation
- upload size limits
- extension not trusted
- files stored on disk only

Allowed Types:
- PDF
- DOCX
- PNG
- JPEG

---

# API Security

Standards:
- protected routes require auth
- validation via Pydantic
- structured error responses

---

# AI Security

All AI calls:
- route through LiteLLM proxy
- include user metadata
- avoid PII logging

---

# Database Security

Rules:
- parameterized queries
- ORM-only access
- no raw SQL from users

---

# Audit Logging

Track:
- login activity
- onboarding actions
- document uploads
- AI interactions

---

# Secrets Management

Use:
- environment variables only

Never:
- hardcode secrets
- commit credentials