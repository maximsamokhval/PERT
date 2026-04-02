# API Contract: Export

**Feature**: `001-pert-estimation-sdlc`
**Purpose**: Contract for export to issue tracker endpoints
**Generated from**: FastAPI OpenAPI spec (backend authority)

---

## Endpoints

### `POST /api/sessions/{session_id}/export`

**Export all items to issue tracker**

**Prerequisites**:
- Session status must be "approved"
- TrackerConnection must be active
- Project field mapping must be configured

**Request** (optional):
```json
{
  "project_id": "yourtrack-project-id",
  "item_ids": ["item-uuid-1", "item-uuid-2"]  // optional, defaults to all
}
```

**Response** (`207 Multi-Status`):
```json
{
  "succeeded": [
    {
      "item_id": "item-uuid-1",
      "tracker_issue_id": "YT-12345",
      "tracker_url": "https://youtrack/issue/YT-12345"
    },
    {
      "item_id": "item-uuid-2",
      "tracker_issue_id": "YT-12346",
      "tracker_url": "https://youtrack/issue/YT-12346"
    }
  ],
  "failed": [
    {
      "item_id": "item-uuid-3",
      "error": {
        "code": "TRACKER_API_ERROR",
        "message": "YouTrack API returned 400",
        "detail": "Field 'Summary' is required but was null"
      }
    }
  ],
  "total": 3
}
```

**Errors**:
- `400 Bad Request` — Session has no items
- `403 Forbidden` — Session not approved
- `404 Not Found` — Session not found
- `503 Service Unavailable` — Tracker connection not configured or inactive
- `401 Unauthorized` — Invalid or missing JWT token

---

### `POST /api/sessions/{session_id}/export/retry`

**Retry failed exports**

**Request**:
```json
{
  "item_ids": ["item-uuid-3"]  // items to retry
}
```

**Response** (`207 Multi-Status`): Same structure as export

**Notes**:
- Only items with export_status="failed" can be retried
- Already exported items are skipped

---

### `GET /api/sessions/{session_id}/export/preview`

**Preview export before committing**

**Response** (`200 OK`):
```json
{
  "project_id": "CON",
  "project_name": "Consolidation2025",
  "items": [
    {
      "item_id": "item-uuid-1",
      "title": "Implement authentication",
      "mapped_fields": {
        "Summary": "Implement authentication",
        "Description": "JWT-based authentication with refresh tokens",
        "Оценка": "2h 30m",
        "Type": "New Feature",
        "Subsystem": "API: Exchange 1C-Odoo",
        "Assignee": "john.doe",
        "CoS": "Standard"
      }
    }
  ],
  "field_mapping": [
    {
      "item_field": "title",
      "tracker_field": "Summary"
    },
    {
      "item_field": "description",
      "tracker_field": "Description"
    },
    {
      "item_field": "total_effort",
      "tracker_field": "Оценка"
    },
    {
      "item_field": "work_type",
      "tracker_field": "Type"
    },
    {
      "item_field": "subsystem",
      "tracker_field": "Subsystem"
    },
    {
      "item_field": "assignee",
      "tracker_field": "Assignee"
    },
    {
      "item_field": "priority",
      "tracker_field": "CoS"
    }
  ]
}
```

**Errors**:
- `404 Not Found` — Session not found
- `503 Service Unavailable` — Tracker connection not configured
- `401 Unauthorized` — Invalid or missing JWT token

---

## Export Idempotency

**Mechanism**: `estimation_item.tracker_issue_id`

- If `tracker_issue_id` is already set, skip creation (return existing)
- Export is idempotent — calling multiple times with same data produces same result
- To re-export, must clear `tracker_issue_id` first (via session clone or manual reset)

---

## Conversion Logic

**hours_to_period**: Utility function to convert float hours to YouTrack period format

```python
def hours_to_period(hours: float) -> str:
    """
    Convert decimal hours to YouTrack period string.
    Example: 8.8 → "8h 48m"
    """
    h = int(hours)
    m = int((hours - h) * 60)
    if m == 0:
        return f"{h}h"
    return f"{h}h {m}m"
```

**Examples**:
- `8.0` → `"8h"`
- `8.5` → `"8h 30m"`
- `8.8` → `"8h 48m"`
- `0.5` → `"30m"`
- `24.25` → `"24h 15m"`

---

## Field Mapping

**Default mapping** (configurable per project):

| Item Field | Tracker Field | Type |
|------------|---------------|------|
| title | Summary | String |
| description | Description | Text |
| total_effort | Оценка | Period (e.g., "2h 30m") |
| work_type | Type | Enum |
| subsystem | Subsystem | Enum |
| assignee | Assignee | User |
| analyst | Аналитик | User |
| developer | developer | User |
| priority | CoS | Enum |
| start_date | Start Date | Date |
| lead_time | LT | Period |

**Project-specific available fields**:

### CON (Consolidation2025)
- **Stage** — Backlog, Анализ, ToDo, Develop, Staging, Re-work, Deployment, Done, Cancelled, Validation, UAT
- **Status-Phase** — Initiate, Plan, Build, Test, Release, Close
- **ID Service Desk** — String
- **Контактное лицо** — String

### MDM (Master Data Management)
- **Stage** — Backlog, Анализ, ToDo, Develop, Staging, Re-work, Deployment, Done, Cancelled, Validation, UAT
- **Команда разработки** — Хибна думка, Мудрая сова, Черепахи, Палаючий дедлайн
- **OnHold** — True, False
- **Подразделение** — Логистика, Производство, Закупки, IT, Финансы, Коммерция, Департамент по оптимизации БП, Бухгалтерия, Безопасность, ДНІПРОАГРОЛАН, ЗАВОД, Лабораторія, Відділ якості
- **Due Date** — Date
- **Дата реализации (IT)** — Date
- **ID Service Desk** — String
- **Контактное лицо** — String

**Note**: MDM project requires `Assignee` field.

---

## Tracker Adapter Interface

**Protocol** (backend/src/features/export/ports/__init__.py):

```python
class IssueTrackerPort(Protocol):
    async def test_connection(self) -> ConnectionResult: ...
    async def list_projects(self) -> list[Project]: ...
    async def get_project_fields(self, project_id: str) -> list[Field]: ...
    async def create_issue(
        self,
        project_id: str,
        payload: IssuePayload
    ) -> CreatedIssue: ...
```

**YouTrackAdapter** implements this protocol.

---

## Error Handling

**Partial failures**:
- Some items export successfully, others fail
- HTTP `207 Multi-Status` returned
- Client displays per-item success/failure
- User can retry failed items

**Error Codes**:
- `TRACKER_API_ERROR` — YouTrack API returned error
- `FIELD_MAPPING_ERROR` — Required field not mapped
- `CONNECTION_ERROR` — Cannot connect to tracker
- `AUTHENTICATION_ERROR` — Tracker token invalid/expired

---

## Rate Limiting & Throttling

**MVP**: No throttling (batch export all at once)

**Future**: Add throttling if YouTrack API rate limits:
- Max 10 requests/second
- Retry-After header handling

---

## Authentication

All endpoints require JWT Bearer token:

```
Authorization: Bearer <jwt_token>
```

---

## Example Flow

```
1. User approves session
2. User clicks "Export to YouTrack"
3. Frontend calls GET /export/preview
4. User reviews mapping
5. Frontend calls POST /export
6. Backend creates issues in YouTrack
7. Backend updates tracker_issue_id for each item
8. Frontend displays results (success + failures)
9. User can retry failed items
```
