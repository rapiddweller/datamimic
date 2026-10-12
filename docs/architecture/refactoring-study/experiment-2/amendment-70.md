# Amendment 70: declare Runtime demographic context

Date: 2026-09-29. Decision: Astra.

`SetupContext` already accepts, returns and sets Runtime-owned
`DemographicContext`. `runtime.api` now re-exports that existing class; the
Runtime API and contexts modules are already declared public by their owning
components. No new model or compatibility path is introduced.

`DemographicConfig.transaction_profile` deliberately accepts a named profile or
an open `Mapping[str, float]` of weights. The three exact nested Runtime API
positions are allowed; other mapping positions remain findings. ArchKeel's
previous generic UNKNOWN for this type is not treated as a pass. AD-123 first
classifies proven standard-library mappings as broad maps, then these three
exact allowances record the reviewed exception.

The target still requires zero unreviewed violations and UNKNOWN positions.
