# Step 19: Zero rows and guaranteed nulls

Two owning tests now check behavior that the generic shape oracle cannot infer:
an empty CSV produces exactly `{"g": []}`, and `nullQuota="1"`/`"0"` produce
ten rows with a present null/non-null field respectively. The XML is unchanged.

LOCAL VERIFIED: Both tests passed on the current branch and against the frozen
Step 0 code (`3b844b5`) using the same updated tests and descriptors. QA
independently reviewed the assertions. The unseeded `nullQuota="0.5"` field is
not asserted to have an exact count; its sampled shape and zero-row element
shape remain `UNKNOWN` in the generic comparator. These two owning tests are
supplementary evidence, not a full descriptor-parity waiver.

CI-ONLY VERIFICATION: not run. The remaining incomplete descriptor records
and architecture `boundary_types` findings are not resolved by this step.
