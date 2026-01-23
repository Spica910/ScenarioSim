# Agent Instructions

## Known Issues

### Test Runner Path Configuration

There is a persistent `ModuleNotFoundError` for `src.ui.llm_dialog` when running the `unittest discover` command, specifically for `tests/test_gui_integration.py`. This issue occurs even when the project is installed in editable mode or when `src` is added to the `PYTHONPATH`.

As a temporary workaround, the "Import from Text..." feature in the GUI has been disabled in `src/ui/main_window.py`. Any agent attempting to fix or work on the LLM import functionality must first find a definitive solution to this test pathing issue. The application code itself works when run directly.

## Design Decisions

### Expression Engine (`eval` vs. Custom Parser)

An attempt was made to replace the `eval()` and `exec()` calls in the simulation engine and analyzer with a custom, safer expression engine (parser and interpreter). This attempt failed due to the difficulty of creating a robust-enough parser with simple regular expressions, leading to persistent bugs.

**Decision:** The implementation was reverted to the original `eval()`/`exec()` based logic. While this carries security risks (mitigated by a UI warning), it is functionally correct and more robust than the incomplete custom parser. Any future attempt to replace `eval()` should involve a more powerful parsing library (e.g., ANTLR, Lark) rather than regex.
