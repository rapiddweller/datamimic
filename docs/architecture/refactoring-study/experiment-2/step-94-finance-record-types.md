# Step 94: Type finance records

Replace bare `dict` annotations for Bank data and cached credit-card specifications with their
actual field types. Keep the existing dictionaries, cache identity, CSV parsing, RNG calls,
consumer fallbacks, descriptors, and generated values unchanged.

**LOCAL VERIFIED:** Bank and credit-card API/serialization tests; seeded determinism test; Ruff
on changed Finance modules; full-package mypy (492 files); `git diff --check`.

**NOT VERIFIED:** ArchKeel 1.0.0 validation and CI. This is not a completed architecture gate or
descriptor-suite acceptance.
