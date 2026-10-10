# Step 38: Type the source-length cache

`SetupContext.data_source_len` now declares its real key and value: `dict[tuple[str | None, str | None], int]`. The key comes from `data_source_cache_key`; `set_data_source_length` is the only production writer. No data flow or descriptor changed.

Independent QA found an existing test for equal product names with different sources. The focused source/context tests passed (79); GenerateTask tests passed (21, 11 skipped). Full-package mypy and Ruff passed.

ArchKeel now reports 123 violations and 194 unknown positions, versus 122 and 195 before this step. The extra finding is the typed cache property on the public `SetupContext`; the constructor's map was already a violation. This is a contract-policy question, not evidence that the cache needs a DTO. The target gate remains red; no rule was relaxed.
