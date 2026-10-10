# Amendment 100: Doctor acceptance generation ownership

Date: 2026-10-07. Decision: architect-approved, Astra-advised implementation.

Move the lazy `accepting_new_patients` draw to `DoctorGenerator`. Preserve the
public `rng` accessor, one draw, and strict `< 0.8` threshold; the cached model
property remains lazy. Subclasses overriding `rng` continue to control this
draw. No descriptor or existing API behavior changes; adds the generator operation.
