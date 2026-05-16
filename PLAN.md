# PenguWave — Implementation Plan

A detailed, ordered plan for turning the frontend-only PenguWave starter into a working, secure full-stack application. Written **before any code is touched**, so it doubles as a design document.

---

## 0. Assignment Context

This implements the Upwind Security take-home: *Secure Development — Backend Implementation*. Key guidelines from the assignment:

- **Submission:** a GitHub repository (or equivalent) containing all deliverables.
- **Evaluation focus:** thinking, reasoning, and approach — not just the final output.
- **Audience for docs:** a software engineer who is **not** a security specialist. Plain English, no jargon-as-mystery.
- **Explicit guideline:** *"Keep your solution clear and focused. Avoid overengineering."*

That last line is load-bearing for this plan. Every "nice to have" that doesn't directly support a graded requirement has been trimmed.

### Locked-in decisions (confirmed)

| Question | Choice |
|---|---|
| Backend stack | **Python 3.11+ + FastAPI** |
| Persistent storage | **SQLite via SQLModel** |
| Auth transport | **httpOnly + Secure + SameSite=Lax cookie** (documented deviation from the API contract) |
| Repo shape | **Monorepo** with `frontend/` + `backend/` |
| Seed admin password | **`ADMIN_BOOTSTRAP_PASSWORD` env var, random fallback printed once to stdout** |
| Events data | **Seed into DB on first run** from `data/mock_events.json` |
| Dependency manager | **`uv`** (with a generated `requirements.txt` for reviewer compatibility) |
| Test depth | **Full coverage of security-relevant paths**, not just happy-path |

---

## 1. Goals & Success Criteria

By the end of the work the project must satisfy every numbered task in the assignment:

| Task | Requirement | Delivered by |
|---|---|---|
| 1 | Threat Thinking doc (~½ page, plain English) | `THREAT_MODEL.md` |
| 2 | Login + persistent auth across pages | FastAPI auth router + `AuthContext` + `ProtectedRoute` |
| 3 | Backend API for login, users, protected endpoints | FastAPI app at `:3001` |
| 4 | Events endpoint reading the JSON, frontend wired to it | `/api/events`, rewritten `EventsPage.tsx` |
| 5 | Authorization: users can't access others' data or perform unauthorized actions | RBAC via FastAPI dependencies + frontend role guards |
| 6 | Persistent user storage | SQLite file, survives restarts |
| 7 | README covering run, auth, authorization, secure prod deployment | Rewritten `README.md` |

A reviewer should be able to clone the repo, run two commands, log in as a seeded admin, create a new user, restart the server, and still see that user.

---

## 2. Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Backend | Python 3.11 + FastAPI | Auto OpenAPI docs help the reviewer; Pydantic gives free validation |
| ASGI server | Uvicorn (dev) | Standard FastAPI pairing |
| Database | SQLite (`sqlite3` built-in) | Single file, zero setup, survives restarts |
| ORM / models | SQLModel | One typed class per table, Pydantic-compatible |
| Password hashing | `argon2-cffi` | OWASP-recommended |
| Session strategy | Server-side sessions, `sid` cookie | XSS can't steal it; logout actually invalidates |
| Validation | Pydantic with `extra="forbid"` | Blocks mass-assignment automatically |
| Rate limiting | `slowapi` | Mitigates brute force on login |
| Logging | `structlog` with field redaction | Structured JSON; no passwords ever in logs |
| CORS | `fastapi.middleware.cors.CORSMiddleware` | Allowlist `http://localhost:5173`, `allow_credentials=True` |
| Testing | `pytest` + FastAPI `TestClient` | Synchronous, easy assertions |
| Dependency manager | `uv` + generated `requirements.txt` | Fast install, but `pip install -r requirements.txt` always works |
| Lint | `ruff` | Replaces flake8/black/isort |
| Frontend state | React Context (`AuthContext`) | Avoids pulling in Redux for one slice of state |
| Frontend HTTP | `fetch` wrapper sending `credentials: "include"` | Cookies travel automatically |

