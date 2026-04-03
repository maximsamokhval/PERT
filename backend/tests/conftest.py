from __future__ import annotations

# Import all fixtures from shared fixtures so they're available to tests

# Re-export fixtures so pytest can find them
pytest_plugins = [
    "tests.fixtures",
]
