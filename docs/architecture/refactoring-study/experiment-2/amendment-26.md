# Amendment 26: publish the runtime generator catalog

Date: 2026-09-28. Astra decision during the final-boundary review.

`runtime.api` already reads `RUNTIME_GENERATOR_TYPES` from the Values
constructor module to describe generator capabilities. Publish that exact
symbol through the Tasks and Values contracts. No implementation or dependency
edge changes; the contracts now describe the existing access without making
the whole constructor module public.
