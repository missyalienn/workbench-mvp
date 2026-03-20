**Testing Gotchas**
Short notes about tests that can fail in non-obvious ways.

**Embedding cache round-trip precision**
The embedding cache stores vectors as float32. When reading them back,
values can round slightly (for example, 0.1 becomes 0.10000000149).
Do not compare cached vectors with exact equality. Use approximate
comparisons (e.g., `pytest.approx`) in tests.
