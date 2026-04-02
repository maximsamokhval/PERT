# API Contract: Settings

**Feature**: `001-pert-estimation-sdlc`
**Purpose**: Contract for system settings and tracker configuration
**Generated from**: FastAPI OpenAPI spec (backend authority)

---

## Endpoints

### `GET /api/settings/tracker`

**Get current tracker connection status**

**Response** (`200 OK`):
```json
{
  "tracker_type": "youtrack",
  "base_url": "https://youtrack.company.com",
  "is_active": true,
  "last_verified_at": "2026-04-02T09:00:00Z",
  "configured": true
}
```

**Response** (not configured, `200 OK`):
```json
{
  "tracker_type": null,
  "base_url": null,
  "is_active": false,
  "last_verified_at": null,
  "configured": false
}
```

**Errors**:
- `401 Unauthorized` — Invalid or missing JWT token
- `403 Forbidden` — User role is "viewer" (only editors can view settings)

---

### `POST /api/settings/tracker`

**Configure or update tracker connection**

**Request**:
```json
{
  "tracker_type": "youtrack",
  "base_url": "https://youtrack.company.com",
  "token": "perm:xxxxxxxxxxxxxxxxxxxx"
}
```

**Response** (`200 OK`):
```json
{
  "tracker_type": "youtrack",
  "base_url": "https://youtrack.company.com",
  "is_active": true,
  "last_verified_at": "2026-04-02T10:00:00Z",
  "configured": true
}
```

**Errors**:
- `400 Bad Request` — Invalid URL, invalid tracker_type, token too short
- `401 Unauthorized` — Invalid or missing JWT token
- `403 Forbidden` — User role is "viewer"
- `503 Service Unavailable` — Cannot connect to tracker (test connection failed)

---

### `POST /api/settings/tracker/test`

**Test tracker connection without saving**

**Request**:
```json
{
  "tracker_type": "youtrack",
  "base_url": "https://youtrack.company.com",
  "token": "perm:xxxxxxxxxxxxxxxxxxxx"
}
```

**Response** (`200 OK`):
```json
{
  "success": true,
  "message": "Connection successful",
  "projects": [
    {
      "id": "project-1",
      "name": "Project Alpha",
      "short_name": "ALPHA"
    },
    {
      "id": "project-2",
      "name": "Project Beta",
      "short_name": "BETA"
    }
  ]
}
```

**Response** (failure, `200 OK`):
```json
{
  "success": false,
  "message": "Authentication failed. Check your API token.",
  "projects": []
}
```

**Errors**:
- `400 Bad Request` — Invalid request structure
- `401 Unauthorized` — Invalid or missing JWT token
- `403 Forbidden` — User role is "viewer"

---

### `GET /api/settings/tracker/projects`

**List available projects from connected tracker**

