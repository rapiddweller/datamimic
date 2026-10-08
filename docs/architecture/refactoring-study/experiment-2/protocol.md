# Experiment 2 protocol

Written before implementation. Contract edits after freeze require a dated amendment explaining
why the original target was wrong; an implementation difficulty is not a reason to weaken it.

Current recursive target: [Amendment 19](amendment-19.md), corrected through the
semantic freeze in [Amendment 20](amendment-20.md). Astra decides remaining
ownership questions; Luna implements and Terra verifies independently. Frozen
inputs below remain history, including the original checker and agent versions.

[Amendment 80](amendment-80.md) corrects Authoring policy ownership: acceptance
and verification live in Domain; canonical contracts own the existing capture
records. Application still sequences execution and adapters still run it.

[Amendment 92](amendment-92.md) incorporates upstream's empty-Echo diagnostic
correction; this intended error-to-continuation change is not output parity.

[Amendment 93](amendment-93.md) retains seven exact setup-state annotation
disclosures as a red checkpoint. It does not waive the newly measured debt
or change any gate, baseline or final acceptance requirement.

[Amendment 94](amendment-94.md) assigns the inert Domain namespace marker to
its existing API owner without widening package selectors or public surfaces.

[Amendment 95](amendment-95.md) recognizes exact native Python scripting-state
and deepcopy-memo positions. This is a target correction, not source-debt
reduction; unrelated type findings and UNKNOWNs remain subject to the gates.

[Amendment 96](amendment-96.md) assigns the inert Runtime and IO namespace
markers to their existing API owners. Child ownership and permissions stay fixed.

[Amendment 97](amendment-97.md) assigns four reviewed initializers to existing
model, service and shared-interface owners, preserving all permissions. The
Errors assignment stops at a reproduced checker false-unused diagnosis.

The Step 31 Domains boundary correction is recorded in [Amendment 64](amendment-64.md):
the six inherited service result models are declared at the root Domains boundary and under
their owning nested components, without adding package convenience exports or suppressing
registry findings.

The Step 32 Finance boundary correction is recorded in [Amendment 65](amendment-65.md):
the `Bank` and `BankAccountGenerator` types exposed by `BankAccount` are declared at the
root Domains boundary and under `DOMAINS-FINANCE`, with no convenience exports.

The IO facade contraction is recorded in [Amendment 71](amendment-71.md): five
implementation names remain at their owners but leave the parent-facing API.
[Amendment 72](amendment-72.md) adds the two nested-value smoke-export
allowances without changing the request's container types.
[Amendment 77](amendment-77.md) records three exact open-property-map return
allowances; other dictionary boundary positions remain disallowed.
[Amendment 73](amendment-73.md) declares two existing demographic record types
at the parent Domains boundary; typed-map findings remain open.
[Amendment 74](amendment-74.md) declares two existing types already exposed by
DSL and Runtime signatures at their owning root boundaries.

[Step 94](step-94-finance-record-types.md) types the existing Bank and credit-card
finance records without changing their dictionary or descriptor behavior. ArchKeel 1.0.0
validation remains pending.

[Amendment 90](amendment-90-bank-generator-ownership.md) corrects the Finance
responsibility descriptions to match the existing target: BankGenerator owns
BIC, BIN, and customer-service phone generation; Bank retains cached access.

[Amendment 91](amendment-91-credit-card-generator-ownership.md) moves card-number
and security-code generation, plus the existing Luhn dependency, from Finance
models to generators while preserving cached model access and CE behavior.

[Amendment 92](amendment-92-hospital-capacity-ownership.md) moves hospital bed
and staff count calculations into `HospitalGenerator`; `Hospital` retains its
lazy cached properties and existing CE behavior.

[Amendment 93](amendment-93-medical-device-identifiers.md) clarifies that
`MedicalDeviceGenerator` owns model-number and serial-number generation while
the model retains cached field access.

[Amendment 94](amendment-94-runtime-factory-lookup.md) publishes the existing
pre-run named-Generate search from `engine.dsl.statements.traversal`; Runtime
delegates to it without changing factory lookup, error, or mutation behavior.

