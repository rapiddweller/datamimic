# CE / EE physical alignment

Status: shared target decided by Astra under Alex's delegation; implementation target,
not evidence that either checkout currently conforms. Source snapshot: CE
`3b844b5083e5af89269ef917bc0614601d30cf61`; EE experiment
`30889502599b81e7ea8087269cb09a5f9168f094`. EE main at `dc7526592` is dirty
and excluded as a clean execution baseline. Astra additionally inspected its
committed core read-only; no EE edits are authorized by this CE migration.
The final [semantic decisions](semantic-review/astra-target-decision.md) override
earlier placements below where explicitly corrected.

## Shared paths and EE migration

Shared code moves to the same physical owner in both editions. Move by behavior,
not by current import or package boundary. The table inventories EE's current
root owners; line references are from the EE experiment snapshot.

| EE source owner | Shared target | Placement rule / evidence |
|---|---|---|
| `authoring/` | `authoring/{api.py,contracts.py,spec,domain,application,adapters,projection}` | Keep typed requests and use cases here; see `authoring/application/app.py:42-58`, `authoring/domain/requests.py:85-155`. |
| `contract_bundle/` | `authoring/adapters/` | Bundle assembly may gather Authoring and DSL projections; DSL must not import Authoring. |
| `model/` | `engine/dsl/model/` | Typed XML grammar and element facts. Descriptor value types belong to DSL; concrete connector/configuration behavior belongs to IO. DSL must not import IO. |
| `model/{generator_model,state_machine_model,transition_model}.py` | `engine/dsl/model/setup/generators/` | CE and EE share the named-generator definition family here; this is an EE target, not a claim that its files have moved. |
| `parsers/`, `statements/` | `engine/dsl/parsers/`, `engine/dsl/statements/` | Parsing composition and executable DSL meaning stay with DSL; parser-to-statement binding is not Runtime ownership. |
| `dsl_contract/` | Split by owner | `models` with DSL contracts; registry with parser composition; reflection with the runtime evaluator it reflects; projections consume supplied facts. Bundle assembly is currently in `contract_bundle/`, not `dsl_contract/bundle.py`. Do not move the package wholesale. |
| `constants/`, `contracts/` | Owning DSL, IO, or Runtime subtree | DSL vocabulary/constants/enums, properties, and XML parser/document belong to DSL; transport and source/export types to IO; run DTOs to Runtime. No replacement catch-all package. |
| `contexts/`, `lifecycle/`, `logger/`, `factory/`, `utils/process_util.py` | `engine/runtime/{contexts,lifecycle,logging.py}` | Process setup/title and invocation stay in Lifecycle (`lifecycle/entrypoint.py:14-20`, `utils/process_util.py`); keep existing factory operations at Runtime boundary. |
| `tasks/` | `engine/runtime/tasks/` | Generation orchestration/workers under `tasks/generate`; shared count expression resolution under `tasks/base`; runtime value generators and their selection under `tasks/values/construction`; source adapters under `tasks/sources`. |
| `engine/runtime/generators/sequence_table.py` | `engine/runtime/tasks/values/construction/sequence_table.py` | Keep page-stateful sequence generation beside the global increment runtime generator and its factory. |
| `data_sources/` | `engine/io/data_sources/` | Source routing, pure selection, paging and loading policy belong to IO, not task orchestration (`data_sources/data_source_registry.py:23-29`). |
| `exporters/`, `clients/` | `engine/io/{exporters,clients}/` | Exporters own writes; clients own connectivity (`exporters/export_registration.py:8-13`, `clients/registry.py:3-10`). Tasks use IO boundaries, never construct clients. |
| `domains/` | `domains/{domain_core,shared,finance,healthcare,insurance,ecommerce,public_sector}/` | Keep EE vertical data and generators (`domains/shared/generators/__init__.py:11-14`); move runtime-owned generator behavior to Runtime `tasks/values`. |
| `errors/` | `errors/` | Common stable codes/types/factories/formatters share paths; retain EE-only entries here. CE already has `errors/{base.py,codes.py,factory.py,formatters.py}`. |
| `cli/` | `interfaces/cli/` | Keep the installed command entry point (`cli/app.py:14-16`); do not preserve old Python import paths with wrappers. |
| `scripting/` | `engine/runtime/scripting/` | Runtime expression surface (`scripting/__init__.py:3`). |
| `utils/` | Split by actual owner | Move each utility to DSL, IO, Runtime, Domains, or Errors; do not create `engine/utils`. |
| `config.py`, `error_handling.py` | `engine/runtime/lifecycle/config.py`, Runtime policy owner | EE settings remain EE-only (`config.py:13-53`); per-run `platform_json` belongs to Runtime contracts. CE need not acquire an EE settings twin. |
| Rust crate (`src/`) and `native.py` | EE-only Runtime implementation | Native facade imports the EE extension (`native.py:7-9`); Rust stays exclusive to EE. Do not add a CE package, switch, or placeholder for it. |

