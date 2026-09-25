# Step 08C23: fail closed on incomplete architecture verdicts

## Change

- `make architecture-check` still uses pinned ArchKeel 0.6.1, but now checks
  the JSON verdict as well as the process result. It requires complete
  observation, passing coverage and declared rules, zero violations and
  material unknown positions, and no baseline delta.
- No contract, baseline, source, or descriptor change.

## Evidence

- Negative probe: a typed public generator-return annotation caused ArchKeel
  to emit `exit_code=0`, `declared_rules=UNKNOWN`, `unknown_positions=1`.
  The Make target failed while printing the JSON. The typing slice was then
  reverted; see Step 08C21.
- Positive probe: the current worktree, run with the published 0.6.1 version
  already in the local uv cache and `UV_OFFLINE=1`, passed: 474/474 source
  files, `declared_rules=PASS`, complete observation, coverage PASS, zero
  violations, zero material unknown positions, and zero baseline delta.
- A network-blocked `uvx` fetch produces no JSON and the guard fails closed.
  Remote CI has not run; local offline success is not a CI claim.