[Amendment 95](amendment-95-credit-card-value-ownership.md) moves credit-card
status and amount draws into `CreditCardGenerator`; cached model access, RNG
order, and the existing balance range remain unchanged. EE still owns these
draws on `CreditCard`; track that alignment separately and do not copy its
field-keyed RNG policy into CE.

[Amendment 96](amendment-96-transaction-internationality.md) moves the lazy
weighted `is_international` draw to `TransactionGenerator`, preserving its
shared RNG and model-level cache.

[Amendment 97](amendment-97-bank-account-balance-ownership.md) moves the lazy
account-balance draw to `BankAccountGenerator`; the model cache and setter
semantics remain unchanged.

[Amendment 98](amendment-98-medical-procedure-duration-ownership.md) moves the
duration draw to `MedicalProcedureGenerator`, preserving the cached surgical
flag, duration cache, and cost evaluation order.

[Amendment 99](amendment-99-medical-procedure-cost-ownership.md) keeps the
coupled cached procedure-cost calculation model-owned; eager arguments or
fragmented generator helpers would disturb its lazy-property/RNG order without
clarifying ownership.

[Amendment 100](amendment-100-doctor-acceptance-ownership.md) moves the lazy
new-patient acceptance draw to `DoctorGenerator`, preserving its public RNG
override, one-draw cache behavior, and strict threshold.

[Amendment 101](amendment-101-hospital-founding-year-ownership.md) moves the
lazy founding-year draw to `HospitalGenerator`, preserving reference-clock then
public-RNG access order, the inclusive bounds, and the model cache.

[Amendment 102](amendment-102-medical-procedure-surgical-status.md) moves the
lazy surgical-status draw to `MedicalProcedureGenerator`, preserving the public
RNG override, strict threshold, one-draw cache behavior, and seeded ordering.

[Amendment 103](amendment-103-medical-procedure-anesthesia-ownership.md) moves
the conditional anesthesia draw to `MedicalProcedureGenerator`, preserving
evaluation of the cached surgical flag before its public-RNG draw.

[Amendment 104](amendment-104-medical-procedure-preventive-status.md) moves
the conditional preventive-status draw to `MedicalProcedureGenerator`, keeping
the cached surgical-flag and description-first evaluation order.

[Amendment 105](amendment-105-medical-procedure-diagnostic-status.md) moves the
conditional diagnostic-status draw to `MedicalProcedureGenerator`, preserving
the cached surgical flag and name/description argument evaluation order.

[Amendment 106](amendment-106-hospital-emergency-services-ownership.md) moves
the lazy emergency-status draw to `HospitalGenerator`, preserving type-before-
RNG evaluation, thresholds, and the per-model cache.

[Amendment 107](amendment-107-hospital-teaching-status-ownership.md) moves
teaching-status decisions to `HospitalGenerator`, preserving the no-RNG
`Teaching` case, conditional public-RNG draws, and the per-model cache.

[Amendment 108](amendment-108-medical-procedure-code-ownership.md) moves the
cached procedure-code generation to `MedicalProcedureGenerator`, preserving
five ordered public-RNG draws and leading-zero formatting.

[Amendment 109](amendment-109-medical-procedure-cpt-code-ownership.md) moves
cached CPT-code generation to `MedicalProcedureGenerator`, preserving its
non-zero first digit and four ordered trailing digit draws.

[Amendment 110](amendment-110-doctor-npi-ownership.md) moves cached NPI
generation to `DoctorGenerator`, preserving ten ordered shared-RNG digit draws
and leading zeroes.

[Amendment 111](amendment-111-doctor-license-ownership.md) moves cached
license-number generation to `DoctorGenerator`, preserving the two-letter,
six-digit draw order and formatting.

[Amendment 112](amendment-112-medical-device-id-candidate.md) moves device-ID
candidate sampling and formatting to `MedicalDeviceGenerator`; `BaseEntity`
continues to own optional unique allocation, and the model caches the claimed
result.

[Amendment 113](amendment-113-hospital-id-candidate.md) moves hospital-ID
candidate sampling and formatting to `HospitalGenerator`; `BaseEntity` retains
unique allocation, while the model's lazy website fallback still reads the
claimed, cached ID.

