# Amendment 153: Administration office email department

Date: 2026-10-08. Decision: coordinator-approved target clarification.

Assign the ordered office-type-to-department mapping to
`AdministrationOfficeGenerator`. `AdministrationOffice` keeps website/domain
handling, type normalization, email composition, and its lazy cache. Preserve
branch priority, access order, output, and failure/retry behavior.
