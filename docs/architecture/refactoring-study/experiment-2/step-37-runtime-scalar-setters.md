# Step 37: Runtime scalar setters

`SetupContext` now declares the setter types for multiprocessing, process count, variable delimiters, and report logging. The types match its getters and guarded `SetupStatement` updates; behavior and descriptors are unchanged.

Independent QA added one test for omitted setup values preserving inherited settings. All five context tests, Ruff, and full-package mypy pass. With the same local ArchKeel analyzer, `unknown_positions` fell from 201 to 195; violations remain at 122. The target gate still fails.