[Amendment 114](amendment-114-patient-medical-record-number.md) assigns MRN
sampling and formatting to `PatientGenerator`; `Patient` retains lazy access
and caching, with no uniqueness or allocation behavior.

[Amendment 115](amendment-115-patient-ssn-ownership.md) assigns SSN sampling
and formatting to `PatientGenerator`, matching the EE method boundary while
preserving CE's existing shared-RNG sequence and model cache.

[Amendment 116](amendment-116-doctor-id-candidate.md) assigns doctor-ID
candidate sampling and formatting to `DoctorGenerator`; `BaseEntity` retains
optional unique allocation and the model retains cached access.

[Amendment 117](amendment-117-patient-height-ownership.md) assigns conditional
height calculation and sampling to `PatientGenerator`; `Patient` still resolves
demographics first and retains the lazy cache.

[Amendment 118](amendment-118-patient-weight-ownership.md) assigns BMI sampling
and weight calculation from supplied age and height to `PatientGenerator`;
`Patient` still resolves and caches those inputs and retains the lazy weight and
BMI properties.

[Amendment 119](amendment-119-patient-insurance-policy-number.md) assigns
insurance-policy-number sampling and formatting to `PatientGenerator`; `Patient`
retains its lazy cache and duplicate candidates remain allowed.

[Amendment 120](amendment-120-patient-id-candidate-ownership.md) assigns
patient-ID candidate sampling and formatting to `PatientGenerator`; `Patient`
retains lazy access and `BaseEntity` retains optional unique allocation.

[Amendment 121](amendment-121-medical-procedure-id-candidate.md) assigns
procedure-ID candidate sampling and formatting to `MedicalProcedureGenerator`;
`MedicalProcedure` retains lazy access and `BaseEntity` retains optional unique
allocation.

[Amendment 122](amendment-122-doctor-office-hours-ownership.md) assigns
office-hour sampling and formatting to `DoctorGenerator`; `Doctor` retains its
lazy cached property and output behavior.

[Amendment 123](amendment-123-transaction-id-candidate.md) assigns transaction
ID candidate generation to `TransactionGenerator`; `Transaction` keeps its
lazy cache and unique-ID claim, with regex, RNG sequence and serialized output
unchanged.

[Amendment 124](amendment-124-address-house-number-ownership.md) assigns
house-number sampling and formatting to `AddressGenerator`; `Address` keeps its
lazy cache and serialization, with country resolution and RNG order unchanged.

[Amendment 125](amendment-125-police-badge-number-ownership.md) assigns badge
number sampling and formatting to `PoliceOfficerGenerator`; the model retains
the cached property, leading zeroes, duplicate allowance, and RNG order.

[Amendment 126](amendment-126-insurance-company-id-candidate.md) assigns UUID
candidate creation to `InsuranceCompanyGenerator`; `InsuranceCompany` retains
its lazy property and `BaseEntity` retains unique-ID allocation.

[Amendment 127](amendment-127-insurance-product-id-candidate.md) assigns UUID
candidate creation to `InsuranceProductGenerator`; `InsuranceProduct` retains
its lazy property and `BaseEntity` retains unique-ID allocation.

[Amendment 128](amendment-128-police-officer-id-candidate.md) assigns officer-ID
candidate sampling and formatting to `PoliceOfficerGenerator`; `PoliceOfficer`
retains its lazy property and `BaseEntity` retains unique-ID allocation.

[Amendment 129](amendment-129-insurance-policy-id-candidate.md) assigns UUID
candidate creation to `InsurancePolicyGenerator`; `InsurancePolicy` retains its
lazy property and `BaseEntity` retains unique-ID allocation.

[Amendment 130](amendment-130-insurance-policy-coverage-count.md) assigns the
coverage-count draw to `InsurancePolicyGenerator`; `InsurancePolicy` retains
lazy coverage construction, caching, and child creation order.

[Amendment 131](amendment-131-product-sku-generation.md) assigns SKU formatting
and digit generation to `ProductGenerator`; `Product` retains its cached
property and brand-before-category evaluation order.