**Response** (`200 OK`):
```json
{
  "projects": [
    {
      "id": "CON",
      "name": "Consolidation2025",
      "short_name": "CON",
      "fields": [
        {
          "name": "Summary",
          "type": "string",
          "required": true
        },
        {
          "name": "Description",
          "type": "text",
          "required": false
        },
        {
          "name": "Type",
          "type": "enum",
          "required": false,
          "values": ["New Feature", "Task", "Epic", "User Story", "Tech Debt", "Scope Change", "Requirement Clarification", "Bug (Production)", "Bug (Development)"]
        },
        {
          "name": "Stage",
          "type": "enum",
          "required": false,
          "values": ["Backlog", "Анализ", "ToDo", "Develop", "Staging", "Re-work", "Deployment", "Done", "Cancelled", "Validation", "UAT"]
        },
        {
          "name": "Subsystem",
          "type": "enum",
          "required": false,
          "values": ["1C: UPP", "1C: BAS Agro", "1C: Budget", "1C: Conso", "1C: MDM", "1C: DAL", "Odoo: Accounting", "Odoo: Sales", "Odoo: Warehouse", "API: Exchange 1C-Odoo", "External: SAF-T", "Mobile: App", "API: Exchange 1C-Pohoda", "API: Exchange 1C-1C", "API: Exchange 1C-FortMonitor", "1C: CRM", "1C: ТОіР ДКПК", "1C: ТОіР ІК", "1C: ТОіР Німеччина", "1C: ТОіР Mobile", "1C: security", "API: Exchange 1C-SAP", "1C:WMS"]
        },
        {
          "name": "Оценка",
          "type": "period",
          "required": false,
          "format": "Period in string representation (w d h m), e.g. '1w 2d 3h 10m', '2h 30m', '15m'"
        },
        {
          "name": "Assignee",
          "type": "user",
          "required": false,
          "format": "Login. Example: \"john.doe\""
        },
        {
          "name": "Аналитик",
          "type": "user",
          "required": false,
          "format": "Login. Example: \"john.doe\""
        },
        {
          "name": "developer",
          "type": "user",
          "required": false,
          "format": "Login. Example: \"john.doe\""
        },
        {
          "name": "CoS",
          "type": "enum",
          "required": false,
          "values": ["Expedite", "Fixed deadline", "Standard", "Нематериальный"]
        },
        {
          "name": "Status-Phase",
          "type": "enum",
          "required": false,
          "values": ["Initiate", "Plan", "Build", "Test", "Release", "Close"]
        },
        {
          "name": "Start Date",
          "type": "date",
          "required": false,
          "format": "yyyy-MM-dd"
        },
        {
          "name": "LT",
          "type": "period",
          "required": false,
          "format": "Period in string representation (w d h m)"
        },
        {
          "name": "ID Service Desk",
          "type": "string",
          "required": false
        },
        {
          "name": "Контактное лицо",
          "type": "string",
          "required": false
        }
      ]
    },
    {
      "id": "MDM",
      "name": "MDM (Master Data Management)",
      "short_name": "MDM",
      "fields": [
        {
          "name": "Summary",
          "type": "string",
          "required": true
        },
        {
          "name": "Description",
          "type": "text",
          "required": false
        },
        {
          "name": "Type",
          "type": "enum",
          "required": false,
          "values": ["New Feature", "Task", "Epic", "User Story", "Tech Debt", "Scope Change", "Requirement Clarification", "Bug (Production)", "Bug (Development)"]
        },
        {
          "name": "Stage",
          "type": "enum",
          "required": false,
          "values": ["Backlog", "Анализ", "ToDo", "Develop", "Staging", "Re-work", "Deployment", "Done", "Cancelled", "Validation", "UAT"]
        },
        {
          "name": "Subsystem",
          "type": "enum",
          "required": false,
          "values": ["1C: UPP", "1C: BAS Agro", "1C: Budget", "1C: Conso", "1C: MDM", "1C: DAL", "Odoo: Accounting", "Odoo: Sales", "Odoo: Warehouse", "API: Exchange 1C-Odoo", "External: SAF-T", "Mobile: App", "API: Exchange 1C-Pohoda", "API: Exchange 1C-1C", "API: Exchange 1C-FortMonitor", "1C: CRM", "1C: ТОіР ДКПК", "1C: ТОіР ІК", "1C: ТОіР Німеччина", "1C: ТОіР Mobile", "1C: security", "API: Exchange 1C-SAP", "1C:WMS"]
        },
        {
          "name": "Оценка",
          "type": "period",
          "required": false,
          "format": "Period in string representation (w d h m), e.g. '1w 2d 3h 10m', '2h 30m', '15m'"
        },
        {
          "name": "Assignee",
          "type": "user",
          "required": true,
          "format": "Login. Example: \"john.doe\""
        },
        {
          "name": "Аналитик",
          "type": "user",
          "required": false,
          "format": "Login. Example: \"john.doe\""
        },
        {
          "name": "developer",
          "type": "user",
          "required": false,
          "format": "Login. Example: \"john.doe\""
        },
        {
          "name": "CoS",
          "type": "enum",
          "required": false,
          "values": ["Expedite", "Fixed deadline", "Standard", "Нематериальный"]
        },
        {
          "name": "Команда разработки",
          "type": "enum[]",
          "required": false,
          "values": ["Хибна думка", "Мудрая сова", "Черепахи", "Палаючий дедлайн"]
        },
        {
          "name": "OnHold",
          "type": "enum",
          "required": false,
          "values": ["True", "False"]
        },
        {
          "name": "Подразделение",
          "type": "enum",
          "required": false,
          "values": ["Логистика", "Производство", "Закупки", "IT", "Финансы", "Коммерция", "Департамент по оптимизации БП", "Бухгалтерия", "Безопасность", "ДНІПРОАГРОЛАН", "ЗАВОД", "Лабораторія", "Відділ якості"]
        },
        {
          "name": "Due Date",
          "type": "date",
          "required": false,
          "format": "yyyy-MM-dd"
        },
        {
          "name": "Дата реализации (IT)",
          "type": "date",
          "required": false,
          "format": "yyyy-MM-dd"
        },
        {
          "name": "Start Date",
          "type": "date",
          "required": false,
          "format": "yyyy-MM-dd"
        },
        {
          "name": "LT",
          "type": "period",
          "required": false,
          "format": "Period in string representation (w d h m)"
        },
        {
          "name": "ID Service Desk",
          "type": "string",
          "required": false
        },
        {
          "name": "Контактное лицо",
          "type": "string",
          "required": false
        }
      ]
    }
  ]
}
```

