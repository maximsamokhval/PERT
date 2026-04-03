from __future__ import annotations

from pydantic import Field

from .base import ReadModel
from .enums import ErrorCode
from .types import ItemId


class ErrorResponse(ReadModel):
    """
    Canonical error response for ALL endpoints.
    No other error shape is valid.

    HTTP status is set in the response header — not in this body.
    All HTTPException instances MUST be wrapped via ErrorResponse.
    Direct raise HTTPException(detail="raw string") is PROHIBITED.
    """

    code: ErrorCode
    message: str = Field(min_length=1, max_length=500)
    detail: str = Field(default="", max_length=2000)
    request_id: str = Field(default="", max_length=100)


class ConflictDetail(ReadModel):
    """
    Body extension for CONCURRENT_MODIFICATION (409).
    Included as detail payload alongside ErrorResponse.
    """

    expected_updated_at: str  # AwareDatetime ISO string client sent
    actual_updated_at: str  # AwareDatetime ISO string from DB


class ItemResult(ReadModel):
    """Single successfully exported item result."""

    item_id: ItemId
    tracker_issue_id: str | None


class FailedItemResult(ReadModel):
    """Single failed item result with error context."""

    item_id: ItemId
    error: ErrorResponse


class PartialResultResponse(ReadModel):
    """
    HTTP 207 Multi-Status response for batch/export operations with partial results.
    Used when some items succeed and some fail.
    """

    succeeded: list[ItemResult]
    failed: list[FailedItemResult]
    total: int