## Boundaries

Shared Authoring target: `domain/acceptance.py` and `domain/verification.py`
own verdict policy; `contracts.py` owns bounded-capture records; Application
owns execution sequencing. EE currently uses `projection/acceptance.py` and
Domain request/evidence types. Its later physical migration must keep its
algorithms and stronger tests; this CE move does not claim EE conformance.

Keep the existing operations and typed values as the public seams; moves must
not add a facade feature or synchronization framework.

| Boundary | Stable operations and types | Evidence |
|---|---|---|
| Authoring | Typed request/result use cases. CE exposes `check`, `reference`, bounded `run`, `scaffold`; EE has its own build/roundtrip contract, not identical methods | CE `authoring/api.py`; EE `authoring/application/app.py` |
| DSL | Parse/model operations and DSL-owned statements; neutral generator metadata belongs to Domains, serialization contract to IO | Historical CE `engine/dsl/api.py`, `engine/dsl/contracts.py`; Astra decisions D06/D18 |
| IO | Target: source loading and exporter registration through typed IO contracts, no concrete clients/exporters as Runtime's boundary. Current CE facade still leaks exporter classes | CE `engine/io/api.py` versus target.md boundary table |
| Runtime | `run`, `create_run_session`; `RunRequest`, `RunResult`, `RunSession` | CE `engine/runtime/api.py:34-49`; `engine/runtime/contracts.py:50-70` |
| Errors | Stable issue code, public error type, factory, formatter; local validation policy stays with its owner | CE `errors/`; EE `errors/` |
| Interfaces | CLI/MCP adapt typed calls and present results; Runtime and Authoring own behavior | Shared target: Lifecycle and boundaries |

## Superseded experiment proposal

The EE experiment-3 proposal is explicitly unfrozen and says no production
module moved (`target-proposal.md:1-4`; `protocol.md:3`). Its proposed root
`cli/`, `scripting/`, `config.py`, `native.py`, explicit import-compatibility
paths, and “not an exact CE mirror” (`target-proposal.md:20-46, 57-59`) are
superseded by this shared physical target and Alex's no-shim requirement.
Preserve the executable CLI command through its entry point, not the old module
path. Do not retain `constants.runtime.api` as a compatibility wrapper.

## Authoring contract remains a product decision

CE `AuthoringSpecV1` defines the contents of `model.dm.json`
(`datamimic_ce/authoring/spec.py:955-961`). Its scaffold CLI reads a supplied
file or stdin and returns the compiled/verified result; it does not write the
input file (`datamimic_ce/interfaces/cli/authoring.py:119-157`). The user or
project owns retaining that editable intent artifact. EE's `DmJsonDocumentV1`
is an agent wire representation and XML is the persisted executable descriptor
(`docs/architecture/authoring-4.0-contract.md:5-16`). These are different
contracts today. Package alignment must not silently select a migration or
replace one format with the other.

## Acceptance evidence

Keep the two evidence tracks separate:

Before each shared-behavior change, compare against the frozen EE implementation.
Preserving CE results alone does not prove EE-led semantics. Generate policies sit
directly in `tasks/generate/policies/`; split EE's existing Generate `services/`
by responsibility instead of carrying that catch-all wrapper into the common tree.

- **CE:** freeze and rerun the full CE descriptor oracle across the migration,
  then run unit, API, factory, functional, integration, architecture, lint and
  full-package type gates. A passing structural contract is not descriptor
  behavior proof (target.md acceptance; experiment-2 protocol).
- **EE:** preserve its existing unit, contract, integration, external-service,
  Rust, lint, type, build and remote-CI gates. Run the complete descriptor
  corpus at baseline, boundary milestones and final acceptance; subsets do not
  substitute (`experiment-3/protocol.md:71-98`).
- **Cross-edition:** every executable CE descriptor is an EE candidate; record
  unsupported EE-to-CE paths with capability and descriptor evidence. Check
  seeded replay within each edition under identical initial target state, not
  equality of CE and EE random values (`experiment-3/protocol.md:71-81`).
