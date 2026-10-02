# Amendment 64: declare inherited domain service result types

Date: 2026-09-29. Decision: Astra.

The inherited `BaseDomainService[T]` methods expose six concrete model types through
the supported domain services. Add the exact `Address`, `City`, `Company`, `Country`,
`Person`, and `Patient` symbols to the root Domains component. In the nested contract,
`DOMAINS-SHARED` owns the five shared model symbols (narrowing its existing module-wide
Address and Person declarations to exact classes); `DOMAINS-HEALTHCARE` already owns
Patient. `DOMAINS-API` continues to own only its service API symbols.

This corrects the target's boundary declaration; it does not add package-level
convenience exports, change runtime behavior or registry typing. The focused
test checks exact ownership and excludes these symbols from the external
`public_api` list.

LOCAL VERIFIED on isolated commit `c5e07e9c`: nine ownership/architecture
tests and five target-definition tests passed. The pinned ArchKeel checker
parsed all 491 files and moved from 108 to 96 violations and from 86 to 74
baseline-new findings; UNKNOWN positions stayed at 176. The architecture gate
still fails. Full descriptor and service-backed verification remain open.
