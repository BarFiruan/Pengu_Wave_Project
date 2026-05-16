# PenguWave

PenguWave is a security operations portal: authenticated users browse security events, and administrators manage user accounts. The stack is a React frontend (`frontend/`) talking to a FastAPI backend (`backend/`) with a SQLite database. For a plain-language discussion of threats and mitigations, see [THREAT_MODEL.md](THREAT_MODEL.md).

## 1. How to run the project

You need **Node.js 18+**, **Python 3.11+**, and two terminal windows.

**Backend** (API on http://localhost:3001):

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env               # optional; defaults work for local dev
uvicorn app.main:app --reload --port 3001
```

Leave this terminal running. On first start, copy the **admin password** printed in this window.

Run each command on its **own line** (do not paste the whole block as one line). On macOS use `python3`, not `python`.

### Running the backend (step by step)

**First time:**

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 3001
```

You should see `Uvicorn running on http://127.0.0.1:3001`. The first run prints an admin password once in this terminal—save it.

**Every time after that** (venv already exists):

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 3001
```

**Check the backend:** open http://localhost:3001/api/health — you should see `{"ok":true}`. API docs: http://localhost:3001/docs

**Stop the backend:** click that terminal and press **Ctrl + C**. You get your shell prompt back. Stopping only ends the server; run `uvicorn` again when you want to start.

**Frontend** (UI on http://localhost:5173) — use a **second** terminal:

```bash
cd frontend
npm install
npm run dev
```

Do not run `npm run dev` from the repo root; the app lives in `frontend/`.

**Stop the frontend:** in the frontend terminal, press **Ctrl + C**.

If http://localhost:5173 still loads, Vite is probably still running in another terminal (or the terminal was closed without stopping the server). Try this:

1. Find the terminal tab that shows `VITE` or `npm run dev`, click it, and press **Ctrl + C** again.
2. Or run in any terminal to free port 5173:

```bash
lsof -ti :5173 | xargs kill
```

If it still will not stop:

```bash
lsof -ti :5173 | xargs kill -9
```

Stopping the frontend does not stop the backend on port 3001—they are independent.

Open http://localhost:5173 in your browser.

On the **first** backend start, if the database has no users yet, the server creates an admin account and prints credentials to the terminal:

- Email: `admin@penguwave.io` (override with `ADMIN_EMAIL` in `backend/.env`)
- Password: set `ADMIN_BOOTSTRAP_PASSWORD` in `.env`, or copy the random password printed once to stdout

The server also loads 50 sample events from `data/mock_events.json` into the database when the events table is empty. Data is stored in `backend/data/penguwave.db` (gitignored) and survives restarts. To confirm: log in as admin, create a user on **Users**, stop uvicorn (`Ctrl+C`), start it again, and verify the user still exists.

**Environment variables** (see `backend/.env.example`): `DATABASE_URL`, `CORS_ORIGINS`, `COOKIE_SECURE` (use `false` on localhost), `ADMIN_EMAIL`, `ADMIN_BOOTSTRAP_PASSWORD`, `ENVIRONMENT`. Session lifetime defaults to 24 hours (`session_ttl_hours` in `backend/app/config.py`).

**Tests:** `cd backend && pytest` runs security-focused API tests (auth failures, RBAC, rate limiting, mass-assignment rejection, and similar cases).

API reference: [docs/api_contract.md](docs/api_contract.md). Interactive docs: http://localhost:3001/docs while the backend is running.

## 2. How authentication works

The original assignment API contract described a **Bearer token** in the `Authorization` header. This implementation uses an **httpOnly cookie** named `sid` instead, which JavaScript cannot read—so a cross-site scripting bug is less likely to steal a session. The updated contract in `docs/api_contract.md` documents this choice.

**Sign-in flow:**

1. The browser sends `POST /api/auth/login` with `{ email, password }` and `credentials: "include"` so the cookie can be stored.
2. The backend validates the body with Pydantic, looks up the user by email (stored lowercased), and checks the password with **argon2** (a slow password-hashing algorithm designed to resist guessing).
3. On success, the server creates a row in the `session` table with a random session id (`secrets.token_hex(32)`), sets the `sid` cookie (`HttpOnly`, `SameSite=Lax`, `Path=/`, `Max-Age` from session TTL), and returns `{ "user": { id, email, role, status } }`. The response never includes a token string or a password.
4. On failure (wrong email, wrong password, or disabled account), the server always returns the same message: `"Invalid email or password"`. That avoids telling an attacker whether an email is registered (**user enumeration**).
5. Login is rate-limited to **10 requests per minute per IP** (`slowapi` on the login route).

**Staying signed in:** On load, the React app calls `GET /api/auth/me` (`frontend/src/auth/AuthContext.tsx`). The backend reads the `sid` cookie, loads the session, checks expiry, and returns the user—or **401** if the cookie is missing, expired, or tied to a disabled account.

**Sign-out:** `POST /api/auth/logout` deletes the session row and clears the cookie.

## 3. How authorization is enforced

**Role-based access control (RBAC)** means each user has a role that determines what they may do. There are three roles: `admin`, `analyst`, and `viewer`.

| Action | admin | analyst | viewer |
|--------|-------|---------|--------|
| View events (`GET /api/events`) | yes | yes | yes |
| Manage users (`/api/users` …) | yes | no | no |

**The server is the authority.** Every `/api/users` route is mounted with `dependencies=[Depends(require_role("admin"))]` on the router (`backend/app/routers/users.py`), so a single declaration protects all user-management endpoints. The `current_user` and `require_role` helpers in `backend/app/deps.py` read the session cookie first; unauthenticated callers get **401**, authenticated non-admins get **403**.

The frontend adds convenience only: `ProtectedRoute` blocks pages when not logged in, and `RequireRole` hides the **Users** link and page for non-admins. Calling the API directly (for example with `curl`) still hits the same server checks.

**Additional rules enforced in code:**

- **Mass-assignment:** `PATCH /api/users/:id` accepts only `role` and `status` via a Pydantic model with `extra="forbid"`. Extra fields such as `password_hash` are rejected with **422**.
- Passwords and hashes never appear in JSON responses.
- An admin cannot delete their own account.
- An admin cannot demote themselves to a non-admin role if they are the last active admin.

Event endpoints require any authenticated role; they use `current_user` but not `require_role("admin")`.

## 4. How I would deploy this securely in production

No deployment is included in this submission; the following is the approach I would take for a real environment.

**Transport and cookies.** Terminate **TLS** (HTTPS) at a reverse proxy (Nginx or a cloud load balancer). Set `COOKIE_SECURE=true` so the session cookie is only sent over HTTPS, and send an **HSTS** header so browsers prefer HTTPS. Restrict **CORS** to the production frontend origin only.

**Application process.** Run the API with **Gunicorn** and `UvicornWorker` workers—not `uvicorn --reload`. Run the process as a **non-root** user inside a minimal container or VM.

**Data store.** Replace SQLite with **managed PostgreSQL** (SQLModel supports this with a changed `DATABASE_URL`). Use encryption at rest, restricted network access, automated **daily backups**, and a dedicated DB user with least privilege.

**Secrets.** Load `ADMIN_BOOTSTRAP_PASSWORD`, database credentials, and similar values from a **secrets manager** (AWS Secrets Manager, HashiCorp Vault, etc.), not from a committed `.env` file. Rotate credentials on a schedule.

**Frontend hardening.** Serve the built static assets behind the same TLS front end. Add a strict **Content-Security-Policy** header to limit where scripts may run, which reduces the impact of XSS if a rendering bug ever appears.

**Operations.** Ship **structured JSON logs** (`structlog` in the backend) to a log aggregator or SIEM, with alerts on elevated 5xx rates and login-failure spikes. Run **`pip-audit`** and **`npm audit`** (or Dependabot) in CI to catch vulnerable dependencies.

For threat context and trade-offs (for example why we rely on `SameSite=Lax` instead of CSRF tokens at this scope), see [THREAT_MODEL.md](THREAT_MODEL.md).
