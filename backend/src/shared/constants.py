from __future__ import annotations

from typing import Final

# PERT formula constants — not configurable in MVP.
# Changes require a code release, not a config change.
CONTINGENCY_FACTOR: Final[float] = 0.1  # hidden_reserve = spread * k
BUFFER_Z_SCORE_95: Final[float] = 1.645  # buffer_95 = sigma_total * z

# Session limits
SESSION_SOFT_CAP: Final[int] = 50  # warning shown to user
SESSION_HARD_CAP: Final[int] = 100  # 409 ITEM_LIMIT_REACHED returned

# JWT TTL
JWT_ACCESS_TTL_MINUTES: Final[int] = 15
JWT_REFRESH_TTL_DAYS: Final[int] = 30

# Focus factor allowed values (Literal enforced in schema)
FOCUS_FACTOR_VALUES: Final[tuple[float, ...]] = (0.5, 0.6, 0.7, 0.8, 0.9, 1.0)
FOCUS_FACTOR_DEFAULT: Final[float] = 0.8

# Session defaults
HOURS_PER_DAY_DEFAULT: Final[int] = 8

# Spread precision — all PERT values rounded to this many decimal places
PERT_PRECISION: Final[int] = 3