[Amendment 132](amendment-132-educational-institution-student-count.md) assigns
student-count selection to `EducationalInstitutionGenerator`; the model resolves
type before level and retains the lazy cache.

[Amendment 133](amendment-133-administration-office-hours-ownership.md) assigns
operating-hours generation and its cross-office anti-repeat state to
`AdministrationOfficeGenerator`; the model retains the cached property.

[Amendment 134](amendment-134-product-name-ownership.md) assigns product-name
data selection, formatting, and pattern choice to `ProductGenerator`; the model
resolves category before brand and retains the cached property.

[Amendment 135](amendment-135-product-description-ownership.md) assigns
description composition to `ProductGenerator`; `Product` resolves name before
category and retains its lazy cached property.

[Amendment 136](amendment-136-order-tax-ownership.md) assigns tax-rate sampling
and amount rounding to `OrderGenerator`; `Order` retains product-price summing
and the lazy cached property.

[Amendment 137](amendment-137-order-coupon-code-ownership.md) assigns the full
prefix-selection, random-code, and formatting sequence to
`OrderGenerator`; `Order` retains only the discount gate and lazy cached `None`.

[Amendment 138](amendment-138-order-product-count-ownership.md) assigns the
1–10 product-count draw to `OrderGenerator`; `Order` retains child construction,
ordering, the lazy cached list, and its setter.

[Amendment 139](amendment-139-product-id-candidate-ownership.md) assigns
product ID candidate generation to `ProductGenerator`; `Product` retains
identifier claiming and the lazy cached property.

[Amendment 140](amendment-140-administration-office-budget-ownership.md)
assigns budget sampling and calculation to `AdministrationOfficeGenerator`;
the model retains type/staff resolution order and its lazy cached property.

[Amendment 141](amendment-141-educational-institution-staff-count-ownership.md)
assigns staff-count sampling and calculation to
`EducationalInstitutionGenerator`; the model resolves student count first and
retains the lazy cached property.

[Amendment 142](amendment-142-educational-institution-name-ownership.md)
assigns institution-name candidate construction and choice to
`EducationalInstitutionGenerator`; the model resolves city, state, type, and
level in order and retains the lazy cached property.

[Amendment 143](amendment-143-administration-office-jurisdiction-ownership.md)
assigns jurisdiction mapping and fallback formatting to
`AdministrationOfficeGenerator`; the model resolves type, city, and state in
order and retains the lazy cached property.

[Amendment 144](amendment-144-person-gender-ownership.md) assigns demographic
sex normalization and fallback selection to `PersonGenerator`; `Person`
reuses its already-reserved sample and retains the lazy cached property.

[Amendment 145](amendment-145-educational-institution-program-category.md)
assigns the exact level-to-program-category mapping to
`EducationalInstitutionGenerator`; the model resolves level first, forwards its
existing file anchor, and retains the lazy cached property. Preserve the current
case-sensitive precedence, including `Higher Education` mapping to
`high_school` because the `High` check comes first.

[Amendment 146](amendment-146-administration-office-id-candidate.md) assigns
office-ID candidate formatting and its eight RNG draws to
`AdministrationOfficeGenerator`; `AdministrationOffice` retains the uniqueness
claim, evaluation order, and lazy cached property.

[Amendment 147](amendment-147-educational-institution-id-candidate.md) assigns
institution-ID candidate formatting and its eight RNG draws to
`EducationalInstitutionGenerator`; `EducationalInstitution` retains the
uniqueness claim, evaluation order, constructor child-RNG setup, and lazy cached
property.

[Amendment 148](amendment-148-order-billing-address-reuse.md) assigns the strict
80-percent shipping-address reuse decision to `OrderGenerator`; `Order` retains
lazy address construction, relationship identity, and the cached billing field.

[Amendment 149](amendment-149-order-ids.md) assigns order-ID candidate and user-ID
generation to `OrderGenerator`; `Order` retains the order-ID claim and both lazy
caches. User IDs remain unclaimed, including when an identifier registry is bound.

Step 150 moves age-sampled versus configured birthdate selection into
`PersonGenerator`, which already owns birthdate generation in the target contract.
This aligns implementation with the existing target; it does not change that target.

