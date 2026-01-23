# Agent Instructions

## Known Issues

### Test Runner Path Configuration

There is a persistent `ModuleNotFoundError` for `src.ui.llm_dialog` when running the `unittest discover` command, specifically for `tests/test_gui_integration.py`. This issue occurs even when the project is installed in editable mode or when `src` is added to the `PYTHONPATH`.

As a temporary workaround, the "Import from Text..." feature in the GUI has been disabled in `src/ui/main_window.py`. Any agent attempting to fix or work on the LLM import functionality must first find a definitive solution to this test pathing issue. The application code itself works when run directly.
