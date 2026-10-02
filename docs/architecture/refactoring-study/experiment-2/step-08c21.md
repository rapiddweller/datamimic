# Step 08C21: defer built-in generator typing boundary

## Change

- Tried `type[BaseLiteralGenerator | BaseDomainGenerator]` and the equivalent
  `type[BaseLiteralGenerator] | type[BaseDomainGenerator]` across the registry
  and public iterator. Reverted the slice because the pinned architecture gate
  leaves its return position `UNKNOWN`.
- No contract or baseline changes.

## Evidence

- ArchKeel 0.6.1, exact baseline: exit 0, 474/474 files parsed, 0 violations,
  but `declared_rules=UNKNOWN` and `unknown_positions=1`. The alternate union
  spelling did not clear the unknown position.
- Full-package mypy passed: 474 source files, no issues. A disposable negative
  probe rejected an unrelated class assigned to the narrowed generator type.
- Focused inventory test passed (1 test); Ruff and `git diff --check` passed.
- The type boundary remains deferred until ArchKeel can prove it without
  widening the contract or baseline.
