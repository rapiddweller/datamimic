# Amendment 164 — truthful Authoring scope guidance

Date: 2026-10-08. Decision: Astra-approved public projection correction.

CE Authoring must describe the existing name-resolution behavior truthfully.
Two independent native probes generated a nested bare sibling successfully,
while an intermediate-ancestor failure received a hint saying bare names only
resolve at top level. Four isolated native owner tests confirmed scope precedence.

Replace only `_SCOPE_HINT` with conditional name/structure guidance: current
names can resolve bare; existing outermost bare names win collisions; other
ancestors need qualification. Alias collisions retain their current behavior.
This intentionally changes public `fix_hint` text exposed by CLI/MCP/JSON.

Preserve resolver, native exceptions/messages, hint dispatch, IPC and diagnostic
code/severity/path. Native ancestor-guidance wording remains separate open debt.
Historical projections contain no full-hint oracle; external consumers remain
UNKNOWN. No frozen expectation, architecture grant or compatibility waiver changes.
