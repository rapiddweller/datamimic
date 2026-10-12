# Amendment 90: native client registry

2026-10-02. Decision: Astra, delegated architect. Base `b15d265b`.

Runtime owns the mutable client-ID registry; IO owns SQL capability validation
and execution. Descriptor IDs are open keys with Client values, not fields of a
fixed record. A wrapper would add no invariant and break dictionary identity.
The blanket collection ban was the wrong target for this registry.

Admit only three RUNTIME-API-TYPES positions, all with empty field_path:
SetupContext.__init__/clients (`dict[str, Client] | None`) and
SetupContext.clients/return and /value (`dict[str, Client]`). Names are qualified
under datamimic_ce.engine.runtime.api. No bare dictionary, object/Any value,
other member, control map, baseline or budget is admitted. The getter and setter
share a name but have distinct positions. Do not remove annotations to hide debt.

SQL supports RdbmsClient and subclasses. A Client-only SQL implementation is
rejected; unsupported clients now raise the operation's TypeError instead of
incidental AttributeError. Non-string registry keys are outside the typed API.
External use is UNKNOWN. No shim, runtime registration validation, namespace
change or claim that historical ArchKeel #228 is fixed.

The source-only report exposed the setter: 106/157 violations/UNKNOWN became
107/154. This correction requires fresh positive and negative checker probes;
it is not permission to grow the baseline or count UNKNOWN as PASS. Valid DSL,
queries, interpolation, client identity, disposal and deepcopy stay unchanged.

Published-checker full rescan: 104/154, with exactly three allowance FACTs and
source evidence. Removing each entry restores only its violation. Bare,
object/Any-valued, wrong-key and union maps fail at all three seams; an
unresolved Client retains three seam-local UNKNOWNs. No blanket suppression or
checker blocker was demonstrated. Global acceptance remains FAIL.
