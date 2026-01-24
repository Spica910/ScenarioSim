# Agent Instructions

## Final Design Decisions & Known Issues

### 1. Security: `eval()` Usage and Mitigation

This application uses Python's built-in `eval()` and `exec()` functions to interpret the `condition` and `effect` expressions within a scenario. This design choice was made for flexibility and functional correctness, but it carries a **critical security risk**.

**Risk:**
A malicious or improperly designed scenario file could execute arbitrary code on the user's machine, potentially leading to data loss or system compromise.

**Attempted Alternative:**
An attempt to create a secure, custom Abstract Syntax Tree (AST) based parser was made. However, this implementation proved to be buggy and functionally incorrect, failing to properly simulate complex state transitions. It was therefore reverted.

**Final Decision & Mitigation:**
- **The use of `eval()` remains in the codebase.** This is a known and accepted trade-off to ensure the simulation engine works as intended.
- **The primary mitigation is user-facing.** The GUI displays a **prominent, non-dismissible critical security warning** every time a user opens a file. This warning explicitly states the risks and requires the user to consciously accept them before proceeding.
- This approach places the responsibility on the user to only open and execute scenarios from trusted sources.

### 2. Z3 Solver: Fully Functional

The Z3 solver integration has been successfully re-implemented and is now fully functional. It correctly uses Bounded Model Checking (BMC) to find violation paths for complex scenarios, including those with conditional logic.

- **Architecture**: The solver now correctly models state transitions using `Implies(event_chosen, effect_applied)` logic, resolving the critical flaw in the previous design.
- **Testing**: All unit tests for the solver, including the previously disabled `test_finds_path_with_conditional_assignment`, are now passing.

### 3. Build & Distribution: **Failed - Run from Source Recommended**

Creating a standalone executable with `PyInstaller` **consistently fails** in the provided Linux sandbox environment. This is due to intractable dependency issues between `PyInstaller` and the low-level system libraries required by the Qt platform plugins (e.g., X11 libraries like `libxcb`).

**Final Attempt Summary:**
- **Method**: Used the `pyinstaller-hooks-contrib` library and the `--collect-all pyside6` flag, which is the standard automated way to bundle all necessary components.
- **Result**: The build still failed at runtime with the same error: `Could not load the Qt platform plugin "xcb" ... even though it was found.`
- **Conclusion**: The issue is not with finding the plugin files themselves, but with the plugins being unable to load their own system-level dependencies within the bundled environment. This is a limitation of the sandbox environment, not a simple packaging error.

**Therefore, the official and only supported way to run this application is from source.**

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the application
python main.py
```

## Building the Application

This project uses PyInstaller to package the application into a single executable file.

### Prerequisites
- Python 3
- `pip`

### Build Command

To build the application, run the following command from the root of the repository:

```bash
pyinstaller --onefile --windowed --icon=icon.ico main.py
```

- `--onefile`: Creates a single executable file.
- `--windowed`: Prevents a console window from appearing when the application is run.
- `--icon=icon.ico`: Sets the application icon.

The resulting executable will be located in the `dist/` directory.

### Build Status: **FAILED - Run from Source Recommended**

Creating a standalone executable with PyInstaller has **consistently failed** in the provided Linux sandbox environment due to intractable dependency issues with the Qt platform plugins.

**Summary of Attempts and Errors:**

1.  **Initial Failure**: `libz3.so not found`.
    *   **Solution**: Resolved by using `--add-binary` to include the shared library.
2.  **Second Failure**: `Qt platform plugin "xcb" could not be initialized`.
    *   **Attempted Solution**: Used `--add-data` to explicitly copy the `PySide6/Qt/plugins` directory into the build.
3.  **Third Failure**: `Could not load the Qt platform plugin "xcb" ... even though it was found.`
    *   **Analysis**: This final error indicates that while the plugin file (`libqxcb.so`) is now being found (thanks to the previous step), the plugin itself has deeper system-level dependencies (e.g., specific versions of `libxcb-cursor.so`) that are not present in the bundled application's environment.
    *   **Attempted Solution**: A `run.sh` wrapper script was created to set the `QT_QPA_PLATFORM_PLUGIN_PATH` environment variable. This confirmed the diagnosis but did not solve the underlying missing dependency issue.

**Final Conclusion:**
A robust, distributable executable cannot be reliably built in this environment. The deep dependencies of the Qt platform plugins require a more controlled and consistent build environment than is available.

**Therefore, the official and recommended way to run this application is from source.**

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

The build instructions below are kept for archival purposes but are not expected to work in this environment.

---
## Archived Build Instructions

### Building for Linux (Non-functional)
```bash
pyinstaller --onefile --windowed --icon=icon.ico \
--add-binary /path/to/libz3.so:z3/lib \
--add-data /path/to/PySide6/Qt/plugins:PySide6/Qt/plugins \
main.py
```

### Building for Windows

The process for building a standalone executable on Windows is similar, but requires pointing to the Windows-specific `z3.dll` library.

### Finding `z3.dll`
You must first locate the `z3.dll` file within your Python environment. It is typically found in `path\\to\\python\\Lib\\site-packages\\z3\\lib\\z3.dll`.

### Windows Build Command
```bash
pyinstaller --onefile --windowed --icon=icon.ico --add-binary "path\\to\\z3.dll;z3\\lib" main.py
```
- Note the use of a semicolon (`;`) as the path separator for the `--add-binary` flag on Windows.
- The `--icon` flag is fully supported on Windows and will embed the icon into the executable.
