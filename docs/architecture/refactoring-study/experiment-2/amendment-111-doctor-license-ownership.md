# Amendment 111: Doctor license-number ownership

Date: 2026-10-07. Decision: Astra-advised, coordinator-approved implementation.

Move cached license-number generation to `DoctorGenerator`. Preserve one public
RNG lookup, two ordered `choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")` calls followed
by six sequential `randint(0, 9)` draws, hyphen formatting, leading zeroes, and
the model cache. Do not add validation or a dedicated RNG policy. No descriptor
or existing API behavior changes; adds the generator operation.
