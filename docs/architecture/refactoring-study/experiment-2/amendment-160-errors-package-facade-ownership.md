# Amendment 160 — error package facade ownership

Date: 2026-10-08. Decision: Astra-decided target clarification.

`ERRORS-FACTORY` owns `datamimic_ce.errors` as the existing package-level
composition of error classes, codes, and the factory entry point. The package
continues to re-export the same objects; `ERRORS-BASE` and `ERRORS-CODES` retain
ownership of the defining types and enums.

This assigns the facade module without changing `__all__`, public grants,
imports, or dependency permissions.
