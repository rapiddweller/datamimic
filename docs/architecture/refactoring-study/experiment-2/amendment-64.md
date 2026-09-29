# Amendment 64: declare inherited domain service result types

Date: 2026-09-29. Decision: Astra.

The inherited `BaseDomainService[T]` methods expose six concrete model types through
the supported domain services. Add the exact `Address`, `City`, `Company`, `Country`,
`Person`, and `Patient` symbols to the root Domains component. In the nested contract,
`DOMAINS-SHARED` owns the five shared model symbols (narrowing its existing module-wide
Address and Person declarations to exact classes); `DOMAINS-HEALTHCARE` already owns
Patient. `DOMAINS-API` continues to own only its service API symbols.

This corrects the target's boundary declaration; it does not add package-level
convenience exports, change runtime behavior or registry typing, or suppress the six
registry findings. The focused contract test checks both declarations and confirms
these model symbols are not added to the external `public_api` list. The ArchKeel report
still contains all six concrete-service `set_identifier_registry` dictionary findings,
as well as the base-service finding; none were suppressed.
