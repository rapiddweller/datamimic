# Load-time entropy scan: starred generators (follow-up to #390)

**Accepted within the local architecture review scope.** Reviewer: Astra (independent Opus 5.5 review agent, delegated by Alex).

- **Scope:** `fix/ce-entropy-scan-starred`, base `030e6a30` (#390 merged), head `9eb7df8f` (one commit). No PR yet.
- **Origin:** the unanswered Codex P2 on #390.
- **Merge order:** EE MR !464 is still open. It gates the W008 text, not this change.
- This review rebinds the receipt on development and keeps all of its assessments. It does not authorize a merge.

## Binding

- **Moved:** the Source and Validation digests.
- **Unchanged:** Unknowns (319 ids, same groups), Contract (`c70eaaf6`), analyzer, the 20 diagnostics, and the 1,428 / 182 / 261 measurements.
- The rebind uses a gate run that finished without a collector error.

## Review

**The fix.** `_generator_parts` holds the generator's element, every iterable and every `if`. Two places use it:
- the eager-consumer branch;
- a new `ast.Starred` branch for a generator value.

**Now flagged** (probed): `[*gen]`, `max(*gen)`, `(*gen,)`, `{*gen}`, `print(*gen)`, `for x in [*gen]`, `f'{[*gen]}'`, a starred generator inside a subscript argument, and `[*[*gen]]`.

**Already flagged, unchanged:** `{**dict(gen)}`, a dict comprehension under `**`, a conditional expression around `list(gen)`, and `str.join(sep, gen)`.

**Still quiet, correct:** a stored generator, `iter(gen)`, `map(str, gen)`, `zip(gen, gen)`, `print(gen)` (the generator's repr), and starred generators inside a `def` or `lambda` body.

**Not relevant:** module-level `yield`, `yield from` and `await` are compile errors, so the script does not load at all.

### Findings (follow-up, existing since #390, not introduced here)

Five forms consume a generator while the script loads but give no W008. Each was confirmed by two seeded runs: the values differ, and no W008 line appears.

| Form | Example |
|---|---|
| A module-level `for` over a generator | `for x in (random.random() for _ in range(3)):` |
| Tuple unpacking of a generator | `a, b, c = (random.random() for _ in range(3))` |
| A list comprehension over a generator | `[i for i in (random.random() for _ in range(3))]` |
| A lazy wrapper inside an eager consumer | `list(enumerate(gen))` |
| A generator nested as the iterable of a starred or consumed generator | — |

Statically, `0.5 in gen` is also not flagged.

**Suggested rule.** Invert the whitelist. A generator expression is deferred only in two cases:
- it is stored as a single `Name` or attribute target;
- it is passed to a lazy wrapper that is itself stored.

Every other position consumes it at load time.

## Evidence boundary

**LOCAL VERIFIED (by this reviewer):**
- Source review.
- A 26-form scanner probe.
- The 5 runtime determinism probes.
- `test_load_time_entropy` and the DSL functional test: 34 passed.
- ruff.
- A clean gate run and the strict completion gate after the rebind.

**NOT VERIFIED:**
- Full suites and mypy. The coordinator reports these.
- CI.

## Addendum: `746da2f6` (inverted rule)

**Accepted.** The five false negatives above are fixed. A generator expression is now deferred only in two cases:
- it is stored: the value of an `Assign` without an unpacking target, of an `AnnAssign`, or of a bare `Expr`;
- it sits inside lazy wrappers (`iter`, `map`, `zip`, `filter`, `enumerate`, `reversed`) that are themselves stored.

Every other generator is scanned whole. The `Starred` special case is gone because the new rule covers it.

**Re-probed.** Now flagged:
- a module-level `for` over a generator;
- tuple unpacking;
- a list comprehension over a generator;
- `0.5 in gen`;
- `list(enumerate(gen))`;
- a nested generator iterable;
- `sorted(gen)`;
- a consumer inside a `with` block or a class body.

Still quiet:
- a stored generator, also with an attribute, subscript or annotated target, in a class body, or as a bare expression;
- `iter`, `map` and `zip`, also nested and with keyword arguments;
- a generator returned from a `def`.

**Real corpus.** The old and new scanners were compared over the repository's 107 script files. Only the six new flagged corpus scripts change; no demo or test script gains a finding.

### Findings (Low: false positives of the conservative rule; warning only)

All are verified with the scanner.

| Form | Example |
|---|---|
| A stored `itertools` lazy wrapper | `itertools.islice(gen, 2)`, `itertools.chain(gen, gen)`, `itertools.cycle(gen)` |
| A generator stored inside a container literal | `gens = [gen]`, `{'a': gen}` |
| A generator stored through a conditional expression or a walrus | `x = gen if c else ()`, `if (g := gen):` |
| A generator as a default argument | `def f(g=gen):` |
| A generator passed to an unknown callee | `Pool(gen)`, `print(gen)`, a decorator argument |

Two notes on these:
- The default-argument case was quiet at `9eb7df8f`, so it is new. The element runs only when the function consumes the generator, after the names are rebound to the seeded ones.
- The unknown-callee case is documented as conservative.

Suggested follow-up:
1. Add the lazy `itertools` functions to `_LAZY_WRAPPERS`: `islice`, `chain`, `cycle`, `tee`, `takewhile`, `dropwhile`, `accumulate`, `compress`, `groupby`, `starmap`, `zip_longest`, `filterfalse`, `pairwise`. Do not add `product`, `permutations` or `combinations`: they consume their input.
2. Let `mark` descend into container literals, `IfExp` branches, `NamedExpr` values and function default arguments.

**Known limit (documented).** A generator stored and then consumed later at module level is missed.

**Binding.** Source and Validation move. Unknowns, Contract, analyzer and the 20 diagnostics are unchanged, and so are the 1,428 / 182 / 261 measurements.

**LOCAL VERIFIED:**
- A 30-form scanner probe.
- The old-versus-new corpus comparison over 107 scripts.
- `test_load_time_entropy` and the DSL functional test: 34 passed.
- ruff.
- A clean gate run and the strict completion gate after the rebind.
