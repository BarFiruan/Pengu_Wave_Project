# PenguWave API Contract

Base URL: `http://localhost:3001`

**Authentication note:** This implementation uses an **httpOnly session cookie** (`sid`) instead of a Bearer token in the `Authorization` header. Send `credentials: "include"` from the browser (or forward cookies in server-side clients). Logout invalidates the session server-side.

---

## Authentication

### `POST /api/auth/login`

Authenticate a user and start a session.

- **Body:** `{ "email": "...", "password": "..." }`
- **Success (200):**
  ```json
  {
    "user": { "id": "...", "email": "...", "role": "admin|analyst|viewer", "status": "active|disabled" }
  }
  ```
- **Set-Cookie:** `sid=<session-id>; HttpOnly; SameSite=Lax; Path=/; Max-Age=86400` (+ `Secure` in production)
- **Invalid credentials (401):**
  ```json
  { "error": "Invalid email or password" }
  ```
- **Rate limited (429):** 10 requests per minute per IP

### `POST /api/auth/logout`

End the current session. Requires session cookie.

- **Success (200):** `{ "message": "Logged out" }`

### `GET /api/auth/me`

Get the currently authenticated user's info. Requires session cookie.

- **Success (200):**
  ```json
  { "id": "...", "email": "...", "role": "...", "status": "..." }
  ```
- **Not authenticated (401):**
  ```json
  { "error": "Authentication required" }
  ```

---

## Events

All event endpoints require authentication (any role).

### `GET /api/events`

Returns security events.

- **Query (optional):** `severity`, `search`, `limit` (default 100), `offset` (default 0)
- **Success (200):**
  ```json
  [
    {
      "id": "evt-001",
      "timestamp": "2025-02-18T14:32:01Z",
      "severity": "HIGH",
      "title": "...",
      "description": "...",
      "assetHostname": "...",
      "assetIp": "...",
      "sourceIp": "...",
      "tags": ["..."],
      "userId": "usr-002"
    }
  ]
  ```

### `GET /api/events/:id`

Returns a single event by ID.

- **Success (200):** Single event object (same shape as above)
- **Not found (404):** `{ "error": "Event not found" }`

---

## Users

User management endpoints require the **admin** role and a valid session cookie.

### `GET /api/users`

Returns the list of users. Passwords are **never** included.

- **Success (200):**
  ```json
  [
    { "id": "...", "email": "...", "role": "admin", "status": "active" }
  ]
  ```

### `POST /api/users`

Create a new user.

- **Body:** `{ "email": "...", "password": "...", "role": "admin|analyst|viewer" }`
- **Success (201):** The created user (without password)
- **Validation error (400):** `{ "error": "Email already in use" }`

### `PATCH /api/users/:id`

Update a user's role or status. Only `role` and `status` are accepted; extra fields are rejected.

- **Body:** `{ "role": "..." }` and/or `{ "status": "..." }`
- **Success (200):** The updated user
- **Not found (404):** `{ "error": "User not found" }`

### `DELETE /api/users/:id`

Delete a user. Cannot delete yourself or the last active admin.

- **Success (200):** `{ "message": "User deleted" }`
- **Not found (404):** `{ "error": "User not found" }`

---

## Health

### `GET /api/health`

- **Success (200):** `{ "ok": true }`

---

## Error Responses

Errors use a consistent JSON shape:

```json
{ "error": "Human-readable error message" }
```

Common status codes:

- `200` — Success
- `201` — Created
- `400` — Bad request / validation error
- `401` — Not authenticated
- `403` — Not authorized (wrong role)
- `404` — Resource not found
- `429` — Rate limited (login)
- `422` — Request body validation failed (e.g. unknown fields on PATCH)