### Deliberately out of scope (the "avoid overengineering" line)

- **No Docker.** Adds setup friction; SQLite + Uvicorn already runs in two commands.
- **No Alembic migrations.** `SQLModel.metadata.create_all()` on startup is enough for an assignment.
- **No Redux / Zustand.** React Context is plenty.
- **No design system / Tailwind.** Existing CSS works; we polish only what the user actually sees.
- **No 2FA, no OAuth, no SSO.** Not required by the assignment.
- **No CSRF double-submit token.** `SameSite=Lax` plus the fact that login itself is a cookie-setting POST is sufficient at this scope; we document the threat and why our defence is adequate.
- **No audit log table.** Structured logs cover this; an audit table would be a separate feature.

### Deviation from the API contract

The contract describes a Bearer token in the `Authorization` header. We switch to httpOnly cookies and document this in both `docs/api_contract.md` and the README. The contract explicitly says deviations are allowed if documented. Cookies are strictly safer than `localStorage`-stored tokens for browser apps.

---

## 3. Repository Layout (after the work)

```
PenguWaveProject/
├── README.md                     ← rewritten (Task 7)
├── THREAT_MODEL.md               ← new (Task 1)
├── PLAN.md                       ← this file
├── docs/
│   └── api_contract.md           ← updated to reflect cookie auth
├── data/
│   └── mock_events.json          ← unchanged, used to seed events table
├── frontend/                     ← all current frontend files moved here
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig*.json
│   ├── eslint.config.js
│   ├── index.html
│   ├── public/
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── App.css
│       ├── api/
│       │   ├── client.ts         ← fetch wrapper, sends cookies
│       │   ├── auth.ts
│       │   ├── users.ts
│       │   └── events.ts
│       ├── auth/
│       │   ├── AuthContext.tsx
│       │   ├── ProtectedRoute.tsx
│       │   └── RequireRole.tsx
│       ├── components/
│       │   ├── Navbar.tsx        ← shows user + Logout when authed
│       │   ├── LoginModal.tsx    ← rewritten, shows errors
│       │   └── WelcomeBanner.tsx
│       └── pages/
│           ├── EventsPage.tsx    ← rewritten, no dangerouslySetInnerHTML
│           ├── UsersPage.tsx     ← rewritten, RBAC-gated
│           └── NotFound.tsx
└── backend/                      ← new
    ├── pyproject.toml
    ├── requirements.txt          ← exported from uv for reviewer compatibility
    ├── .env.example
    ├── app/
    │   ├── __init__.py
    │   ├── main.py               ← FastAPI app factory + middleware
    │   ├── config.py             ← env vars via pydantic-settings
    │   ├── db.py                 ← SQLModel engine + session
    │   ├── models.py             ← User, Session, Event
    │   ├── schemas.py            ← request/response Pydantic models
    │   ├── security.py           ← argon2 hash/verify, cookie helpers
    │   ├── deps.py               ← current_user, require_role dependencies
    │   ├── routers/
    │   │   ├── auth.py
    │   │   ├── users.py
    │   │   └── events.py
    │   ├── seed.py               ← seeds admin + events on first run
    │   └── logging_config.py
    ├── tests/
    │   ├── conftest.py           ← pytest fixtures, in-memory DB
    │   ├── test_auth.py
    │   ├── test_users.py
    │   └── test_events.py
    └── data/
        └── penguwave.db          ← SQLite file, gitignored
```

---

## 4. Database Schema (SQLModel)

