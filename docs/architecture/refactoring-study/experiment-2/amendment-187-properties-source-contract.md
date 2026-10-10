# Amendment 187 — mutable Properties source contract

The existing Properties path accepts both mutable string dictionaries from the
file loader and explicitly typed native dictionaries from Python callers. Its
source type is `dict[str, str] | dict[str, object]`, with `| None` only at
nullable entries. This follows the reviewed Slice 168 source decision and the
bounded [Runtime policy](amendment-186-runtime-properties-policy.md).

The inline union runs through `DataMimic`, `RunRequest`, descriptor and statement
parsers, dispatch, `SetupTask`, and `SetupContext` storage/getter/setter. The
string file/profile loaders and XML descriptor attributes remain string maps.
`fulfill_credentials` returns `dict[str, object]` because native property values
can override string attributes. It copies the XML-string attribute dictionary
once with `dict(descriptor_attr)`; the other existing deep copies, identity,
truthiness, include updates, and native errors stay in place.

The target permits only the complete union at two DSL parser positions and six
Runtime request/context positions. A separate depth-one permission accepts the
native value leaf; it records opacity, not validation or serialization. The two
obsolete string-only request permissions are removed. Published ArchKeel 1.1.1
was checked with the frozen union fixture: 7 findings without grants, 3 with
outer grants, 1 with native-leaf grants; the fixed control and four UNKNOWN
records remain equal.

The [candidate receipt](step-173-properties-source-contract-receipt.json) pins
the full CE reports. Against the prior 20-finding packet, the candidate has 17
findings and no added finding. All surviving findings match exactly. The 254
UNKNOWN IDs remain; three existing UNKNOWN texts change because the inherited
getter/setter annotation now names the union. `declared_rules` remains FAIL.

External typed callers and the 25 older bare-dict parser constructors remain
unproved. No full DSL/EE or standalone XML parity follows from this amendment.

LOCAL VERIFIED: 119 focused tests, 2,345 CE unit tests (11 skipped, one expected
failure), 13 definition checks, Ruff, full MyPy, published 1.1.1 union controls
and full report comparison. Native validation exits 2 with 19 unchanged usage
diagnostics and 11 baseline-new groups. CI-ONLY VERIFICATION: both exact-head
`019f9cbc` runs ([first](https://github.com/rapiddweller/datamimic/actions/runs/38038847145),
[second](https://github.com/rapiddweller/datamimic/actions/runs/38038851779))
completed; ordinary jobs passed and the two architecture jobs failed at the
open zero target.
An isolated MyPy probe accepts typed string/native dictionaries and rejects
`dict[str, int]`, read-only `Mapping`, and object writes through the union.
