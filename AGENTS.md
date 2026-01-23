# Agent Instructions

## Known Issues

### Persistent `ModuleNotFoundError` in Test Environment

There is a persistent and unusual `ModuleNotFoundError` that occurs when running `pytest` in this specific test environment. The tests consistently fail to find modules located in the `src` directory (e.g., `src.engine.simulation_engine`).

This issue persists despite trying all standard solutions for Python pathing problems, including:
1.  Installing the project in editable mode (`pip install -e .`).
2.  Ensuring `pyproject.toml` is correctly configured with `[tool.setuptools.packages.find] where = ["src"]`.
3.  Explicitly setting the `PYTHONPATH` environment variable (`PYTHONPATH=./src pytest`).
4.  Adding `src` to `pythonpath` in the `[tool.pytest.ini_options]` section of `pyproject.toml`.
5.  Temporarily modifying `sys.path` directly within the test files.

None of these methods have resolved the import errors in this environment. This suggests a unique and non-standard configuration of the test runner that overrides or ignores these settings.

**Workaround/Agent Action:**
- The "Import from Text..." feature, which relies on `src.ui.llm_dialog`, remains disabled as its associated test cannot be run.
- Further attempts to run the full test suite will likely fail until the root cause of this environment-specific pathing issue is identified and resolved. Development can proceed, but verification must be done by running the application directly.

## Design Decisions

### Expression Engine (`eval` vs. Custom Parser)

An attempt was made to replace the `eval()` and `exec()` calls in the simulation engine and analyzer with a custom, safer expression engine (parser and interpreter). This attempt failed due to the difficulty of creating a robust-enough parser with simple regular expressions, leading to persistent bugs.

**Decision:** The implementation was reverted to the original `eval()`/`exec()` based logic. While this carries security risks (mitigated by a UI warning), it is functionally correct and more robust than the incomplete custom parser. Any future attempt to replace `eval()` should involve a more powerful parsing library (e.g., ANTLR, Lark) rather than regex.
