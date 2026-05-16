# PenguWave Threat Model

This document explains what we protect, who might attack it, and how the application defends itself. It is written for software engineers who are not security specialists.

## What is worth protecting

1. **Security event data** — hostnames, IP addresses, incident titles and descriptions. This is sensitive operational data.
2. **User accounts** — especially admin accounts that can create, modify, or delete other users.
3. **Session cookies** — a stolen cookie lets an attacker act as that user until the session expires or is revoked.

## Who might attack it

| Actor | Goal |
|-------|------|
| External attacker (no account) | Guess credentials, brute-force login, or probe for unauthenticated API access |
| Malicious or compromised analyst | Escalate to admin to manage users or change roles |
| Curious authenticated user | Access admin-only endpoints or another user's data |

## Threats and mitigations

### Stealing passwords

**Attack:** Guess or brute-force login; harvest passwords from logs or API responses.

**Mitigations:**
- Passwords stored with **argon2** hashing ([`backend/app/security.py`](backend/app/security.py))
- Login rate-limited to **10 requests per minute per IP** (`slowapi` on `POST /api/auth/login`)
- Failed login returns a **generic** `"Invalid email or password"` — same message for wrong email, wrong password, or disabled account (no user enumeration)
- Passwords and hashes are **never** returned in API responses; response schemas exclude `password_hash`
- Structured logging **redacts** known sensitive fields (`backend/app/logging_config.py`)

### Stealing the session cookie

**Attack:** XSS or malware reads a token from browser storage and replays it.

**Mitigations:**
- Sessions use an **httpOnly** cookie (`sid`) — JavaScript cannot read it
- **SameSite=Lax** limits cross-site cookie sending
- **Secure** flag enabled in production (disabled on `http://localhost` for local dev)
- Sessions expire after **24 hours** and are **deleted on logout** (server-side revocation)
- Disabling a user can invalidate their sessions immediately

### Privilege escalation (analyst → admin)

**Attack:** Call user-management APIs or send extra fields in PATCH requests to change `role`.

**Mitigations:**
- All `/api/users` routes require **admin** role via FastAPI dependencies ([`backend/app/deps.py`](backend/app/deps.py), [`backend/app/routers/users.py`](backend/app/routers/users.py)) — the server is the authority, not the UI
- PATCH body schema allows only `role` and `status` with **`extra="forbid"`** ([`backend/app/schemas.py`](backend/app/schemas.py)) — unknown fields (e.g. `password_hash`) are rejected
- Admin **cannot delete themselves** or demote themselves if they are the **last active admin**

### Cross-site scripting (XSS)

**Attack:** Malicious content in event descriptions or search terms runs as script in the browser.

**Mitigations:**
- Frontend renders user-controlled text with **React's default escaping** — no `dangerouslySetInnerHTML` or `innerHTML` ([`frontend/src/pages/EventsPage.tsx`](frontend/src/pages/EventsPage.tsx))

### Cross-site request forgery (CSRF)

**Attack:** A malicious site tricks the browser into sending authenticated requests.

**Mitigations:**
- **SameSite=Lax** on the session cookie blocks cross-site POST/PATCH/DELETE in modern browsers
- Logout is POST-only; login CSRF is not meaningful (attacker would log the victim into the attacker's account)
- We document this trade-off instead of adding a CSRF token for this assignment scope

### Unauthorized API access

**Attack:** Call `/api/events` or `/api/users` without a valid session.

**Mitigations:**
- Protected routes use a **`current_user`** dependency ([`backend/app/deps.py`](backend/app/deps.py)) that validates the session cookie and returns **401** if missing or expired
- User management returns **403** for authenticated non-admin roles

## Intentionally out of scope

These are acknowledged gaps suitable for a take-home, not oversights:

- TLS termination, HSTS, and WAF (assumed at the reverse proxy in production)
- Two-factor authentication or SSO
- Dedicated audit-log table (structured application logs instead)
- CSRF double-submit tokens (SameSite=Lax deemed sufficient here)
- Network segmentation and SIEM integration

Production deployment guidance (TLS, secrets management, Postgres, CSP, non-root containers) is covered in `README.md`.
