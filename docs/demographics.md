# Demographic Profiles

Demographic profiles provide reusable population priors for age/sex distributions and
condition prevalence. Profiles live as versioned CSV bundles that are loaded at runtime
and exposed through an explicit `DemographicContext` so generators can honour priors
without relying on globals.

## `.dmgrp.csv` contract

All demographic files share the `.dmgrp.csv` suffix to simplify discovery and
versioning. A complete profile currently consists of:

- `age_pyramid.dmgrp.csv`
  - Columns: `dataset,version,sex,age_min,age_max,weight`
  - Weights normalise to 1.0 per sex bucket (or overall when `sex` is empty).
- `condition_rates.dmgrp.csv`
  - Columns: `dataset,version,condition,sex,age_min,age_max,prevalence`
  - `prevalence` is expressed as a probability in `[0,1]`.
- `profile_meta.dmgrp.csv` (optional metadata placeholder)
  - Columns: `dataset,version,source,notes,checksum`

Additional `.dmgrp.csv` files are ignored until the corresponding loader support is
implemented, which keeps the bundle forward compatible.

## XML usage

Declare demographics inside `<setup>` to make the profile and seeded sampler available
to all entities generated within the descriptor:

```xml
<setup>
  <demographics dataset="DE" version="2023Q4"
                dir="examples/demographics/DE/2023Q4" rngSeed="42"/>
  <generate name="cohort" count="1000" target="CSV">
    <variable name="patient" entity="Patient" dataset="DE" rngSeed="1234"/>
    <key name="age" script="patient.age"/>
    <array name="conditions" script="patient.conditions"/>
  </generate>
</setup>
```

- The loader validates dataset/version columns, ensures age buckets do not overlap and
  raises descriptive errors for malformed rows.
- Each entity supported by demographics (`Person`, `Patient`, `Doctor`,
  `PoliceOfficer`) receives the sampler together with an entity-scoped RNG derived from
  the `<demographics>` `rngSeed`.
- `DemographicConfig` overrides (`ageMin`, `ageMax`, `conditionsInclude`,
  `conditionsExclude`) remain available per variable and win over sampler priors.

## Determinism and seeds

The `<demographics>` node seeds a root RNG. Variable-level `rngSeed` attributes still
work; when omitted, the task derives child RNGs from the demographic context so every
entity consumes disjoint deterministic streams. Loader validation is pure, and the
sampler has no hidden state, which keeps test runs reproducible.

## Limitations

- Sex selection defaults to a uniform choice across available sex buckets until richer
  marginal distributions are supplied.
- Condition prevalence is modelled as independent Bernoulli trials; comorbidity pairs
  are not sampled yet.
- Birthdates outside `[0,100]` trigger warnings so unrealistic priors can be spotted
  early.

## Roadmap

Pairwise odds ratios will eventually be supported behind a feature flag. Until then,
set `DEMOGRAPHY_PAIRS=false` in the environment to document the current limitation.