[Amendment 151](amendment-151-administration-office-founding-year.md) assigns
founding-year range selection and sampling to `AdministrationOfficeGenerator`.
`AdministrationOffice` keeps public clock/type resolution order and its lazy cache;
the existing `pick_founding_year()` entry point remains unchanged.

[Amendment 152](amendment-152-company-url-scheme.md) assigns only URL-scheme
sampling to `CompanyGenerator`. `Company` still samples before resolving its
cached email, then composes and caches the URL.

[Amendment 153](amendment-153-office-email-department.md) assigns the ordered
email-department mapping to `AdministrationOfficeGenerator`. `AdministrationOffice`
keeps website/domain handling, type normalization order, composition, and cache.

2026-09-29: The proposed Step 58 `tasks/values/generators/` split was rejected
as unnecessary. D05's `tasks/values/construction/` placement remains the target;
the living map and contracts were reconciled to that decision. This is not a
target amendment. Sequence-table Optional-input guards are reviewed separately.

## Fixed inputs

| Input | Frozen value |
|---|---|
| Code | `development` at `a219163e533d661bcc7bda0faa5ecc77909ab5aa` |
| Worktree | `/private/tmp/datamimic-architecture-experiment-2` |
| Branch | `experiment/target-architecture-v2` |
| Architecture checker | ArchKeel `0.6.0`, local tag `d14035b31ef2addac9cfea738a70d8643df2f7ae` |
| Implementation agent | Luna, contract and baseline read-only |
| Verification agent | Luna, production code and contract read-only |
| Remote changes | none |

## Acceptance contract

1. `archkeel validate --baseline known-violations.json` never accepts new debt.
2. Final `archkeel validate --baseline known-violations.json --json` passes with an empty
   violation list, no new or resolved findings, complete coverage, zero violations, and zero
   material unknown positions. Numeric budgets may be positive but never increase (Amendment 12).
3. The exact root layout and component namespaces match `target-architecture.md`.
4. Every component crossing uses its declared API and every API has checked boundary types.
5. All existing XML descriptors still parse. Seeded descriptors produce byte-identical captured
   output, except for proven domain-ID collision resolution (Amendment 15).
   Unseeded descriptors retain outcome, product counts, row counts, and value shapes.
   Amendment 13 replaces cross-run equality only for genuinely dynamic unseeded counts with
   descriptor-defined ranges and same-run relationships; unknown shape remains unverified.
   Amendment 50 requires field-presence evidence and rejects unknown or all-null shapes as proof.
   Amendment 51 requires structural evidence for every unseeded export file; an
   unsupported format cannot pass merely because its filename is unchanged.
   Target-state reproducibility requires the same initial target state;
   Amendment 16 separates generated-ID uniqueness from target constraints.
6. Authoring schema, reference, capability, compiler, lint, and transport projections remain
   identical unless an explicitly approved product change is recorded. Amendment 60 records
   the narrow capability wording and package-version exception.
7. Existing public CLI commands and documented Python entry points remain importable.
8. Unit, API, factory, functional, integration, architecture, lint, and full-package mypy gates
   pass. External-service tests run serially against already-running local services.
9. The final report independently explores `Actual`, `Target`, and `Diff`. `Actual` comes from
   observed source; `Target` comes only from declared contracts and target layout, never from
   filtering observed edges; `Diff` compares the two. Each view remains explorable to deliberate
   atomic leaves. A selected target component or module shows its responsibility sentence;
   a searchable index exposes all sentences without opening every node.

The controlled Postgres/Mongo subset is recorded in [Step 33](step-33-service-parity.md);
it does not close the full descriptor gate in item 5.
The domain-schema correction in [Step 34](step-34-transaction-account-schema.md)
changes no runtime output or authoring projection.

Items 3–4 require both physical and semantic completion. Layout scopes establish permitted tree
shape only. An atomic semantic leaf is a declared target node for an independently meaningful
policy, behavior, API, or cross-component boundary—not every filesystem directory. Its decision
must be explicit in the containing machine-checked architecture contract, stating ownership,
allowed dependency set, and public decision: a named API or deliberate `public: []`; an empty
allowed-dependency set is valid. Grouping-only folders inherit their nearest parent's contract; do
not create a contract per directory. Aggregate component cards do not stand in for independently
meaningful children.

