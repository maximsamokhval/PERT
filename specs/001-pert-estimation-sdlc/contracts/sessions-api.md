# API Contract: Sessions

**Feature**: `001-pert-estimation-sdlc`
**Purpose**: Contract for session management endpoints
**Generated from**: FastAPI OpenAPI spec (backend authority)

---

## Endpoints

### `POST /api/sessions`

**Create new estimation session**

**Request**:
```json
{
  "title": "Q2 2026 Feature Estimation",
  "description": "Initial estimation for new features",
  "focus_factor": 0.8,
  "hours_per_day": 8
}
```

**Response** (`201 Created`):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "00000000-0000-0000-0000-000000000001",
  "title": "Q2 2026 Feature Estimation",
  "description": "Initial estimation for new features",
  "status": "draft",
  "focus_factor": 0.8,
  "hours_per_day": 8,
  "created_at": "2026-04-02T10:00:00Z",
  "updated_at": "2026-04-02T10:00:00Z",
  "approved_at": null,
  "items": [],
  "aggregates": {
    "total_effort": 0,
    "duration_days": 0,
    "buffer_95": 0
  }
}
```

**Errors**:
- `401 Unauthorized` — Invalid or missing JWT token
- `400 Bad Request` — Validation error (missing title, invalid FF range)

---

### `GET /api/sessions/{session_id}`

**Get session by ID with all items**

**Response** (`200 OK`):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "00000000-0000-0000-0000-000000000001",
  "title": "Q2 2026 Feature Estimation",
  "description": "Initial estimation for new features",
  "status": "draft",
  "focus_factor": 0.8,
  "hours_per_day": 8,
  "created_at": "2026-04-02T10:00:00Z",
  "updated_at": "2026-04-02T10:00:00Z",
  "approved_at": null,
  "items": [
    {
      "id": "item-uuid-1",
      "session_id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Implement authentication",
      "description": "JWT-based auth with refresh tokens",
      "optimistic": 4,
      "most_likely": 8,
      "pessimistic": 12,
      "t_expected": 8.0,
      "spread": 8,
      "sigma": 1.333,
      "variance": 1.777,
      "hidden_reserve": 0.8,
      "total_effort": 8.8,
      "tracker_issue_id": null,
      "export_status": "not_exported",
      "created_at": "2026-04-02T10:05:00Z",
      "updated_at": "2026-04-02T10:05:00Z"
    }
  ],
  "aggregates": {
    "total_effort": 8.8,
    "total_variance": 1.777,
    "sigma_total": 1.333,
    "buffer_95": 2.193,
    "duration_days": 1.375
  }
}
```

**Errors**:
- `404 Not Found` — Session not found
- `401 Unauthorized` — Invalid or missing JWT token
- `403 Forbidden` — User doesn't own this session (viewer restriction)

---

### `PATCH /api/sessions/{session_id}`

**Update session metadata**

**Request**:
```json
{
  "title": "Updated Title",
  "focus_factor": 0.8
}
```

**Response** (`200 OK`): Same structure as GET

**Errors**:
- `404 Not Found` — Session not found
- `400 Bad Request` — Validation error (FF out of range)
- `403 Forbidden` — Cannot modify approved session
- `401 Unauthorized` — Invalid or missing JWT token

---

### `DELETE /api/sessions/{session_id}`

**Delete session (soft delete or hard delete based on config)**

**Response** (`204 No Content`)

**Errors**:
- `404 Not Found` — Session not found
- `403 Forbidden` — Cannot delete approved session
- `401 Unauthorized` — Invalid or missing JWT token

---

### `POST /api/sessions/{session_id}/approve`

**Approve session (transition from draft to approved)**

**Request**: Empty body or optional comment

**Response** (`200 OK`):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "approved",
  "approved_at": "2026-04-02T12:00:00Z",
  ...
}
```

**Errors**:
- `400 Bad Request` — Session has no items or items incomplete
- `403 Forbidden` — Session already approved
- `404 Not Found` — Session not found
- `401 Unauthorized` — Invalid or missing JWT token

---

### `POST /api/sessions/{session_id}/clone`

**Clone approved session as new draft**

**Request**:
```json
{
  "title": "Cloned Session Title"
}
```

**Response** (`201 Created`): New session object with status="draft"

**Errors**:
- `404 Not Found` — Session not found
- `401 Unauthorized` — Invalid or missing JWT token

**Notes**:
- Cloned session has new ID
- tracker_issue_id cleared for all items
- export_status reset to "not_exported"

---

## Error Response Schema

```json
{
  "code": "VALIDATION_ERROR",
  "message": "focus_factor must be between 0 and 1",
  "detail": "Field validation failed",
  "request_id": "req-123456"
}
```

**Error Codes**:
- `VALIDATION_ERROR` — Input validation failed
- `NOT_FOUND` — Resource not found
- `UNAUTHORIZED` — Authentication required
- `FORBIDDEN` — User lacks permission
- `CONFLICT` — State conflict (e.g., modifying approved session)
- `AUTHENTICATION_ERROR` — Tracker authentication failed (export-specific)

---

## Error Code Enum

**ErrorCode** (StrEnum) — Canonical error codes used across all APIs

```python
class ErrorCode(str, Enum):
    VALIDATION_ERROR = "validation_error"
    NOT_FOUND = "not_found"
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    CONFLICT = "conflict"
    AUTHENTICATION_ERROR = "authentication_error"
```

**Usage**: All API error responses MUST use one of these canonical codes.

---

## Authentication

All endpoints require JWT Bearer token:

```
Authorization: Bearer <jwt_token>
```

Token obtained via `POST /api/auth/login` (email/password).

---

## Rate Limiting

MVP: No rate limiting (≤ 5 concurrent users assumed)

Future: Add rate limiting headers if needed:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1617360000
```
