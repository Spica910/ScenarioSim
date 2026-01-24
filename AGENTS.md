# Agent Instructions

## Final Design Decisions & Known Issues

### 1. Expression Engine: Reverted to `eval()`/`exec()` for Correctness

A significant effort was made to replace Python's `eval()` and `exec()` with a custom, secure expression evaluator (`SafeExpression` using the `ast` module). **This attempt ultimately failed.**

While the goal was to improve security, the custom implementation (`safe_exec`) contained subtle but critical bugs related to context management during sequential statement execution. These bugs prevented the simulation engine from correctly applying state transitions, causing it to explore only a tiny fraction of the state space (4 states instead of the correct 472+).

**Final Decision:**
The implementation has been **reverted to the original `eval()`/`exec()` based logic**. This approach, while carrying security risks, is **functionally correct** and allows the simulation engine to perform as intended.

**Mitigation:**
- The security risk is acknowledged and mitigated by a `QMessageBox.Critical` warning in the UI, which forcefully informs the user of the dangers of opening untrusted files.
- The `eval`/`exec` calls are restricted to only allow safe built-ins like `min` and `max`.

This trade-off (correctness over incomplete security) was deemed necessary to deliver a working tool.

### 2. Z3 Solver: Proof-of-Concept State

The Z3 solver integration was reverted along with the `SafeExpression` changes. Its ability to parse Python expressions into Z3 constraints is a complex task that was tied to the failed AST implementation. The current `run_solver_explorer` is a placeholder. A robust implementation remains a task for future work.

### 3. Build & Distribution

Creating a standalone executable with PyInstaller consistently failed due to environment-specific issues with module resolution and Qt platform plugins. The application should be run from source.
