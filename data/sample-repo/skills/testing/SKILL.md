---
name: testing
description: How to write and run tests in this repository
---
# Testing

- Tests live in tests/, one file per module: tests/test_<module>.py.
- Import from the package, as `from checkout.<module> import ...`; tests/conftest.py puts src/ on the path.
- Name each test for the rule it checks: test_<what>_<expected>.
- Money is in cents, as int: assert exact integers, never floats.
- Run them with: python -m pytest -q
- A new function gets a test for its ordinary case, its edge case (zero, empty, unknown input), and its rounding.
