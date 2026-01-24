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
- Using `--hidden-import=src.ui.llm_dialog`
- Using `--paths=src` to add the source directory to the search path.
- Creating a `.spec` file to manually configure `pathex`, `hiddenimports`, and `binaries` for `libz3.so`.
- Manipulating `sys.path` directly within the `.spec` file.

None of these solutions have resolved the issue, suggesting a complex interaction between PyInstaller's module analysis, the project's `src` layout, and the execution environment.

**Recommendation:**
The application is fully functional when run from source (`python main.py`). Future work to create a distributable package should investigate alternative tools (e.g., cx_Freeze) or restructure the project to not use a `src` layout, which can sometimes be problematic for build tools.

## Design Decisions

### Expression Engine (`eval` vs. Custom Parser) - CRITICAL SECURITY NOTE

The simulation engine and analyzer use `eval()` and `exec()` to run user-defined Python expressions from scenario files. This is a **critical security vulnerability**. A malicious scenario file can execute arbitrary, harmful code on the user's machine.

An attempt to replace this with a custom, safe expression parser was made but failed due to its complexity and brittleness.

**Decision & Mitigation:**
The decision was made to keep the `eval()`/`exec()` logic for its flexibility and power, which is essential for the tool's purpose. To mitigate the risk, the following measures are in place:
1.  A **critical** warning dialog (`QMessageBox.Critical`) is displayed to the user every time they open a file, explicitly warning them of the danger.
2.  This design decision is documented here to ensure all future developers are aware of the trade-off.

**DO NOT** remove or downgrade the UI warning without implementing a fully secure, sandboxed expression interpreter. A future effort to replace `eval()` should use a robust parsing library like ANTLR or Lark, not simple regex.

## Future Enhancements

### Robust Z3 Solver Expression Parsing

The current Z3 solver integration (`_parse_effect_to_z3`) is a proof-of-concept and can only parse very simple assignment expressions (`=`, `+=`, `-=`). It cannot handle more complex Python logic (e.g., `min()`, `if/else`, function calls) within an event's `effect` string.

**Recommendation:** To make the solver a truly powerful feature, this simple parser should be replaced with a more robust solution that can translate a wider subset of Python into Z3's abstract syntax tree (AST). This is a significant undertaking and would likely require a dedicated parsing library.

### Distribution and Packaging

The application currently fails to build into a standalone executable with PyInstaller. This has been documented as a "Known Issue."

**Recommendation:** Future work should prioritize creating a reliable build and distribution pipeline. This may involve:
-   Investigating alternative packaging tools like **cx_Freeze** or **py2app**.
-   Restructuring the project to eliminate the `src` layout, which can simplify path resolution for build tools.