**Errors**:
- `503 Service Unavailable` — Tracker not configured
- `401 Unauthorized` — Invalid or missing JWT token
- `403 Forbidden` — User role is "viewer"

---

### `POST /api/settings/tracker/projects/{project_id}/mapping`

**Configure field mapping for a project**

**Request**:
```json
{
  "mappings": [
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
      "tracker_field": "Estimate (hours)"
    }
  ]
}
```

**Response** (`200 OK`):
```json
{
  "project_id": "project-1",
  "mappings": [
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
      "tracker_field": "Estimate (hours)"
    }
  ]
}
```

**Errors**:
- `400 Bad Request` — Invalid mapping (missing required fields)
- `503 Service Unavailable` — Tracker not configured
- `401 Unauthorized` — Invalid or missing JWT token
- `403 Forbidden` — User role is "viewer"

---

### `GET /api/settings/tracker/projects/{project_id}/mapping`

**Get current field mapping for a project**

**Response** (`200 OK`):
```json
{
  "project_id": "project-1",
  "mappings": [
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
      "tracker_field": "Estimate (hours)"
    }
  ]
}
```

**Errors**:
- `404 Not Found` — Project not found
- `503 Service Unavailable` — Tracker not configured
- `401 Unauthorized` — Invalid or missing JWT token
- `403 Forbidden` — User role is "viewer"

---

### `DELETE /api/settings/tracker`

**Remove tracker connection**

**Response** (`204 No Content`)

**Errors**:
- `401 Unauthorized` — Invalid or missing JWT token
- `403 Forbidden` — User role is "viewer"

---

## Tracker Types

**Supported** (TrackerType enum):
- `youtrack` — JetBrains YouTrack
- `jira` — Atlassian Jira (future)
- `linear` — Linear (future)
- `azure_devops` — Azure DevOps (future)

**MVP**: Only `youtrack` is implemented.

---

## Token Storage

**Security**:
- Token encrypted with Fernet (symmetric encryption)
- Encryption key from environment variable `ENCRYPTION_KEY`
- Token never returned in API responses
- Token transmitted only during configuration

---

## Role-Based Access

**Editor** (`role="editor"`):
- Can view and modify settings
- Can configure tracker connection
- Can create field mappings

**Viewer** (`role="viewer"`):
- Cannot access settings endpoints
- Read-only access to sessions

---

## Authentication

All endpoints require JWT Bearer token:

```
Authorization: Bearer <jwt_token>
```

---

## Example Configuration Flow

```
1. Admin navigates to Settings page
2. Enters YouTrack URL and API token
3. Clicks "Test Connection"
4. System shows available projects
5. Admin selects project
6. Admin configures field mapping
7. System saves mapping
8. Admin can now export sessions to this project
```
