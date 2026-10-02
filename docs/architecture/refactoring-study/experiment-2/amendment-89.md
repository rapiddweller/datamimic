# Amendment 89: native descriptor properties

2026-10-02. Decision: Astra, delegated architect. Base `3f604a3b`.

Interfaces adapt input; Runtime sequences execution; DSL parses properties and
merges credentials. These owners do not change. Delete only PlatformProperties:
the inspected callers bypassed its validation with model_construct and Runtime
immediately unwrapped it. Keep RunRequest and PlatformConfiguration.

Pass the native `dict[str, str] | None` unchanged through the Python adapter,
RunRequest and both parser/SetupTask calls. The descriptor loader returns its
parser map directly and still catches only FileNotFoundError. Preserve None,
empty/populated identity and mutation, error propagation and configuration.
No shim, new validation, copy, coercion or narrower DSL payload.

RUNTIME-API-TYPES retains capture permissions and adds exactly three string-map
positions: load_descriptor_properties return (`field_path: ""`), and
create_run_session/run request.platform_props. All names are qualified below
datamimic_ce.engine.runtime.api; every annotation is `dict[str, str]`.
The original plan's absent field path was a format error. Released 0.8.4 requires
the documented empty string for a top-level selector; Astra approved that same
position, not broader semantics.

Independent published-checker preflight: 106/157 violations/UNKNOWN at base,
109/157 source-only, 106/157 exact-amended. Wrong property paths restore two
findings. An unrelated fixed request map still produces two findings despite
the descriptor_path UNKNOWN. Changing the loader to object-valued map produces
two findings despite its string-map allowance. No blocker exists for this slice.
Repository baseline remains unchanged; global architecture is still FAIL.

External Python wrapper imports/constructors are UNKNOWN and may break under
the approved CE5.0 no-shim target. Selected CE behavior checks are not proof of
full corpus parity, EE equivalence or completion of every semantic leaf.
