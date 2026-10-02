# Amendment 45: define flow semantic leaves

Date: 2026-09-28.

Mount a flow contract from TASKS-FLOW with five leaves: branches, loops,
assertion, diagnostics, and script execution. Keep commands as physical
grouping; leaves have no cross-leaf dependencies. ExecuteTask is valid in
setup and nested-key scope, not as a direct generate child. Keep
IfElseBaseTask internal to branch adapters.
