# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Fixture-driven lint regression: every fixture descriptor seeds known violations;
the linter must report (at least) exactly those rule ids. Doubles as the eval set."""

from pathlib import Path

import pytest

from datamimic_ce.authoring import lint_descriptor

_FIXTURES = Path(__file__).resolve().parent / "fixtures"

# fixture -> rule ids that MUST be reported (subset match: broad hints like DM303 may add to it)
EXPECTED: dict[str, set[str]] = {
    "fx_xml_syntax.xml": {"DM001"},
    "fx_unknown_element.xml": {"DM101"},
    "fx_bad_nesting.xml": {"DM102", "DM107"},
    "fx_typo_attribute.xml": {"DM103"},
    "fx_missing_required.xml": {"DM104"},
    "fx_bad_enum.xml": {"DM105"},
    "fx_root_not_setup.xml": {"DM106"},
    "fx_dead_attr.xml": {"DM103"},  # bucket was purged EE surface -> unknown attribute
    "fx_count_conflicts.xml": {"DM201", "DM212"},
    "fx_missing_count.xml": {"DM202"},
    "fx_key_two_modes.xml": {"DM203"},
    "fx_unique_misuse.xml": {"DM204"},
    "fx_source_modes.xml": {"DM205", "DM214"},
    "fx_nestedkey_cyclic.xml": {"DM213"},
    "fx_memory_and_seed.xml": {"DM301", "DM302", "DM303"},
    "fx_seed_multiprocess_pagesize.xml": {"DM304", "DM305"},
    "fx_upsert_zero.xml": {"DM307"},
    "fx_generator_strings.xml": {"DM310", "DM311"},
    "fx_undeclared_refs.xml": {"DM401", "DM403"},
    "fx_engine_fallback.xml": {"DM000"},
    "fx_script_interpolation.xml": {"DM314"},
    "fx_nestedkey_no_type.xml": {"DM216"},
    "fx_unknown_source.xml": {"DM402"},
    "fx_missing_include.xml": {"DM405"},
    "fx_selector_without_count.xml": {"DM211"},
    "fx_key_type_list.xml": {"DM105"},  # C-2 regression: key type=list is invalid
    "fx_variable_two_modes.xml": {"DM203"},  # C-3: variable with two modes is invalid
    "fx_iteration_selector_no_source.xml": {"DM214"},  # C-1: iterationSelector requires source
}


@pytest.mark.parametrize("fixture", sorted(EXPECTED))
def test_fixture_reports_seeded_rules(fixture: str) -> None:
    result = lint_descriptor(_FIXTURES / fixture)
    found = {diag.rule for diag in result.diagnostics}
    missing = EXPECTED[fixture] - found
    assert not missing, f"{fixture}: expected {missing} in {sorted(found)}"


def test_every_fixture_produces_diagnostics() -> None:
    for fixture in EXPECTED:
        result = lint_descriptor(_FIXTURES / fixture)
        assert result.diagnostics, f"{fixture} should produce at least one diagnostic"


def test_dm401_validates_client_operation() -> None:
    from datamimic_ce.authoring import lint_source

    def _op_flagged(op: str) -> bool:
        xml = (
            f'<setup rngSeed="1"><mongodb id="db"/>'
            f'<generate name="g" count="3" source="db" selector="find: \'c\', filter: {{}}" '
            f'target="db.{op}"/></setup>'
        )
        return any(d.rule == "DM401" for d in lint_source(xml).diagnostics)

    assert not any(_op_flagged(op) for op in ("update", "upsert", "delete"))  # real ops (#165)
    assert _op_flagged("insert") and _op_flagged("frobnicate")  # typos / unsupported


def test_dm315_increment_generator_fires_nested_only() -> None:
    from datamimic_ce.authoring import lint_source

    nested = (
        '<setup rngSeed="1"><generate name="parents" count="5" target="ConsoleExporter">'
        '<key name="pid" generator="IncrementGenerator"/>'
        '<generate name="children" count="3" target="ConsoleExporter">'
        '<key name="cid" generator="IncrementGenerator()"/>'
        "</generate></generate></setup>"
    )
    diags = [d for d in lint_source(nested).diagnostics if d.rule == "DM315"]
    # nested cid fires; top-level pid stays silent
    assert [d.name for d in diags] == ["cid"]
    assert "parent" in diags[0].fix_hint and "this." in diags[0].fix_hint

    # keys inside <nestedKey> are per-record list items, not per-parent id sequences
    nested_key = (
        '<setup rngSeed="1"><generate name="g" count="5" target="ConsoleExporter">'
        '<key name="id" generator="IncrementGenerator"/>'
        '<nestedKey name="items" type="list" count="2">'
        '<key name="seq" generator="IncrementGenerator"/></nestedKey>'
        "</generate></setup>"
    )
    assert not [d for d in lint_source(nested_key).diagnostics if d.rule == "DM315"]


def test_dm316_count_with_source_hints_the_silent_cap() -> None:
    from datamimic_ce.authoring import lint_source

    base = (
        '<setup rngSeed="1"><memstore id="mem"/>'
        '<generate name="seed" count="5" target="mem"><key name="x" constant="1"/></generate>'
        '<iterate name="reader" source="mem" type="seed" distribution="ordered" '
        'count="99" {extra}target="ConsoleExporter"/></setup>'
    )
    fired = lint_source(base.format(extra="")).diagnostics
    assert any(d.rule == "DM316" and d.name == "reader" for d in fired)
    # cyclic wraps the source — no silent cap, no hint
    silent = lint_source(base.format(extra='cyclic="True" ')).diagnostics
    assert not any(d.rule == "DM316" for d in silent)
    # {script} counts are not literal digits — out of scope
    scripted = lint_source(base.format(extra="").replace('count="99"', 'count="{5 * 3}"')).diagnostics
    assert not any(d.rule == "DM316" for d in scripted)


def test_db_descriptor_lints_without_spurious_credential_error() -> None:
    from datamimic_ce.authoring import lint_source

    # A <variable source= selector=> reading a declared client is valid DSL; the linter
    # must NOT reject it just because DB credentials aren't wired in the lint environment.
    ok = (
        '<setup rngSeed="1"><mongodb id="mongodb"/>'
        '<generate name="g" count="5" distribution="ordered" target="ConsoleExporter">'
        '<variable name="mongo_data" source="mongodb" selector="find: \'c\', filter: {}"/>'
        '<key name="v" script="mongo_data.x"/></generate></setup>'
    )
    result = lint_source(ok)
    assert result.ok, [(d.rule, d.message) for d in result.diagnostics]
    assert not any(d.rule == "DM000" for d in result.diagnostics)

    # but a real structural error in a DB descriptor is still caught by phase 2
    broken = (
        '<setup rngSeed="1"><mongodb id="m"/>'
        '<generate name="g" count="1" target="ConsoleExporter"><key name="x" bogus="1"/></generate></setup>'
    )
    assert not lint_source(broken).ok

    # a MISSING STRUCTURAL attr (<database> without dbms) shares the credential
    # message but must NOT be suppressed — it is a real error, not an env concern.
    missing_dbms = (
        '<setup rngSeed="1"><database id="db" system="mongodb"/>'
        '<generate name="g" count="1" source="db" selector="find: \'c\', filter: {}" '
        'target="ConsoleExporter"/></setup>'
    )
    assert not lint_source(missing_dbms).ok


def test_dm105_distribution_is_context_aware() -> None:
    """distribution= means NumberDistribution on <key>/<id> (numeric-range sequence) but
    SourceDistribution everywhere else (row selection) — DM105 must validate against the
    right enum instead of always assuming SourceDistribution."""
    from datamimic_ce.authoring import lint_source

    # valid numeric-range sequence value, invalid as a SourceDistribution -- must NOT fire
    numeric = lint_source(
        '<setup rngSeed="1"><generate name="g" count="5" target="ConsoleExporter">'
        '<key name="n" type="int" min="0" max="100" distribution="step"/></generate></setup>'
    )
    assert not any(d.rule == "DM105" for d in numeric.diagnostics), numeric.diagnostics

    # valid SourceDistribution value, invalid as a NumberDistribution -- must fire on <key>
    bad_numeric = lint_source(
        '<setup rngSeed="1"><generate name="g" count="5" target="ConsoleExporter">'
        '<key name="n" type="int" min="0" max="100" distribution="random"/></generate></setup>'
    )
    assert any(d.rule == "DM105" for d in bad_numeric.diagnostics)

    # unchanged: <variable>/<generate> still validate against SourceDistribution
    source_ctx = lint_source(
        '<setup rngSeed="1"><generate name="g" count="5" target="ConsoleExporter">'
        '<variable name="p" entity="Person" distribution="step"/>'
        '<key name="n" script="p.name"/></generate></setup>'
    )
    assert any(d.rule == "DM105" for d in source_ctx.diagnostics)


def test_dm105_type_hint_points_to_datetime_construct() -> None:
    from datamimic_ce.authoring import lint_source

    result = lint_source(
        '<setup rngSeed="1"><generate name="g" count="5" target="ConsoleExporter">'
        '<key name="at" type="datetime"/></generate></setup>'
    )
    diag = next(d for d in result.diagnostics if d.rule == "DM105")
    assert "DateTimeGenerator" in diag.fix_hint
    assert "ts.now" in diag.fix_hint


def test_dm105_skips_scalar_type_check_on_source_backed_read() -> None:
    """On <variable>/<nestedKey> with source=, type= selects the producing statement's
    name (StatementUtil.resolve_source_entity: sourceEntity -> type -> name) -- an
    arbitrary id, not a scalar cast. Must not be checked against the scalar type list."""
    from datamimic_ce.authoring import lint_source

    memstore_read = lint_source(
        '<setup rngSeed="1"><memstore id="mem"/>'
        '<generate name="orders" count="5" target="mem">'
        '<key name="n" type="int"/></generate>'
        '<generate name="summary" count="5">'
        '<variable name="row" source="mem" type="orders" distribution="ordered"/>'
        '<key name="n" script="row.n"/></generate></setup>'
    )
    assert not any(d.rule == "DM105" for d in memstore_read.diagnostics), memstore_read.diagnostics

    # unchanged: same tag, no source= -- type= is still a scalar cast and still checked
    no_source = lint_source(
        '<setup rngSeed="1"><generate name="g" count="5" target="ConsoleExporter">'
        '<variable name="p" type="bogus" constant="x"/>'
        '<key name="n" script="p"/></generate></setup>'
    )
    assert any(d.rule == "DM105" for d in no_source.diagnostics)

    # unchanged: <key>/<id> never read a source (key_task.py ignores it) -- always checked
    key_bogus = lint_source(
        '<setup rngSeed="1"><generate name="g" count="5" target="ConsoleExporter">'
        '<key name="n" type="bogus"/></generate></setup>'
    )
    assert any(d.rule == "DM105" for d in key_bogus.diagnostics)


def test_dm401_dm402_hints_show_the_memstore_declaration() -> None:
    """A missing target/source id is fixed by declaring a <memstore> -- show the literal
    snippet instead of just naming the concept, so a weak model can copy it mechanically."""
    from datamimic_ce.authoring import lint_source

    dm401 = lint_source(
        '<setup rngSeed="1"><generate name="g" count="5" target="mem">'
        '<key name="n" type="int"/></generate></setup>'
    )
    diag = next(d for d in dm401.diagnostics if d.rule == "DM401")
    assert '<memstore id="mem"/>' in diag.fix_hint

    dm402 = lint_source(
        '<setup rngSeed="1"><generate name="g" count="5" target="ConsoleExporter">'
        '<variable name="row" source="mem" type="x"/>'
        '<key name="n" script="row.n"/></generate></setup>'
    )
    diag = next(d for d in dm402.diagnostics if d.rule == "DM402")
    assert '<memstore id="mem"/>' in diag.fix_hint


def test_dry_run_never_crashes_on_parse_error() -> None:
    from datamimic_ce.authoring.dryrun import dry_run_source

    # A descriptor whose engine re-parse raises must yield a diagnostic, not crash the tool.
    result = dry_run_source(
        '<setup rngSeed="1"><database id="db" system="mongodb"/>'
        '<generate name="g" count="1" source="db" selector="find: \'c\', filter: {}" '
        'target="ConsoleExporter"/></setup>'
    )
    assert not result.ok and result.diagnostics


def test_clean_descriptor_is_ok() -> None:
    result = lint_descriptor(_FIXTURES / "fx_clean.xml")
    errors = [d for d in result.diagnostics if d.severity.value == "error"]
    assert result.ok and not errors, [d.message for d in result.diagnostics]


def test_typo_fix_hint_carries_did_you_mean() -> None:
    result = lint_descriptor(_FIXTURES / "fx_typo_attribute.xml")
    typo = next(d for d in result.diagnostics if d.rule == "DM103")
    assert "pageSize" in typo.fix_hint


def test_diagnostics_carry_location_and_hint() -> None:
    result = lint_descriptor(_FIXTURES / "fx_typo_attribute.xml")
    for diag in result.diagnostics:
        assert diag.fix_hint, f"{diag.rule} without fix_hint"
        assert diag.path.startswith("/"), diag
        assert diag.line is None or diag.line >= 1