```python
# app/models.py
from datetime import datetime
from sqlmodel import SQLModel, Field
from typing import Optional

class User(SQLModel, table=True):
    id: str = Field(primary_key=True)             # uuid4 hex
    email: str = Field(unique=True, index=True)   # stored lowercased
    password_hash: str
    role: str                                     # "admin" | "analyst" | "viewer"
    status: str = "active"                        # "active" | "disabled"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Session(SQLModel, table=True):
    id: str = Field(primary_key=True)             # secrets.token_hex(32), the cookie value
    user_id: str = Field(foreign_key="user.id", index=True)
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Event(SQLModel, table=True):
    id: str = Field(primary_key=True)
    timestamp: datetime = Field(index=True)
    severity: str = Field(index=True)             # "HIGH" | "MEDIUM" | "LOW"
    title: str
    description: str
    asset_hostname: str
    asset_ip: str
    source_ip: str
    tags_json: str = "[]"                         # JSON-encoded list[str]
    user_id: Optional[str] = Field(default=None, foreign_key="user.id")
```

Closed sets (`role`, `status`, `severity`) are enforced as `Literal[...]` types in the Pydantic schemas at the API boundary. On startup, `SQLModel.metadata.create_all(engine)` creates tables if missing.

**Seeding** (`app/seed.py`):
- If `user` table is empty → create admin user, email from `ADMIN_EMAIL` env (default `admin@penguwave.io`), password from `ADMIN_BOOTSTRAP_PASSWORD` env if set, else `secrets.token_urlsafe(16)` printed once to stdout.
- If `event` table is empty → read `data/mock_events.json`, validate with Pydantic, bulk insert.

---

## 5. Authentication & Session Flow

1. Frontend posts `{email, password}` to `POST /api/auth/login` with `credentials: "include"`.
2. Backend Pydantic-validates the body. Looks up user by lowercased email. Missing or `status=="disabled"` → `401` with `{"error": "Invalid email or password"}` (identical message either way; no user enumeration).
3. `argon2.verify(stored_hash, plain_password)` — failure returns the same 401.
4. Generate `sid = secrets.token_hex(32)`. Insert a `Session` row with `expires_at = utcnow() + 24h`.
5. Set cookie: `Set-Cookie: sid=<sid>; HttpOnly; Secure; SameSite=Lax; Path=/; Max-Age=86400`.
6. Return body `{"user": {"id", "email", "role", "status"}}`. No password, no token in the body.
7. Every protected route uses a FastAPI dependency `current_user(request)`:
   - Reads the `sid` cookie
   - Looks up the `Session`, checks `expires_at > utcnow()`
   - Joins the `User`, returns it
   - Any failure → `401`
8. `GET /api/auth/me` returns the joined user (no password).
9. `POST /api/auth/logout` deletes the `Session` row and clears the cookie.

### Why server-side sessions over JWT

- Logout invalidates immediately. JWTs stay valid until expiry.
- Disabling a user takes effect immediately — just delete their sessions.
- No `alg=none` / signing-key confusion.
- Cost (one DB lookup per request) is negligible at this scale.

### Why no CSRF token

- `SameSite=Lax` blocks cross-site POST/PATCH/DELETE in every modern browser.
- The only state-changing GET is logout, which is a POST.
- Login itself sets the cookie, so a CSRF on login is meaningless.
- We document this reasoning in the threat doc instead of adding a token mechanism the reviewer would have to read through.

---

## 6. Authorization Model (RBAC)

Three roles: `admin`, `analyst`, `viewer`.

| Endpoint | admin | analyst | viewer | anon |
|---|---|---|---|---|
| `POST /api/auth/login` | ✓ | ✓ | ✓ | ✓ |
| `POST /api/auth/logout` | ✓ | ✓ | ✓ | – |
| `GET /api/auth/me` | ✓ | ✓ | ✓ | – |
| `GET /api/events` | ✓ | ✓ | ✓ | ✗ |
| `GET /api/events/:id` | ✓ | ✓ | ✓ | ✗ |
| `GET /api/users` | ✓ | ✗ | ✗ | ✗ |
| `POST /api/users` | ✓ | ✗ | ✗ | ✗ |
| `PATCH /api/users/:id` | ✓ | ✗ | ✗ | ✗ |
| `DELETE /api/users/:id` | ✓ | ✗ | ✗ | ✗ |