Report four verdicts separately: structure reached (items 1–4 and 7), behavior preserved
(items 5–6 and the relevant runtime tests), report explorability (item 9), and delivery ready
(item 8, integrated checker, and remote CI). A structural pass does not imply the other three.
The literal baseline-free command in the frozen protocol is inapplicable while measurement budgets
are declared; Amendment 12 records the reason.

## Per-step gate

1. smallest coherent architecture slice;
2. targeted test;
3. descriptor and projection comparison for affected paths;
4. ArchKeel baseline decreases and never grows;
5. relevant broader suites, then `make lint` and `make typecheck`;
6. diff review, experiment log, one local commit.

The serial result is authoritative when xdist and serial execution disagree. No flaky descriptor is
excluded from equivalence until repeated unchanged Step-0 runs demonstrate the instability and the
evidence is logged.

[The 2026-09-29 measurement amendment](amendment-2026-09-29-typed-cache-measurement.md)
records one exact UNKNOWN-to-violation transition in Step 38. It permits retaining
the correct annotation, not counting that step as gate-green or growing the
accepted baseline. The final zero-violation and zero-unknown targets are unchanged.

[Amendment 98](amendment-98.md) permits the bounded Step 106 native-properties
annotation disclosure as a red checkpoint. No runtime statement, contract,
baseline, descriptor or oracle changes. It does not waive its remaining map/object
findings, inherited-surface UNKNOWNs or strict descriptor-comparison failures.

[Amendment 99](amendment-99.md) permits the bounded Step 107 native-capture
checkpoint and its dictionary-only factory overlay decision. It retains the
new boundary finding and strict oracle FAIL; no contract, baseline, allowance,
descriptor or gate is relaxed. See [Step 107 evidence](step-107-capture.md).
[Amendment 78](amendment-78.md) permits only the separately reviewed weighted
CSV return UNKNOWN-to-violation transition in Step 72. It does not reuse the
Step 38 exception or accept boundary debt; Step 72 remains gate-red.

[Amendment 154](amendment-154-lazy-model-computation-ownership.md) clarifies
that cached model computations remain model-owned only when extraction would
change observable lazy reads or RNG order; generators own independent rules over
resolved inputs. Step 154 records the distinct Order, EducationalInstitution,
MedicalDevice, and existing MedicalProcedure cases and preserves getter/access
and RNG order.

[Amendment 155](amendment-155-execute-task-sql-capability.md) preserves SQL
client injection through the narrow `SqlScriptClient` Protocol without a
concrete-class restriction or a pre-invocation capability probe. Runtime keeps
target selection; IO performs one direct method call and propagates native errors.

[Amendment 156](amendment-156-package-initializer-ownership.md) assigns reviewed
package-root initializers to existing inner components with exact module selectors.
It does not broaden package ownership, add components, or waive import checks.

[Amendment 157](amendment-157-runtime-initializer-ownership.md) assigns the inert
`engine.runtime` package initializer to `RUNTIME-API` with an exact module selector;
the API package selector and dependency rules remain unchanged.

[Amendment 158](amendment-158-io-initializer-ownership.md) assigns the inert
`engine.io` package initializer to `IO-API` with an exact module selector; the
API package selector and dependency rules remain unchanged.

[Amendment 159](amendment-159-exporter-initializer-ownership.md) assigns the inert
`engine.io.exporters` package initializer to `EXPORTERS-REGISTRY` with an exact
module selector; registry's package selector and dependency rules remain unchanged.

[Amendment 160](amendment-160-errors-package-facade-ownership.md) assigns the
existing package-level error re-exports to `ERRORS-FACTORY` while preserving the
defining owners of error types and codes and all public grants.

When the first real function is added to an API module, the same commit adds that module's
`boundary_types` rule. The rule then remains mandatory. This is a narrowing, not permission to
change the target.

