# Amendment 122: Doctor office-hours ownership

Date: 2026-10-08. Decision: Astra-advised, coordinator-approved target clarification.

Assign office-hour sampling and formatting to `DoctorGenerator`. `Doctor` keeps
the lazy cached `office_hours` property and calls the generator.

Preserve one public RNG lookup; weekday then weekend order; conditional hour
draws and existing bounds/thresholds; output key order, formatting and
`Closed` values; cached dictionary identity; and failure/retry behavior.
