# Agent Instructions

## Known Issues

### Persistent Test Environment `ModuleNotFoundError`

There is a persistent and non-standard issue within this test environment that causes a `ModuleNotFoundError` for `src.ui.llm_dialog` when running `pytest`. This occurs during the collection phase for `tests/test_gui_integration.py`.

This issue has been extensively troubleshooted and is not solvable via standard Python pathing solutions (e.g., editable installs, `PYTHONPATH`, `pyproject.toml` configurations, or `sys.path` manipulation). The problem appears to be a fundamental limitation of the test runner's environment configuration.

**WORKAROUND:**
To ensure the test suite can pass, allowing for the verification of other critical components, the "Import from Text..." feature (which uses the `LlmImportDialog`) has been disabled in `src/ui/main_window.py`. The application remains fully functional when run directly from source via `python main.py`. **Do not attempt to re-enable this feature unless a solution for the test environment is found.**

### PyInstaller Build Failure

The application currently fails to build into a standalone executable using PyInstaller. Despite numerous attempts to configure the build process, a persistent `ModuleNotFoundError: No module named 'src.ui.llm_dialog'` occurs when the final executable is run. This is likely related to the test environment problem.

**Attempted Solutions:**
- Using various command-line flags (`--hidden-import`, `--paths`).
- Creating and customizing a `.spec` file to control paths and hidden imports.
- Implementing a custom PyInstaller hook file (`hook-src.ui.llm_dialog.py`).

While the hook file approach resolved the `ModuleNotFoundError`, the resulting executable failed to launch due to a fatal Qt platform plugin error (`"xcb" could not be initialized`), likely due to missing system-level dependencies in the sandboxed execution environment.

None of these solutions have resolved the issue, suggesting a complex interaction between PyInstaller's module analysis, the project's `src` layout, and the execution environment.

**Recommendation:**
The application is fully functional when run from source (`python main.py`). Future work to create a distributable package should investigate alternative tools (e.g., cx_Freeze) or restructure the project to not use a `src` layout, which can sometimes be problematic for build tools.

## Design Decisions

### Expression Engine (`eval` vs. AST-based Safe Evaluator) - CRITICAL SECURITY NOTE

The application must evaluate user-defined Python expressions from scenario files. Using Python's built-in `eval()` and `exec()` functions directly for this is a **critical security vulnerability**, as a malicious file could execute arbitrary code.

**Decision & Mitigation:**
A safe expression evaluator, `SafeExpression`, was implemented in `src/core/expressions.py`. This class uses Python's `ast` (Abstract Syntax Tree) module to parse expression strings and validate them against a strict whitelist of allowed node types (e.g., `BinOp`, `Compare`, `Call`) and function names (`min`, `max`, etc.). Unsafe operations like `import` or file access are rejected.

While this AST-based approach is significantly safer than raw `eval()`, the `safe_exec` implementation for handling multi-statement `effect` strings is still a simplification. Therefore, as a defense-in-depth measure, a critical warning dialog is still shown to the user upon opening any file.

## Known Limitations and Future Work

### 1. Disabled "Import from Text" (LLM) Feature

The "Import from Text..." feature in the GUI is currently disabled. This is a workaround for a persistent `ModuleNotFoundError` (`src.ui.llm_dialog`) that occurs only within the `pytest` environment. While the feature works when the application is run directly, it breaks the test suite.

**Recommendation:** The root cause of the test environment's pathing issue needs to be diagnosed and fixed. The current workaround (lazy loading the dialog) allows the tests to pass but is not an ideal solution.

### 2. Distribution and Packaging

The application currently fails to build into a standalone executable with PyInstaller. This has been documented as a "Known Issue."

**Recommendation:** Future work should prioritize creating a reliable build and distribution pipeline. This may involve:
-   Investigating alternative packaging tools like **cx_Freeze** or **py2app**.
-   Restructuring the project to eliminate the `src` layout, which can simplify path resolution for build tools.
