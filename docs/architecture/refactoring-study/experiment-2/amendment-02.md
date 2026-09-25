# Amendment 02: stop using string equality as a dispatch proxy

## Decision

Remove `string_literal_compare` from the global `NO-MAGIC-CONTROL-FLOW` rule. Keep the target that
closed-vocabulary routing uses enums and verify each migrated routing owner with focused tests.

## Evidence

- The rule reported 163 comparisons after Step 1.
- 75 were in domain code and included comparisons of ordinary generated values such as department,
  city, and title data.
- Other false positives included XML syntax checks and external client value handling.
- ArchKeel 0.6.0 reports syntax only; it does not distinguish dispatch from data comparison.

## Why this is a correction

The frozen rule claimed to measure string-literal dispatch, but it measured every string-literal
comparison. Rewriting normal data comparisons into enums would change semantics without improving
the architecture. This amendment removes the invalid proxy, not the enum-routing target.

The remaining `Any`, reflection, cast, and type-ignore checks stay global. Public API signatures
also receive `boundary_types` rules as soon as their real functions exist.
