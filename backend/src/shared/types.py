from __future__ import annotations

import uuid
from typing import NewType

# All IDs are UUID v4. NewType provides type-checker distinction between them.
# This is the ONLY place where NewType IDs are defined. Never define local ID
# types in feature modules — always import from here.

UserId = NewType("UserId", uuid.UUID)
SessionId = NewType("SessionId", uuid.UUID)
ItemId = NewType("ItemId", uuid.UUID)
ExportMappingId = NewType("ExportMappingId", uuid.UUID)
