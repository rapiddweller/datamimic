# Amendment 133: administration-office hours ownership

Date: 2026-10-08. Decision: coordinator-approved target clarification.

Assign operating-hours dataset loading, RNG draws, and the shared anti-repeat
signature to `AdministrationOfficeGenerator`. `AdministrationOffice` retains
its lazy cached property and delegates without changing output or draw order.
