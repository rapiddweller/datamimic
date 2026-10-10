# Amendment 91: raw DSL attributes

2026-10-02. Boundary decision: Astra, delegated architect. Base `bd19d370`.
Status: accepted for the bounded local slice; whole-goal acceptance remains open.
Tracking: [ArchKeel #253](https://github.com/rapiddweller/archkeel/issues/253).

DSL validation receives attributes before model field validation. XML names
and extension keys are open; Python values can be strings, numbers, booleans,
None or invalid objects that must reach existing validation. Successful checks
return the original dictionary. A fixed record or wrapper would misrepresent
this stage and change identity without adding an invariant.

Admit only `check_constraints`, `check_exist_count`,
`check_weights_require_values` and `check_min_max_count`, qualified under
`datamimic_ce.engine.dsl.api`, at `values` and `return`, empty `field_path`.
The decision covers eight boundary positions: `values` and `return` for each
of the four operations. Each position has two exact signals: the outer
`dict[str, object]` annotation and its nested `object` values (16 signal
decisions total). Opaque values are accepted at this pre-validation boundary;
this does not prove type closure. Constraint records, other
parameters/functions, Any/bare dictionaries and wrong key types remain
restricted. Raw input acceptance is not descriptor validity.

### Historical ArchKeel 0.8.4 observations

The source-only measurement was 103 -> 111 violations, with 154 counted
UNKNOWN unchanged. The old eight bare-dictionary findings became sixteen
explicit container/value signals. No baseline, budget, gate, schema, descriptor
or oracle changed. Lazy constraint suppliers kept their unresolved evidence
visible.

The 0.8.4 checker accepted the eight outer-map allowances but left the eight
nested-object decisions unresolved. The recorded outer-map-only run had 103
violations and 154 counted UNKNOWN. An empty-path `object` allowance failed
decoding because 0.8.4 had no supported map-value selector. The unchanged
count did not prove acceptance.

### Current ArchKeel 0.8.5 bounded acceptance

ArchKeel 0.8.5 publishes the required `container_depth: 1` map-value selector;
the Makefile pin uses that release without changing gate logic. Fresh local
bounded acceptance removed exactly eight findings (103 -> 95), with no added
or changed remaining finding. All 204 raw UNKNOWN records retain their IDs
and semantics; 150 remain counted. The `constraints.values` generic UNKNOWN
has updated source-symbol/evidence references for the new annotation. Baseline
new is 67 -> 63, baseline resolved remains 0, and baseline, budget and oracle
are unchanged. Fresh QA and Astra review pass for this slice. Lazy
constraint-supplier UNKNOWN evidence remains visible; these results do not
claim whole-goal acceptance.

Runtime behavior, first failure, messages, coercion timing, dictionary/nested
identity and lint-only policy remain unchanged. Static callers with invariant
`dict[str, str]` may need their annotation widened; external usage is UNKNOWN.
This does not admit Runtime properties, IO rows or generator state, or complete
the physical/semantic target. The remaining 95 violations and 150 counted
UNKNOWN are not gate-green.
