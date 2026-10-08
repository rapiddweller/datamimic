# Amendment 130: insurance policy coverage-count ownership

Date: 2026-10-08. Decision: coordinator-approved target clarification.

Assign the policy coverage-count draw to `InsurancePolicyGenerator`.
`InsurancePolicy` retains lazy coverage construction and its cached list.

Preserve the single public RNG access, inclusive `randint(1, 3)` draw, child
coverage construction order, and retry after a failed count draw.
