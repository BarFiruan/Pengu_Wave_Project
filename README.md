# PenguWave

A security operations portal. Analysts read a feed of security events. Admins manage user accounts.

This is a take-home submission. The frontend was provided as a starter; the FastAPI backend and auth/RBAC plumbing were built on top of it.

## How to run the project

You need Node 18+ and Python 3.11+. Open two terminals.

**Backend** (port 3001):

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 3001
```

The first time the server starts it creates a SQLite database at `backend/data/penguwave.db`, loads the 50 sample events from `data/mock_events.json`, and creates an admin user. If you haven't set `ADMIN_BOOTSTRAP_PASSWORD` in `backend/.env`, a random password is printed once to this terminal — copy it. Default admin email is `admin@penguwave.io`.

**Frontend** (port 5173, in a second terminal):

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 and sign in with the admin email and the printed password. To run the tests: `cd backend && pytest`.

The database file persists between restarts, so users you create stay around. Environment variables are documented in `backend/.env.example`.

## How authentication works

Logging in is a `POST /api/auth/login` with email and password. The server checks the password against an **argon2** hash (a slow password-hashing algorithm designed to resist guessing). On success it does three things:

1. Creates a row in the `sessions` table with a random 32-byte id and a 24-hour expiry.
2. Returns a cookie: `Set-Cookie: sid=<random>; HttpOnly; SameSite=Lax; Path=/; Max-Age=86400`.
3. Returns the user's basic info in the body. The password is never in the response.

Every following request includes that cookie automatically — the frontend uses `credentials: "include"`, so the browser handles it. The server looks the cookie up, checks the expiry, and attaches the user to the request. Logout deletes the row and clears the cookie, so the session is gone immediately, not just expired in the future.

Two properties matter:

- **`HttpOnly` means JavaScript can never read the cookie.** Even if a cross-site scripting (XSS) bug slipped in, no script on the page can steal the session.
- **The server is the only thing that decides "logged in".** The frontend just calls `GET /api/auth/me` to find out who you are. It doesn't trust anything stored in the browser.

Login is rate-limited to 10 attempts per minute per IP. Every failure returns the same generic `"Invalid email or password"` — whether the email exists, the password is wrong, or the account is disabled — so the response can't be used to enumerate accounts.

## How authorization is enforced

There are three roles: `admin`, `analyst`, and `viewer`. Logged-in users with any role can read events. Only admins can manage users.

The check lives on the **server**, not in the frontend. The users router declares it once at the top:

```python
router = APIRouter(
    prefix="/api/users",
    dependencies=[Depends(require_role("admin"))],
)
```

Every route under `/api/users` inherits this. A non-admin hitting any of them gets `403`. The frontend has a `RequireRole` component that hides the Users page from non-admins, but that's only convenience — a user typing `/users` into the URL or calling the API with `curl` still gets the same `403`.

Two extra protections against role abuse:

- **No mass-assignment.** `PATCH /api/users/:id` only accepts `role` and `status`. Sending something like `{"role": "admin", "password_hash": "haha"}` is rejected with `422` before any handler code runs.
- **No locking yourself out.** An admin cannot delete themselves, and cannot demote themselves if they are the last active admin.

Passwords and password hashes are never returned in any response — every user-returning endpoint uses a public schema that simply doesn't have a password field.

## How I'd deploy this securely in production

The code already does the security-critical work. Production is mostly about wrapping it in real infrastructure.

**TLS everywhere.** Put the app behind a load balancer that terminates HTTPS. Turn on `COOKIE_SECURE=true` so the browser refuses to send the session cookie over plain HTTP, and add an HSTS header at the load balancer.

**Run the backend properly.** Replace `uvicorn --reload` with `gunicorn -k uvicorn.workers.UvicornWorker -w 4`, running as a non-root user inside a minimal container image.

**Real database.** Swap SQLite for managed Postgres (RDS or Cloud SQL). SQLModel makes the switch a one-line change to `DATABASE_URL`. The database lives in a private subnet, has encryption at rest and in transit, and gets daily backups with a tested restore process.

**Real secrets.** No `.env` files in production. Pull database credentials, signing keys, and the admin bootstrap password from a secrets manager (AWS Secrets Manager, HashiCorp Vault). The container image contains no secrets.

**Frontend behind a CDN.** Build the static output with `npm run build` and serve it from a CDN. The CDN adds a strict `Content-Security-Policy` header that disallows inline scripts — that's the safety net if anyone ever accidentally reintroduces an XSS sink.

**Observability.** Ship the structured JSON logs (already produced by `structlog`) to a SIEM. Expose Prometheus metrics. Alert on a 5xx spike, a login-failure spike, and on every `PATCH` or `DELETE` to `/api/users/*` — admin actions on accounts are worth knowing about even when legitimate.

**Rate limiting at scale.** The current limiter keeps counts in process memory. With multiple workers it needs Redis as a shared backend so all replicas share the same counter.

**CI gates.** Run `pip-audit`, `npm audit`, container scanning, `pytest`, and lint on every push. Block merges on HIGH or CRITICAL CVEs. Dependabot keeps things up to date.