### Enforcement is layered, never client-only

1. **Server FastAPI dependencies** are the single source of truth. The users router declares `dependencies=[Depends(require_role("admin"))]` once, so every route under it is gated identically. The frontend cannot bypass this.
2. **Frontend route guards** (`ProtectedRoute`, `RequireRole`) hide UI for clarity. A user typing `/users` directly still hits the server, which still returns `403`.
3. **Specific defences against escalation:**
   - `PATCH /api/users/:id` uses a Pydantic schema with `model_config = ConfigDict(extra="forbid")` that only whitelists `role` and `status`. Unknown fields (like `password_hash`) are rejected during validation — **mass-assignment is impossible**.
   - An admin cannot delete themselves.
   - An admin cannot demote themselves if they are the last active admin.
   - `POST /api/users` requires admin role, so no self-promotion via account creation.

---

## 7. Security Fixes To The Existing Frontend

Every issue from the code analysis gets a tracked fix:

| Issue | File | Fix |
|---|---|---|
| XSS via search highlight | `EventsPage.tsx` | Replace `dangerouslySetInnerHTML` with plain React text + `<strong>` |
| XSS via event description | `EventsPage.tsx` | Render description as text, not HTML |
| Password in response/table | `UsersPage.tsx`, `types.ts` | Remove `password` from `User` type; remove column |
| New-user password input is `type="text"` | `UsersPage.tsx` | Change to `type="password"` |
| Hardcoded credentials in source | `UsersPage.tsx` | Delete inline array; data from API |
| `console.log("Login:", email, password)` | `api.ts`, `LoginModal.tsx` | Delete both |
| Token in `localStorage` | `api.ts` | Delete; auth state from `GET /api/auth/me` |
| Login modal swallows errors | `LoginModal.tsx` | Inline error message; close only on success |
| No route protection | `App.tsx` | Wrap protected routes in `<ProtectedRoute>` |
| Missing role check on UsersPage | `UsersPage.tsx` | `<RequireRole role="admin">` + server `403` |
| Delete uses `<a href="#">` | `UsersPage.tsx` | `<button>` with confirm |
| No logout UI | `Navbar.tsx` | Logout button when authed |

---

## 8. Frontend Improvements (deliberately minimal)

The assignment says "avoid overengineering". Frontend improvements stay at the **minimum that shows polish without ballooning the scope**:

- Show current user email + role in the Navbar
- Logout button
- Inline error message in the login modal (success/failure are visible)
- Loading state while `GET /api/auth/me` is in flight (no flicker)
- Confirm dialog before deleting a user
- Empty-state messages instead of blank tables

**Explicitly skipped** (would add code without adding evaluation signal):
- Toasts library
- Date-range filters
- Pagination UI (we add it on the backend but use a fixed page size)
- Loading skeletons
- Sortable columns

---

## 9. Phase-By-Phase Execution Plan

### Phase 0 — Pre-work
- [ ] Write `THREAT_MODEL.md` first (Task 1, explicitly ordered before coding)

### Phase 1 — Repo restructure
- [ ] Move existing frontend files into `frontend/`
- [ ] Update `.gitignore`: `backend/data/*.db`, `backend/.env`, `backend/.venv`, `__pycache__/`, `.pytest_cache/`, `node_modules/`
- [ ] Commit: "chore: restructure into monorepo with frontend/ and backend/"

### Phase 2 — Backend scaffold
- [ ] Create `backend/` with `pyproject.toml`. Deps: `fastapi`, `uvicorn[standard]`, `sqlmodel`, `argon2-cffi`, `slowapi`, `pydantic-settings`, `structlog`. Dev: `pytest`, `httpx`, `ruff`
- [ ] `app/config.py` — env vars via `pydantic-settings`
- [ ] `app/db.py` — SQLite engine, `create_all` on startup
- [ ] `app/main.py` — FastAPI app, CORS, structured logging, router mounting
- [ ] `GET /api/health` returns `{"ok": true}`
- [ ] Verify: `uvicorn app.main:app --reload --port 3001` boots cleanly

