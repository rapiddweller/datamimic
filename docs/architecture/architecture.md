# datamimic_ce architecture

Seven product components and their allowed directions. [`architecture-contract.json`](../../architecture-contract.json)
is the **target** architecture (SPOT), not a description of today's code. `archkeel report`
measures the code against it and is red where the code still contradicts it. Success means:
the target stays stable and the known violations only decrease.

`pytest tests_ce/architecture` (in `make check` and CI) freezes the known violations in
`tests_ce/architecture/architecture_debt_budget.json`. Any new violation fails: a new edge
between components, an import of a non-public name across components, or a third-party
library outside its declared owners. A resolved violation must be dropped from the budget.

## Lifecycle of a run

```mermaid
flowchart LR
    I["interfaces<br/>CLI · MCP · Python API<br/>factory = composition root"] --> P["dsl<br/>parse XML → models → statements"]
    I --> A["authoring<br/>model.dm.json → XML"]
    A --> P
    P --> S["engine<br/>setup context → generate tasks"]
    S --> W["engine<br/>workers, page by page"]
    W --> R["io<br/>read sources"]
    W --> D["domain<br/>generate · convert"]
    W --> X["io<br/>export targets"]
```

## Components

| Component | Responsibility | Must not | Packages |
|---|---|---|---|
| `interfaces` | CLI, MCP server and Python API (datamimic, data_mimic_test); factory is the composition root that wires a run | business logic; being imported by other components | `cli`, `cli_authoring`, `cli_presenter`, `cli_runtime`, `mcp`, `datamimic`, `data_mimic_test`, `factory` |
| `authoring` | model.dm.json intent to XML; lint rules and rule catalog; bounded dry-run and acceptance verification | importing interfaces | `authoring` |
| `dsl` | the DSL: XML parsing, element models, statements | execution; knowledge of contexts or connections | `model`, `parsers`, `statements`, `constants`, `enums` |
| `engine` | run lifecycle: setup, tasks, workers; script-expression evaluation | generator logic; database details | `tasks`, `workers`, `contexts`, `services`, `product_storage` |
| `io` | adapters to external systems: sources, exporters, clients, connection configuration | driving the run lifecycle | `data_sources`, `exporters`, `clients`, `connection_config` |
| `domain` | pure data generation and value conversion | workers; contexts; connections; statements | `domains`, `converter` |
| `foundation` | stable, low-semantic types and technical primitives needed by at least two components; determinism SPOTs: rng, clock, RunSeed; logger and process settings | importing any other component; knowledge of DSL, engine, domain or IO | `utils`, `logger`, `config`, `_compat` |
| `demos` | bundled examples that use the product; not part of the product architecture | being imported by product components | `demos` |

`foundation` holds only stable, low-semantic types and technical primitives that at least two
components need, and knows nothing about DSL, engine, domain or IO. This describes the target;
today's contents are not yet that pure (see Debt). `demos` uses the product and
is not part of the product architecture.

## Dependencies

Target direction: `interfaces → authoring → dsl`, `authoring → engine`, `interfaces → engine`,
`engine → dsl / domain / io`, everyone → `foundation`. The graph below is the **observed** state,
including the debt edges the target forbids.

<!-- archkeel-component-graph -->
```mermaid
graph TD
    authoring --> domain
    authoring --> dsl
    authoring --> engine
    authoring --> foundation
    authoring --> interfaces
    authoring --> io
    demos --> domain
    demos --> engine
    demos --> foundation
    demos --> io
    domain --> dsl
    domain --> engine
    domain --> foundation
    domain --> io
    dsl --> domain
    dsl --> engine
    dsl --> foundation
    dsl --> io
    engine --> domain
    engine --> dsl
    engine --> foundation
    engine --> io
    foundation --> domain
    foundation --> dsl
    foundation --> engine
    interfaces --> authoring
    interfaces --> dsl
    interfaces --> engine
    interfaces --> foundation
    interfaces --> io
    io --> domain
    io --> dsl
    io --> engine
    io --> foundation
```

### Under review

- `io → dsl`: existing coupling; adapters should not need to know the DSL, the engine should translate DSL configuration for them. Level 2 decides.

### Debt

Observed edges the target forbids. They are not in the contract; their imports are frozen in the
debt budget. Each is removed by moving code, never by widening the contract or the budget.

| Edge | Cause and target |
|---|---|
| `authoring → interfaces` | authoring.dryrun starts a run through the DataMimic interface; target: call the engine directly. |
| `domain → dsl` | generator_util resolves generators per statement and literal generators read DSL enums; target: generator_util moves to engine, shared enums move to their owner or foundation one by one. |
| `domain → engine` | generator_util reads contexts; target: generator_util moves to engine. |
| `domain → io` | DataSourcePagination and SequenceTableGenerator's database access; target: decide per type (value type or io semantics). |
| `dsl → domain` | state_machine_statement builds a generator; target: the engine builds it. |
| `dsl → engine` | statements import contexts; target: the DSL does not know execution. |
| `dsl → io` | statements import MongoDB client and connection configs; target: the DSL does not know connections. |
| `foundation → domain` | utils.object_util references converters; target: move to engine. |
| `foundation → dsl` | utils read DSL constants and enums; target: foundation imports nothing. |
| `foundation → engine` | utils.object_util builds converters with contexts; target: move to engine. |
| `io → domain` | clients serialize with domain base_entity; target: a foundation helper. |
| `io → engine` | DataSourceRegistry evaluates source scripts with contexts; target: an engine-provided port. |

Debt cannot grow: the budget holds each known violation by rule, source module and imported
symbol, so an unrelated edit does not move it and a new import over a debt edge fails.

## Cross-component surface

A component's `public` list in the contract is the **currently permitted cross-component surface,
not its intended long-term public API**: it froze the names other components used when the
contract was introduced. A new import of any other name fails. Listing a name there does not make
it a supported API or a reason not to change it; the lists shrink toward small facades.

| Component | Permitted surface today (names) | Target facade |
|---|---:|---|
| `interfaces` | 1 | to be defined, intentionally small |
| `authoring` | 18 | to be defined, intentionally small |
| `dsl` | 128 | to be defined, intentionally small |
| `engine` | 7 | to be defined, intentionally small |
| `io` | 21 | to be defined, intentionally small |
| `domain` | 39 | to be defined, intentionally small |
| `foundation` | 30 | to be defined, intentionally small |
