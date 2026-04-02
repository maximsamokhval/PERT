# API Contract: Items

**Feature**: `001-pert-estimation-sdlc`
**Purpose**: Contract for estimation item endpoints
**Generated from**: FastAPI OpenAPI spec (backend authority)

---

## Endpoints

### `POST /api/sessions/{session_id}/items`

**Create new estimation item**

**Request**:
```json
{
  "title": "Implement user authentication",
  "description": "JWT-based authentication with refresh tokens",
  "optimistic": 4,
  "most_likely": 8,
  "pessimistic": 12
}
```

**Response** (`201 Created`):
```json
{
  "id": "item-uuid-1",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "Implement user authentication",
  "description": "JWT-based authentication with refresh tokens",
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
```

**Errors**:
- `400 Bad Request` — Validation error (O > M > P violated, negative values)
- `403 Forbidden` — Session is approved (cannot add items)
- `404 Not Found` — Session not found
- `401 Unauthorized` — Invalid or missing JWT token
- `409 Conflict` — Session at item limit (100 items)

---

### `GET /api/sessions/{session_id}/items/{item_id}`

**Get single item by ID**

**Response** (`200 OK`): See item structure above

**Errors**:
- `404 Not Found` — Item or session not found
- `401 Unauthorized` — Invalid or missing JWT token

---

### `PATCH /api/sessions/{session_id}/items/{item_id}`

**Update item O/M/P values**

**Request**:
```json
{
  "optimistic": 5,
  "most_likely": 10,
  "pessimistic": 15
}
```

**Response** (`200 OK`): Updated item with recalculated metrics

**Errors**:
- `400 Bad Request` — Validation error (O ≤ M ≤ P violated)
- `403 Forbidden` — Session is approved (cannot modify)
- `404 Not Found` — Item or session not found
- `401 Unauthorized` — Invalid or missing JWT token
- `409 Conflict` — Concurrent modification detected (optimistic locking)

---

### `DELETE /api/sessions/{session_id}/items/{item_id}`

**Delete item from session**

**Response** (`204 No Content`)

**Errors**:
- `403 Forbidden` — Session is approved (cannot delete)
- `404 Not Found` — Item or session not found
- `401 Unauthorized` — Invalid or missing JWT token

---

### `PATCH /api/sessions/{session_id}/items/batch`

**Batch update multiple items (for auto-save)**

**Request**:
```json
{
  "items": [
    {
      "id": "item-uuid-1",
      "optimistic": 5,
      "most_likely": 10,
      "pessimistic": 15
    },
    {
      "id": "item-uuid-2",
      "title": "Updated title"
    }
  ]
}
```

**Response** (`207 Multi-Status`):
```json
{
  "succeeded": [
    {
      "item_id": "item-uuid-1",
      "data": { ...updated item... }
    }
  ],
  "failed": [
    {
      "item_id": "item-uuid-2",
      "error": {
        "code": "VALIDATION_ERROR",
        "message": "O must be ≤ M",
        "detail": "optimistic=5, most_likely=4 violates O ≤ M"
      }
    }
  ],
  "total": 2
}
```

**Errors**:
- `400 Bad Request` — Invalid request structure
- `403 Forbidden` — Session is approved
- `401 Unauthorized` — Invalid or missing JWT token

---

## Validation Rules

**Item-level constraints**:
- `optimistic ≥ 1`
- `most_likely ≥ 1`
- `pessimistic ≥ 1`
- `optimistic ≤ most_likely ≤ pessimistic`

**Session-level constraints**:
- Maximum 100 items per session (hard cap)
- Cannot modify items if session.status = "approved"

---

## Optimistic Locking

**Mechanism**: `updated_at` timestamp comparison

**Request Header** (optional):
```
If-Unmodified-Since: 2026-04-02T10:05:00Z
```

**Response on Conflict** (`409 Conflict`):
```json
{
  "code": "CONCURRENT_MODIFICATION",
  "message": "Item was modified by another user",
  "detail": "Expected updated_at ≤ 2026-04-02T10:05:00Z, but found 2026-04-02T10:06:00Z",
  "current_item": { ...latest item state... }
}
```

**Client Resolution**:
1. Display conflict warning to user
2. Show current values vs. user's intended values
3. Allow user to overwrite or discard changes

---

## PERT Calculation Authority

**Backend is authoritative source** for all calculated fields:
- `t_expected`
- `spread`
- `sigma`
- `variance`
- `hidden_reserve`
- `total_effort`

**Frontend may calculate optimistically** for UX, but MUST sync with backend response within 2 seconds.

---

## Error Response Schema

See [sessions-api.md](./sessions-api.md#error-response-schema)

Common error codes for items:
- `VALIDATION_ERROR` — O/M/P constraints violated
- `CONCURRENT_MODIFICATION` — Optimistic locking conflict
- `ITEM_LIMIT_REACHED` — Session at 100 items
- `SESSION_APPROVED` — Cannot modify approved session

---

## Export Mapping Model

**ExportMapping** — Separate model storing additional fields for tracker export

**Structure**:
```json
{
  "item_id": "item-uuid-1",
  "work_type": "New Feature",
  "subsystem": "API: Exchange 1C-Odoo",
  "assignee": "john.doe",
  "analyst": "jane.smith",
  "developer": "bob.wilson",
  "priority": "Standard",
  "start_date": "2026-04-15",
  "lead_time": "2h 30m"
}
```

**Fields** (all optional):
- `work_type` — Type of work (maps to YouTrack "Type" field)
- `subsystem` — Subsystem/component (maps to "Subsystem")
- `assignee` — Assignee login (maps to "Assignee", required for MDM project)
- `analyst` — Analyst login (maps to "Аналитик")
- `developer` — Developer login (maps to "developer")
- `priority` — Priority/CoS (maps to "CoS")
- `start_date` — Start date in yyyy-MM-dd format
- `lead_time` — Lead time in period format (e.g., "2h 30m")

**Storage**: One-to-one relationship with EstimationItem

**Retrieval**: Included in export preview and export operations, not in basic item responses