### Phase 3 — Storage seed
- [ ] On startup: empty user table → seed admin (env-var-with-random-fallback)
- [ ] On startup: empty event table → seed from `data/mock_events.json`

### Phase 4 — Auth endpoints
- [ ] `POST /api/auth/login` with Pydantic validation, argon2 verify, session row, cookie
- [ ] `GET /api/auth/me`
- [ ] `POST /api/auth/logout`
- [ ] Rate-limit `/api/auth/login` via slowapi: 10 req/min/IP
- [ ] `tests/test_auth.py`:
  - happy path
  - wrong password (generic 401)
  - disabled user (same generic 401, no enumeration)
  - missing cookie → 401
  - expired session → 401
  - rate-limit triggers → 429
  - logout invalidates session

### Phase 5 — Users CRUD (RBAC-gated)
- [ ] `GET /api/users`, `POST /api/users`, `PATCH /api/users/:id`, `DELETE /api/users/:id`
- [ ] Router with `dependencies=[Depends(require_role("admin"))]`
- [ ] Schemas with `extra="forbid"`; PATCH only allows `{role, status}`
- [ ] Email uniqueness → 400 with clear message
- [ ] Cannot delete self
- [ ] Cannot demote self if last admin
- [ ] `tests/test_users.py`:
  - admin can list/create/update/delete
  - analyst gets 403 on every users endpoint
  - viewer gets 403
  - anon gets 401
  - password never appears in any response (explicit assertion)
  - mass-assignment attempt with extra field → 422
  - last admin protection works
  - duplicate email → 400

### Phase 6 — Events endpoints
- [ ] `GET /api/events` with `?severity=&search=&limit=&offset=`
- [ ] `GET /api/events/:id` with 404 fallback
- [ ] Both require auth, any role
- [ ] `tests/test_events.py`:
  - anon → 401
  - authed user → 200, returns list
  - filtering works
  - not-found → 404

### Phase 7 — Frontend rewire
- [ ] `api/client.ts` — fetch wrapper with `credentials: "include"`, typed `ApiError`
- [ ] `AuthContext` — calls `/me` on mount, exposes `user`, `login`, `logout`, `isLoading`
- [ ] `ProtectedRoute` — renders login modal blocker if `!user`
- [ ] `RequireRole` — admin-only guard
- [ ] Rewrite `LoginModal` — uses `AuthContext.login`, shows errors, closes only on success
- [ ] Rewrite `EventsPage` — fetches `/api/events`, no `innerHTML` anywhere
- [ ] Rewrite `UsersPage` — fetches `/api/users`, no password column, admin-gated
- [ ] Update `Navbar` — show user + logout when authed
- [ ] Verify in browser: login → see events → /users blocked as analyst, allowed as admin → restart server → still works

### Phase 8 — Documentation
- [ ] `THREAT_MODEL.md` — finalised with cross-references to the actual code
- [ ] `README.md` — rewritten: prerequisites, how to run, env vars, seeded admin instructions, auth flow, RBAC enforcement, secure-deployment-in-production section. Audience: a generalist software engineer.
- [ ] `docs/api_contract.md` — updated to reflect cookie auth + the actual response shapes

### Phase 9 — Self-review
- [ ] Re-read `THREAT_MODEL.md` — each mitigation traceable to code
- [ ] `ruff check`, `pytest`, `npm run lint` all clean
- [ ] Manual attack attempts: SQL injection in email, oversize JSON body, PATCH another user as analyst, IDOR on `/api/users/<x>`, attempt to escalate own role
- [ ] Clean git history: meaningful commit messages, no `wip` commits, no `console.log` left behind
- [ ] Push to GitHub, verify README renders, repo link ready for submission

---

