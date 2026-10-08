# Amendment 93: Medical-device identifier ownership

Date: 2026-10-07. Decision: Astra-advised, coordinator-approved implementation.

Clarify that `MedicalDeviceGenerator` owns model-number and serial-number
generation. The existing target assigns value generation to generators while
models expose cached fields; the previous responsibility text did not make the
identifier ownership clear.

No dependency, public grant, rule, budget, descriptor, or behavior changes.
