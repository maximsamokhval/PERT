from __future__ import annotations

from enum import StrEnum


class SessionStatus(StrEnum):
    DRAFT = "draft"
    APPROVED = "approved"


class ExportStatus(StrEnum):
    NOT_EXPORTED = "not_exported"
    EXPORTED = "exported"
    FAILED = "failed"


class TrackerType(StrEnum):
    YOUTRACK = "youtrack"
    # JIRA = "jira"          # not implemented in MVP
    # LINEAR = "linear"      # not implemented in MVP
    # AZURE_DEVOPS = "azure_devops"  # not implemented in MVP


class UserRole(StrEnum):
    EDITOR = "editor"
    VIEWER = "viewer"


# ERROR CODES — exhaustive list per Constitution Principle V.
# Agent MUST NOT introduce codes outside this enum. New codes require a code
# release and enum update.
class ErrorCode(StrEnum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    CONFLICT = "CONFLICT"
    CONCURRENT_MODIFICATION = "CONCURRENT_MODIFICATION"
    ITEM_LIMIT_REACHED = "ITEM_LIMIT_REACHED"
    SESSION_APPROVED = "SESSION_APPROVED"
    TRACKER_API_ERROR = "TRACKER_API_ERROR"
    CONNECTION_ERROR = "CONNECTION_ERROR"
    FIELD_MAPPING_ERROR = "FIELD_MAPPING_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