[Amendment 161](amendment-161-client-lookup-boundary.md) declares the exact
client lookup Protocol at the root IO boundary. Existing registry arguments,
Runtime calls and routing behavior remain unchanged; no allowance is added.

[Amendment 162](amendment-162-client-names-boundary.md) declares the exact
client names Protocol at the root IO boundary. Exporter dispatch and diagnostics
remain unchanged; no allowance is added.

[Amendment 163](amendment-163-factory-error-log-ownership.md) gives the execution
boundary one ERROR record for a missing factory entity. Validation retains its
native exception without a redundant log; no other error or gate changes.

[Amendment 164](amendment-164-authoring-scope-hint.md) corrects the public Authoring
scope hint under a dated projection decision. Native resolution and error messages
remain unchanged; no oracle or architecture allowance changes.

[Step 130](step-130-original-determinism.md) records original/current owner tests
and eleven three-way seeded digest equalities. Five unseeded strict gaps and
full931 acceptance remain open; no target or oracle changes.

[Amendment 165](amendment-165-transaction-profile-catalog.md) permits the two
transaction-profile catalog and reference corrections and matching model-doc
rows. Runtime Mapping identity and native serialization behavior remain unchanged;
[Step 132](step-132-transaction-profile-catalog.md) records bounded local verification.
Full DSL and architecture acceptance remain open.

[Amendment 166](amendment-166-native-scope-guidance.md) permits only the native
scope-guidance suffix and three ordinary message expectations. Local verification
and independent candidate review are recorded there. All 19
historical message rows and unchanged comparator outcomes remain visible; full
acceptance and Step 131's separate native profile stay unchanged.

[Amendment 167](amendment-167-mongo-connection-values.md) names and publishes the
existing fixed Mongo configuration result. It preserves the native dictionary
and separate client kwargs path; architecture permissions and open RDBMS payloads
remain unchanged. Candidate verification is recorded in the amendment.

[Amendment 168](amendment-168-memstore-data-owner.md) moves Memstore's raw storage
and injected-client reconciliation to a distinct IO owner and its nominal marker
to IO contracts. Preserve method/state/error behavior and the existing context
copy split. No old-path shims; new module/serialization paths are disclosed.
Step 141: nine-case and 122-case unit cohorts and six native cases (including
SQLite) passed before/after. Integrated 38 physical/API/registry, 12 definition
and four inner-target cases, Ruff, MyPy and pinned Pylint cycles passed.
Global declared rules remain FAIL (89 violations, 200 unknown positions); the
58 new baseline entries also occur at the original checkpoint. Machine amendment
binding is OPEN: the writer produced no JSON. Astra reviewed and accepted the ten
unamended classifications for this red checkpoint. The amendment records the
exact command and remaining limits.
Worker/historical compatibility, full DSL/EE acceptance and final-head CI remain
open; no merge or baseline promotion.

## Agent separation

- The implementation agent changes production code and targeted tests for one approved slice.
- The verification agent builds the Step-0 oracle, runs gates, and reports regressions. It does not
  repair production code.
- The orchestrator owns the contract, baseline, slice selection, acceptance, and commits.

## Success and stop conditions

Structural success means the declared target is reached, not merely that debt decreased.
Behavioral and delivery verdicts remain separate. Stop and report instead of weakening the
target when behavior cannot be proven, ArchKeel returns UNKNOWN for a required fact, or
compatibility requires a product decision.

## Known checker limit under test

ArchKeel 0.6.0 can require target namespaces only after they exist as scanned packages. The freeze
therefore adds empty target package markers before Step 0. It also returns `UNKNOWN` for
`boundary_types` until a real facade function exists; those rules are activated with the first
real function instead of adding dummy code. Both constraints are recorded as checker limits, not
accepted architecture debt.

Layout violations on an empty legacy `__init__.py` also lack the non-empty excerpt ArchKeel later
requires for its own trace. The freeze adds ownership-only docstrings to the affected files so the
same violations become traceable and baselineable.

Target progress may remove a legacy package from a component's ownership list or promote a built
API from `planned` to `public`; these are synchronized contract facts, not target changes. A target
permission or restriction changes only through an amendment.
