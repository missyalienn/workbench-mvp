# Dev Notes

A living log of commands, tricks, and lessons learned while building this project.

---

## 🧪 Pytest
- `pytest tests/test_auth.py` — run all tests in file
- `pytest tests/test_auth.py::test_reddit_auth` — run a single test
- `pytest -k test_name` — run tests matching substring
- `pytest -x` — stop after first failure
- `pytest --maxfail=2` — stop after 2 failures
- `pytest -v` — verbose output

---

## 🔑 Auth & Secrets
- Store API keys in macOS Keychain with `keyring`
- Retrieve in Python:  
  ```python
  import keyring
  keyring.get_password("service", "username")

## 📚 Tests Lessons 
- Cursor’s generated tests = scaffolding, not real unit tests
- Refactoring into pytest style makes tests shorter, clearer, and maintainable
