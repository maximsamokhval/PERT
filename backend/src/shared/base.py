from __future__ import annotations

from pydantic import BaseModel, ConfigDict

# Canonical config — applied to ALL models in this project.
_BASE_CONFIG = ConfigDict(
    strict=True,  # No implicit type coercion (int "1" ≠ int 1 from JSON string)
    frozen=True,  # Instances are immutable after construction
    populate_by_name=True,  # Allow field name AND alias to populate
    use_enum_values=True,  # Serialize enums as their .value (str), not enum instances
)


class ReadModel(BaseModel):
    """
    Base for all API response schemas.
    Strict + frozen: immutable DTOs returned from backend.
    """

    model_config = _BASE_CONFIG


class WriteModel(BaseModel):
    """
    Base for Create schemas (POST body).
    Strict mode preserved; not frozen (constructed from request data).
    """

    model_config = ConfigDict(
        strict=True,
        frozen=False,
        populate_by_name=True,
        use_enum_values=True,
    )


class UpdateModel(BaseModel):
    """
    Base for Update schemas (PATCH body).
    All fields are Optional — agent MUST NOT make them required.
    Not frozen.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=False,
        populate_by_name=True,
        use_enum_values=True,
    )
