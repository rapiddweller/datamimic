# Amendment 152: Company URL scheme

Date: 2026-10-08. Decision: coordinator-approved target clarification.

Assign only HTTP/HTTPS scheme selection to `CompanyGenerator`. `Company` keeps
the URL composition from its cached email domain. Preserve the scheme draw
before lazy email resolution, URL/email caches, output, and failure/retry RNG
behavior.
