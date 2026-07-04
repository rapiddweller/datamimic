# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""The showcase gallery cannot rot: every example lints clean, dry-runs, and its
documented invariants (referential integrity, decision bands, custom components,
determinism) hold on the captured rows. Dry-run keeps CI artifact-free; the
memstore targets carry the pipeline, sample_rows is raised to see every row."""

from pathlib import Path

import pytest

from datamimic_ce.authoring import lint_descriptor
from datamimic_ce.authoring.dryrun import dry_run

SHOWCASE = Path(__file__).parents[3] / "examples" / "showcase"

_EXAMPLES = sorted(p.name for p in SHOWCASE.iterdir() if (p / "datamimic.xml").is_file())


def _run(example: str, **kwargs):
    result = dry_run(SHOWCASE / example / "datamimic.xml", max_count=25, sample_rows=200, **kwargs)
    assert result.ok, [(d.rule, d.message) for d in result.diagnostics]
    return {p.name: p.sample for p in result.products}


def test_gallery_layout_and_lint() -> None:
    assert _EXAMPLES, "showcase gallery missing"
    for example in _EXAMPLES:
        assert (SHOWCASE / example / "README.md").is_file(), f"{example}: README missing"
        result = lint_descriptor(SHOWCASE / example / "datamimic.xml")
        assert result.ok, (example, [(d.rule, d.message) for d in result.diagnostics])


def test_banking_core_referential_integrity() -> None:
    rows = _run("01-banking-core")
    customers, transactions = rows["customers"], rows["accounts|transactions"]
    accounts = rows["accounts"]
    cust_ids = {c["customer_id"] for c in customers}
    owner = {a["account_id"]: a["customer_id"] for a in accounts}
    assert len(owner) == len(accounts), "account_id not unique"
    assert all(a["customer_id"] in cust_ids for a in accounts)
    # two-hop FK: every transaction points at a real account AND that account's owner
    assert all(
        t["account_id"] in owner and t["customer_id"] == owner[t["account_id"]] for t in transactions
    )
    assert len({t["tx_id"] for t in transactions}) == len(transactions)


def test_banking_core_is_deterministic() -> None:
    assert _run("01-banking-core") == _run("01-banking-core")


def test_multi_source_join_correct() -> None:
    rows = _run("02-multi-source-assembly")
    branches, customers = rows["branches"], rows["branch_customers"]
    city = {int(b["branch_id"]): b["city"] for b in branches}
    assert all(c["branch_city"] == city[c["branch_id"]] for c in customers)
    assert all(
        c["monthly_fee_eur"] == pytest.approx(4.9 if c["segment"] == "retail" else 12.9)
        for c in customers
    )


def test_orchestration_bands_and_timeseries() -> None:
    rows = _run("03-orchestration-timeseries")
    for r in rows["loan_applications"]:
        if r["score"] >= 700:
            assert r["decision"] == "approved" and 3.1 <= r["rate_pct"] <= 4.5
        elif r["score"] >= 550:
            assert r["decision"] == "manual_review" and 4.6 <= r["rate_pct"] <= 7.9
        else:
            assert r["decision"] == "declined" and "rate_pct" not in r
    ticks = rows["fx_ticks"]
    assert {t["pair"] for t in ticks} == {"EUR/USD", "EUR/GBP"}
    eur_usd = sorted((t["tick"], t["mid"]) for t in ticks if t["pair"] == "EUR/USD")
    assert all(float(b[1]) > float(a[1]) for a, b in zip(eur_usd, eur_usd[1:], strict=False))


def test_python_seam_custom_components() -> None:
    import re

    # <execute> loads the custom classes; that is the point of the example
    rows = _run("04-python-seam", allow_side_effects=True)
    cards = rows["cards"]
    assert all(re.fullmatch(r"\d{6}\*{6}\d{4}", c["pan_masked"]) for c in cards)
    for c in cards:
        expected = "high" if c["limit_eur"] >= 10000 else "medium" if c["limit_eur"] >= 3000 else "low"
        assert c["risk_bucket"] == expected
