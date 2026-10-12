# Amendment 63: exact domain model exports

Decision: Keep the existing `finance.CreditCard`, `healthcare.Doctor`, and
`healthcare.Patient` package exports in the external Python API declaration.
Narrow the shared City, Company, and Country internal entries from whole modules
to their concrete classes. Do not remove the 13 internal model promises: published
`BaseDomainService[Model]` services return those types.

Evidence: CE and EE package exports and service signatures; independent QA import
checks. ArchKeel [#204](https://github.com/rapiddweller/archkeel/issues/204)
tracks the generic inherited-return proof missing from `interface.unused`.

The machine amendment cannot yet be generated: candidate `archkeel validate`
exits 2 on those 13 diagnostics. This is open, not a passing gate.
