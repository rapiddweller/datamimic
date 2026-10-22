# Project acceptance architecture review (ADR #356 slice c)

**Accepted within the local architecture review scope.** Reviewer: Astra (independent Opus 5.5 review agent, delegated by Alex).

- Scope: `feat/project-acceptance-c`, base `c2ff96d5` (b2 head, PR #365), head `229a22bd` (`dc0f0ae8`, `79dfda42`, `60df0427`, `229a22bd`).
- This review rebinds the [Build includes receipt](issue-356-build-includes-review.md) and keeps all of its assessments.
- It does not authorize a merge and does not claim that every native rule passes.

## Current binding

| Item | Value |
|---|---|
| Source | `bae2cd577841cfb8e90d10bded66a5345317f95342e36458050eebfd4b6413c7` |
| Target (changed by the contract widening below) | `4ed7e7f238d6b453e0a889013212c7c72ef90c5ec65a10bf0784d3c2baf184c0` |
| Analyzer (unchanged; ArchKeel 4.0.1, Python 3.11.12) | `bb1a3262d3fdd38c3e9a6af980cc063281ae98ab1c28c89c2c5be6dfb450744f` |
| Validation | `41240ba061b86d75ab2a4b08e1905be33fa7b7379a9579d2226ee764e7e83f15` |
| UNKNOWN | `d316c04cdb5a692b2f8d792be070e359ddfb1667b3156a29dbd7b22819d2773c` |

**Budgets:** `calls_unresolved` is ratcheted down from 1,426 to 1,424, a real net −2. `typing_positions` stays at 178. No gate change.

## Design

```
authoring build [PROJECT]
  ProjectFiles.read_project_file (AuthoringWorkspaceContext, contained)   acceptance/build.json -> BuildRequestV5
                                                                  datamimic.xml (fixed entry)
  validate (entry + literal steps) -> decompile -> include_graph (step digests) -> policy -> acceptance
  bounded run(s) -> child records reads:
      audit hook: read-opens of snapshot files      (bounded_executor_child.py:124)
      reader wrapper: contained dir_fd reads         (:164)  incl. conf/<env>.env.properties
    parent hashes recorded paths from the private copy (bounded_executor.py:181)
  union of digests; one path with two hashes -> evidence rejection at ("project", path) (build.py:241)
  ReadyBuild.artifact = sorted unique files (>= 2) + ce_version
```

## Review questions

### 1. Read recording

The recording is sound for what it claims.
- **Hook:** it compares `normcase(realpath(...))` against the snapshot's file set, which is taken after the child writes the entry. Directories are excluded. It records the `relpath` from the real workspace root. On Windows both sides sit on the snapshot's drive, so `relpath` cannot cross drives.
- **Reader wrapper:** it covers the contained reader's `dir_fd` opens, which the open event does not report. Both recorders produce the same workspace-relative POSIX spelling.
- **No snapshot:** when no snapshot is needed, the run reads no workspace file. The manifest then holds what the parent read: `build.json`, the entry, and the steps.
- **`order_desk`:** the manifest lists exactly the 9 files the run depends on, and `README.md` is absent.
- **TOCTOU:** the b1 gap is closed for every recorded file. A step digest read by the parent and the same path hashed from the child's private copy must agree, or the Build is rejected.
- **Not recorded** (as stated in the ADR): native readers outside the audited open and the reader, and directory listings.

### 2. Forged or relative `read_files`

The parent cannot be made to read outside the private copy. I probed `_read_file_digests` directly:
- `../../outside/o.txt`, an absolute host path and `data/../../../outside/o.txt` raise `ValueError` (outside the workspace).
- A directory raises `ValueError`.
- A missing file raises `FileNotFoundError`. The executor's outer `except (OSError, ValueError)` turns both into a serialization failure.
- Only files inside the private copy are hashed. The run cannot modify the snapshot files (#362).
- **Info:** a run could still name a file it created itself. The ADR's accidental-side-effect model covers that.

### 3. Redaction

- Manifest paths are workspace-relative and digests are hex.
- The digest-conflict diagnostic is static, at `("project", path)`.
- `build.json` validation errors use the existing Build projection, as V4 did over stdin.
- No host path or descriptor value appears.

### 4. Over-engineering

None worth cutting.
- The two recorders are both needed.
- `ProjectFiles` follows the existing port-per-adapter pattern of the Authoring application.
- `BuildArtifact` shrank. The removed V4 compile and proof code and the migration script are net deletions.

### 5. ArchKeel widening (`--against c2ff96d5`)

ArchKeel reports exactly five public gains and no other widening:
- authoring: `BuildRequestV5`, `PROJECT_ENTRY_PATH`, `ProjectFileDigest`, `ports:ProjectFiles`;
- the inner ports component: `ProjectFiles`.

`BuildRequestV4` is removed. These gains implement Alex's ADR #356 decision (BuildRequestV5 with a per-file digest). I see no need for a separate decision, but they are listed here and in the receipt for Alex's sight.

### Finding (Low): budget tightening partly by name collision — resolved in `229a22bd`

Of the eight calls removed from `calls_unresolved`, six are not resolutions. They are file-object `.read` calls:
- `dryrun` `stream.read`;
- `TXTExporter` `txtfile.read`;
- two `JsonExporter` `file.read`;
- the workspace `handle.read`;
- the executor `reply.read`.

They became "partially resolved — dynamic receiver with matching internal methods" only because a project method named `read` now exists (`ProjectFiles.read` at `ports.py:44`, `AuthoringWorkspaceContext.read` at `workspace.py:85`).
- Net real change: four removals with the V4 code, two additions.
- The ratchet to 1,418 is therefore brittle. Renaming that method later would put six calls back above the budget.
- **Recommendation:** name the port method distinctively (for example `read_project_file`) and set the budget to the then-measured value.
- The receipt records this truthfully in `dynamic_call_limit` and `measurement_amendment`.

**Resolved in `229a22bd`:** the port method is now `read_project_file`.
- I re-measured against base `c2ff96d5`. None of the six file-object `.read` calls appears in the decoded diff any more, so they are back to their base status, unresolved.
- Unresolved calls: two added (`item.path.as_posix`, `read.add`) and four removed with the V4 code, net −2 to 1,424.
- Partially resolved calls are 2,040 (60df0427: 2,046).
- Nothing else moved. The diagnostics, UNKNOWN identities and contract are unchanged against `60df0427`.
- The re-measurement was taken after the coordinator's brief branch switch, on `feat/project-acceptance-c` at `229a22bd`.
- The budget is 1,424, and the receipt notes are corrected to the honest −2.

## Native result

- **Base:** I re-collected `c2ff96d5` independently, and it reproduces every digest of the previous receipt.
- **Head:**
  - 534/534 files; failures [].
  - 0 violations, 0 baseline additions or resolutions.
  - Rules: 271 PASS and 5 UNKNOWN; the report exits 0.
- **Calls (at `229a22bd`):** 13,338 analyzed; resolved 9,874; partially resolved 2,040; unresolved 1,424.
- **Diagnostics:** still 20. The `CompiledDocumentArtifact` publication diagnostic moves from `/components/1/public/21` to `/22`, because new public entries precede it. Subject, kind and claim are identical, and the receipt carries the new pointer.
- **UNKNOWN records:** 314 → 313.
  - `UNKNOWN-BOUNDARY-TYPE-POSITION-607498d48e034dc8` (the `AuthoringApplication.build` request position) no longer exists, because `build()` takes no argument. It is removed from the `other` group with a note.
  - 17 records have reference churn only.
  - AUTHORING-API-TYPES now decides 13 of 30 positions, and the dynamic-call record reads 1,424.

## Evidence boundary

**LOCAL VERIFIED (by this reviewer):**
- Source review of `c2ff96d5..60df0427` (product code).
- `order_desk` Build: `ready` with the 9-file manifest.
- Forged-path probes of the parent hashing.
- ArchKeel `--against c2ff96d5`.
- Native collection at head and base; decoded call and UNKNOWN diffs.
- Tests: Authoring, MCP, CLI functional, final-review boundaries and public-API ownership, 925 passed and 4 skipped.
- ruff and mypy (534 files).
- Strict completion gate acceptance.

**NOT VERIFIED:**
- Windows (the `newline=""` entry write is reasoned, not run).
- Full integration suites.
- CE CI.
- EE parity (BuildRequestV5 is CE first).
- The installed-wheel check (the author ran `check_installed_authoring.py --mcp`).

## Addendum: rebase onto development `2a1898ab` (#365 merged), head `5943699a`

**Receipt.** I rebound it against development's current receipt.
- The #368/#369 continuation passages and development's `boundary_type_limit` note are kept verbatim.
- The slice (c) facts are appended to `review_scope` and `delivery_boundary`.

**Contract.** The digest moves from development's `3bc00974` to `c70eaaf6` only because of slice (c)'s five public gains, re-confirmed with ArchKeel `--against 2a1898ab`. Development's TotalRowBudget entries stay in the file.

**b2's late changes still fit slice (c):**
- Build lints the entry with `validator.validate` before calling `include_graph`. With an unreadable graph, `declarations_complete=False` suppresses only undeclared-id findings, and the INCLUDE refusal decides.
- A step-declared client is refused in `include_graph` before step lint. Probed under V5 Build: `rejected`, phase POLICY, with only `("include","model/a.xml","database","line",2)`.
- Client scoping (file plus entry) and project-wide memstores are unchanged.
- The `order_desk` Build is `ready` with the same 9-file manifest.

**Native result against `2a1898ab`, re-collected after an initial collector timeout under load:**
- 0 violations; 1,424 unresolved calls, 178 typing positions, 255 unknown positions.
- The decoded unresolved-call diff is exactly the slice (c) set: `item.path.as_posix` and `read.add` added; the two V4 `model_dump` calls, `proof_json.encode` and `build.model_copy` removed. No file-object `.read` call moved.
- 20 diagnostics, with the one pointer shift.
- 313 UNKNOWN records: the `build()` request position is removed; 17 records have reference churn only.

**Tests:** 101 passed across project build, global Build budget, dynamic count, Build workflow, Build verification, dryrun includes and public lint.

## Addendum: `7c53e2cd` (#371, Codex P1), accepted

**The finding was valid.** `create_authoring_application(project).build()` was bound to the default `model.xml`, so the executor refused every project; only the CLI and MCP passed `PROJECT_ENTRY_PATH`.

**The fix.**
- The composition root (`bootstrap.py`) creates a second workspace context at `PROJECT_ENTRY_PATH`.
- It wires Build to that context's validator and executor, and to `ProjectFiles`, through the existing public ports (`project_validator`, `project_executor`).
- The other operations keep the descriptor-bound ports.
- It is the smallest correct placement: binding stays in the composition root, and no contract changes.

**Verification.**
- The default factory now builds `order_desk` `ready` with the 9-file manifest.
- 61 tests passed across project build, Build workflow, public API, MCP end-to-end and `cli_v4`; ruff and mypy are clean.

**Native result.**
- 0 violations; 1,424 unresolved calls, 178 typing positions, 255 unknown positions.
- The unresolved-call diff against development is unchanged.
- The same 20 diagnostics and 313 UNKNOWN identities.
- AUTHORING-API-TYPES decides 15 of 32 positions; the two new constructor positions are both decided.

