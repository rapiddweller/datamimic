# Amendment 83: state-machine definition owner

2026-10-01. Decision: Astra. Declare the existing `StateMachineDef` at
Domain core's generation-contract boundary after moving it out of the concrete
walker. ArchKeel classifies that exact internal export as a promotion; no rule,
allowance, baseline or budget changes. The public Domain facade keeps one
canonical class. CE5 changes its defining module, without an old-path shim.