## 10. Threat Model — What `THREAT_MODEL.md` Will Cover

Roughly half a page, plain English (the audience is a non-security generalist):

1. **What's worth protecting** — security-event data (internal hostnames, IPs, incident details), user accounts (especially admin), session cookies.
2. **Who might attack it** — external attacker with no credentials; a malicious or compromised analyst trying to escalate; a curious user trying to read events not addressed to them.
3. **What they might try, and how we stop it:**
   - *Stealing passwords* → argon2 hashing, rate limiting on login, generic error message (no user enumeration), never logged.
   - *Stealing the session cookie* → httpOnly + Secure + SameSite=Lax, short expiry, server-side revocation on logout.
   - *Escalating from analyst to admin* → server-side role check on every users route, `extra="forbid"` on PATCH schema (no mass assignment), last-admin protection.
   - *Injecting JavaScript (XSS)* → no `dangerouslySetInnerHTML` / `innerHTML` anywhere in the new frontend; React's default text rendering escapes content.
   - *CSRF (forging requests from another site)* → SameSite=Lax cookie blocks it; explained in the doc.
   - *Brute-forcing logins* → slowapi rate limit, 10/min/IP.
   - *Leaking passwords in responses or logs* → server schemas explicitly exclude `password_hash`; structlog redaction strips known fields.
4. **What's intentionally out of scope** — TLS termination, WAF, SIEM forwarding, network segmentation, 2FA. Acknowledged so the reviewer sees we made conscious trade-offs.

---

## 11. README — What It Will Cover (Task 7)

The assignment requires these four sections, written for a generalist:

1. **How to run the project** — clone, `cd backend && uv pip install -r requirements.txt && uvicorn app.main:app --port 3001` and `cd frontend && npm install && npm run dev`. The seeded admin credentials.
2. **How authentication works** — login form posts to backend, server verifies argon2 hash, sets httpOnly cookie, frontend trusts `/api/auth/me`. Logout deletes the session row.
3. **How authorization is enforced** — three roles, FastAPI dependency gates every users route on the server, frontend `RequireRole` hides UI but is not the security boundary.
4. **How I'd deploy this securely in production** — TLS everywhere (HSTS, Secure cookies), reverse proxy with Gunicorn + UvicornWorkers, secrets from a manager (not env files), swap SQLite for managed Postgres, structured logs to a SIEM, CSP header, `pip-audit` in CI, run as non-root, daily DB backups.

---

## 12. What To Drop If Time Runs Out

Listed so we know what to cut first if scope pressure builds up:

1. **Slowapi rate limiting on login** — keep the test, drop the implementation. Document in the threat doc as "would add in production".
2. **Pagination + filtering on `/api/events`** — return all 50 events unfiltered; the frontend does the filtering.
3. **`structlog` with redaction** — fall back to stdlib `logging`. Note in threat doc.
4. **Last-admin demotion protection** — simpler "cannot delete self" only.
5. **Frontend `confirm()` dialogs** — silent delete.

What we **never** drop, because they are the assignment:
- Threat model doc
- Real authentication (cookie + argon2)
- RBAC enforcement on the server
- Password never in any response
- No XSS sinks in the new frontend
- Persistent storage of users
- README with the four required sections

---

## 13. Estimated Effort

| Phase | Effort |
|---|---|
| 0 — Threat model | 30 min |
| 1 — Repo restructure | 15 min |
| 2 — Backend scaffold | 30 min |
| 3 — Seed | 20 min |
| 4 — Auth + tests | 1 h 15 min |
| 5 — Users CRUD + RBAC + tests | 1 h 15 min |
| 6 — Events + tests | 30 min |
| 7 — Frontend rewire | 1 h 30 min |
| 8 — Documentation | 45 min |
| 9 — Self-review | 30 min |
| **Total** | **~7 hours of focused work** |

---

## Next Step

Phase 0: write `THREAT_MODEL.md`. That's the next concrete artefact; no code until it's done.
