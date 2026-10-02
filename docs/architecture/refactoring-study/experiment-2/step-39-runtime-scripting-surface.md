# Step 39: Keep the scripting context public

`Context` and `SetupContext` remain public by class identity. Checked-in scripts use `isinstance(context, SetupContext)` and `get_client_by_id`; the public API test asserts the exported classes are the implementation classes. Replacing them with a protocol or wrapper would change this behavior.

The `RUNTIME-API-TYPES` rationale now states that this is a scripting surface with reviewed dynamic state, not only request/result DTOs. The rule is unchanged and its findings remain visible. Exact top-level map allowances need ArchKeel [#207](https://github.com/rapiddweller/archkeel/issues/207); no broad class exemption or DTO wrapper was added.
