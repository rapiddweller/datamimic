# Project acceptance architecture review (ADR #356 slice c)

**Accepted within the local architecture review scope.** Reviewer: Astra (independent Opus 5.5 review agent, delegated by Alex).

- Scope: `feat/project-acceptance-c`, base `c2ff96d5` (b2 head, PR #365), head `60df0427` (`dc0f0ae8`, `79dfda42`, `60df0427`).
- This review rebinds the [Build includes receipt](issue-356-build-includes-review.md) and keeps all of its assessments.
- It does not authorize a merge and does not claim that every native rule passes.

## Current binding

| Item | Value |
|---|---|
| Source | `884a12106ca6f316437bed4c615cd462605c4fe10d5c4dcc473d2fabe9de76ad` |
| Target (changed by the contract widening below) | `4ed7e7f238d6b453e0a889013212c7c72ef90c5ec65a10bf0784d3c2baf184c0` |
| Analyzer (unchanged; ArchKeel 4.0.1, Python 3.11.12) | `bb1a3262d3fdd38c3e9a6af980cc063281ae98ab1c28c89c2c5be6dfb450744f` |
| Validation | `4a397f51c242cc18dd305eaaa111063a4b02243edd0949c20672964f679d0e2c` |
| UNKNOWN | `2d513e4d11a2f4915d538a7f90838afc1db46de2f3bb0f40ac11c6f104081b8f` |

**Budgets:** `calls_unresolved` is ratcheted down from 1,426 to 1,418, and `typing_positions` stays at 178. No gate change.

## Design

```
authoring build [PROJECT]
  ProjectFiles.read (AuthoringWorkspaceContext.read, contained)   acceptance/build.json -> BuildRequestV5
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

### Finding (Low): budget tightening partly by name collision

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

## Native result

- **Base:** I re-collected `c2ff96d5` independently, and it reproduces every digest of the previous receipt.
- **Head:**
  - 534/534 files; failures [].
  - 0 violations, 0 baseline additions or resolutions.
  - Rules: 271 PASS and 5 UNKNOWN; the report exits 0.
- **Calls:** 13,338 analyzed; resolved 9,874; partially resolved 2,046; unresolved 1,418.
- **Diagnostics:** still 20. The `CompiledDocumentArtifact` publication diagnostic moves from `/components/1/public/21` to `/22`, because new public entries precede it. Subject, kind and claim are identical, and the receipt carries the new pointer.
- **UNKNOWN records:** 314 → 313.
  - `UNKNOWN-BOUNDARY-TYPE-POSITION-607498d48e034dc8` (the `AuthoringApplication.build` request position) no longer exists, because `build()` takes no argument. It is removed from the `other` group with a note.
  - 17 records have reference churn only.
  - AUTHORING-API-TYPES now decides 13 of 30 positions, and the dynamic-call record reads 1,418.

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
