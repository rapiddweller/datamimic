# Amendment 97: Bank-account balance generation ownership

Date: 2026-10-07. Decision: Astra-advised, coordinator-approved implementation.

Move the existing balance draw to `BankAccountGenerator`. The model property
remains cached and its setter still replaces the cached value without drawing.
The same RNG expression, lazy timing, and seeded output are preserved. No
descriptor or existing API behavior changes; adds the generator operation.
