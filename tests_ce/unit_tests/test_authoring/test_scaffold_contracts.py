# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""Parity tests for scaffold across MCP, CLI, and service transports."""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from typer.testing import CliRunner

from datamimic_ce.authoring.contracts import (
    AcceptanceStatus,
    AuthoringStage,
    ScaffoldRequest,
)
from datamimic_ce.authoring.service import scaffold
from datamimic_ce.cli import app
from datamimic_ce.mcp.models import ScaffoldArgs
from datamimic_ce.mcp.server import scaffold_impl

# Test specs covering various scenarios
SPEC_VALID_DRY_RUN = {
    "seed": 1,
    "generates": [{
        "name": "customers", "count": 10, "target": "JSON",
        "fields": [
            {"name": "id", "kind": "increment"},
            {"name": "name", "kind": "person_name"},
            {"name": "age", "kind": "int_range", "min": 18, "max": 90},
        ],
    }],
}

SPEC_VALID_NO_DRY_RUN = {
    "seed": 1,
    "generates": [{
        "name": "items", "count": 5, "target": "JSON",
        "fields": [{"name": "id", "kind": "increment"}],
    }],
}

SPEC_MALFORMED = {
    "generates": [{
        "name": "data", "count": 5, "target": "JSON",
        # Missing fields array — should fail at render
    }],
}

SPEC_LINT_FAILURE = {
    "generates": [{
        "name": "data", "count": 5, "target": "JSON",
        "fields": [{"name": "id", "kind": "increment"}],
        # DM303: No rngSeed — will pass render but lint will warn
    }],
}

SPEC_V1 = {
    "version": "1",
    "seed": 1,
    "products": [
        {
            "kind": "generated",
            "name": "items",
            "count": 2,
            "fields": [{"kind": "increment", "name": "id"}],
            "targets": [{"kind": "file_export", "format": "JSON"}],
        }
    ],
    "expectations": [{"kind": "exact_count", "product": "items", "count": 2}],
}

SPEC_V1_COMPLETE_MEMSTORE = {
    "version": "1",
    "seed": 1,
    "products": [
        {
            "kind": "generated",
            "name": "producer",
            "count": 5,
            "targets": [{"kind": "memstore", "id": "mem"}],
            "fields": [
                {
                    "kind": "increment",
                    "name": "id",
                    "roles": [{"kind": "identifier"}],
                }
            ],
        },
        {
            "kind": "source",
            "name": "reader",
            "source": {"kind": "memstore", "id": "mem", "product": "producer"},
            "fields": [
                {
                    "kind": "script",
                    "name": "id",
                    "script": "id",
                    "roles": [
                        {
                            "kind": "foreign_key",
                            "parent_product": "producer",
                            "parent_field": "id",
                        }
                    ],
                },
                {
                    "kind": "int_range",
                    "name": "seat",
                    "minimum": 1,
                    "maximum": 10,
                    "unique": True,
                },
            ],
        },
    ],
}


class TestScaffoldParity:
    """Verify parity between service, MCP, and CLI implementations."""

    def test_service_scaffold_valid_dry_run(self):
        """Service correctly processes a valid spec with dry-run."""
        request = ScaffoldRequest(
            spec=SPEC_VALID_DRY_RUN,
            max_count=10,
            sample_rows=5,
            response_format="concise",
        )
        result = scaffold(request)

        assert result.ok is True
        assert result.stage is AuthoringStage.ACCEPTANCE
        assert result.verified is True
        assert result.xml is not None
        assert len(result.products) > 0
        assert all(p.name and p.count >= 0 for p in result.products)

    def test_service_scaffold_rejects_removed_lint_only_switch(self):
        """Scaffold always runs the complete canonical transaction."""
        with pytest.raises(ValueError, match="dry_run"):
            ScaffoldRequest(spec=SPEC_VALID_NO_DRY_RUN, dry_run=False)

    def test_service_scaffold_render_error(self):
        """Service correctly handles render errors."""
        request = ScaffoldRequest(
            spec=SPEC_MALFORMED,
            max_count=10,
            sample_rows=5,
            response_format="concise",
        )
        result = scaffold(request)

        assert result.ok is False
        assert result.stage is AuthoringStage.RENDER
        assert result.error is not None
        assert result.xml is None

    def test_mcp_service_parity_dry_run(self):
        """MCP scaffold_impl returns same data as service layer."""
        args = ScaffoldArgs(
            spec=SPEC_VALID_DRY_RUN,
            max_count=10,
            sample_rows=5,
            response_format="concise",
        )
        request = ScaffoldRequest(**args.model_dump())

        mcp_result = scaffold_impl(args)
        service_result = scaffold(request)
        service_dict = service_result.model_dump(mode="json", exclude_none=True)

        # Compare key fields
        assert mcp_result["ok"] == service_dict["ok"]
        assert mcp_result["stage"] == service_dict["stage"]
        assert mcp_result["xml"] == service_dict["xml"]
        assert mcp_result["compile_plan"] == service_dict["compile_plan"]

        # Compare products structure (should have name, count, sample, truncated_rows)
        mcp_products = mcp_result.get("products", [])
        service_products = service_dict.get("products", [])
        assert len(mcp_products) == len(service_products)
        for mcp_prod, service_prod in zip(mcp_products, service_products, strict=False):
            assert mcp_prod["name"] == service_prod["name"]
            assert mcp_prod["count"] == service_prod["count"]
            assert "sample" in mcp_prod
            assert "truncated_rows" in mcp_prod

    def test_cli_json_parity_dry_run(self):
        """CLI JSON output matches service layer structure."""
        runner = CliRunner()
        spec_json = json.dumps(SPEC_VALID_DRY_RUN)

        with TemporaryDirectory() as tmpdir:
            spec_file = Path(tmpdir) / "spec.json"
            spec_file.write_text(spec_json)

            result = runner.invoke(app, ["scaffold", str(spec_file), "--format", "json"])
            assert result.exit_code == 0

            cli_output = json.loads(result.stdout)

            # Verify service generates same structure
            request = ScaffoldRequest(
                spec=SPEC_VALID_DRY_RUN,
                max_count=10,
                sample_rows=5,
                response_format="concise",
            )
            service_result = scaffold(request)
            service_dict = service_result.model_dump(mode="json", exclude_none=True)

            # Compare structure (not values, as they may differ due to RNG)
            assert cli_output["ok"] == service_dict["ok"]
            assert cli_output["stage"] == service_dict["stage"]
            assert "xml" in cli_output
            assert "xml" in service_dict
            assert cli_output["compile_plan"] == service_dict["compile_plan"]
            assert len(cli_output.get("products", [])) == len(service_dict.get("products", []))

    def test_cli_rejects_removed_no_dry_run_switch(self):
        """The removed lint-only path cannot be selected through CLI."""
        runner = CliRunner()
        spec_json = json.dumps(SPEC_VALID_NO_DRY_RUN)

        with TemporaryDirectory() as tmpdir:
            spec_file = Path(tmpdir) / "spec.json"
            spec_file.write_text(spec_json)

            result = runner.invoke(app, ["scaffold", str(spec_file), "--no-dry-run", "--format", "json"])
            assert result.exit_code == 2

    def test_cli_stdin_support(self):
        """CLI supports '-' for reading spec from stdin."""
        runner = CliRunner()
        spec_json = json.dumps(SPEC_VALID_NO_DRY_RUN)

        result = runner.invoke(
            app,
            ["scaffold", "-", "--format", "json"],
            input=spec_json,
        )
        assert result.exit_code == 0

        cli_output = json.loads(result.stdout)
        assert cli_output["ok"] is True
        assert "xml" in cli_output

    def test_v1_cli_mcp_service_parity(self):
        """All transports accept the same canonical model.dm.json contract."""
        request = ScaffoldRequest(spec=SPEC_V1)
        service_result = scaffold(request).model_dump(mode="json", exclude_none=True)
        mcp_result = scaffold_impl(ScaffoldArgs(**request.model_dump()))
        cli_result = CliRunner().invoke(
            app,
            ["scaffold", "-", "--format", "json"],
            input=json.dumps(SPEC_V1),
        )

        assert cli_result.exit_code == 0
        cli_output = json.loads(cli_result.stdout)
        assert mcp_result["xml"] == service_result["xml"] == cli_output["xml"]
        assert mcp_result["compile_plan"] == service_result["compile_plan"]
        assert cli_output["compile_plan"] == service_result["compile_plan"]
        assert service_result["normalization_notes"] == []

    def test_v1_acceptance_response_is_identical_across_transports(self):
        """CLI and MCP preserve a complete memstore result byte-for-byte."""
        request = ScaffoldRequest(
            spec=SPEC_V1_COMPLETE_MEMSTORE,
            max_count=5,
            sample_rows=1,
        )
        service_result = scaffold(request).model_dump(mode="json", exclude_none=True)
        mcp_result = scaffold_impl(ScaffoldArgs(**request.model_dump()))
        cli_result = CliRunner().invoke(
            app,
            [
                "scaffold",
                "-",
                "--format",
                "json",
                "--max-count",
                "5",
                "--sample-rows",
                "1",
            ],
            input=json.dumps(SPEC_V1_COMPLETE_MEMSTORE),
        )

        assert cli_result.exit_code == 0
        assert json.loads(cli_result.stdout) == service_result == mcp_result
        assert service_result["stage"] == "acceptance"
        assert service_result["verified"] is True
        assert {product["name"]: product["count"] for product in service_result["products"]} == {
            "producer": 5,
            "reader": 5,
        }
        memstore = next(
            item
            for item in service_result["acceptance"]["results"]
            if item["kind"] == "memstore_completeness"
        )
        assert memstore["status"] == AcceptanceStatus.PASS
        assert memstore["required_consumer_foreign_key"] == {
            "role_kind": "foreign_key",
            "parent_product": "producer",
            "parent_field": "id",
            "required_count": 1,
            "observed_count": 1,
        }

    def test_v1_count_remediation_is_identical_across_transports(self):
        """CLI and MCP serialize the service-owned retry action unchanged."""
        spec = json.loads(json.dumps(SPEC_V1_COMPLETE_MEMSTORE))
        spec["products"][0]["count"] = 15
        spec["products"][1]["fields"] = spec["products"][1]["fields"][:1]
        request = ScaffoldRequest(spec=spec, max_count=10, sample_rows=1)

        service_result = scaffold(request).model_dump(mode="json", exclude_none=True)
        mcp_result = scaffold_impl(ScaffoldArgs(**request.model_dump()))
        cli_result = CliRunner().invoke(
            app,
            [
                "scaffold",
                "-",
                "--format",
                "json",
                "--max-count",
                "10",
                "--sample-rows",
                "1",
            ],
            input=json.dumps(spec),
        )

        assert cli_result.exit_code == 1
        assert json.loads(cli_result.stdout) == service_result == mcp_result
        assert service_result["remediations"] == [
            {
                "kind": "retry_with_parameter",
                "parameter": "max_count",
                "minimum_value": 15,
                "affected_products": ["producer", "reader"],
            }
        ]

    def test_v1_source_repair_is_identical_across_transports(self):
        """Nested source repair is a canonical result, not adapter policy."""
        spec = json.loads(json.dumps(SPEC_V1_COMPLETE_MEMSTORE))
        source = spec["products"][1]["source"]
        source["type"] = source.pop("product")
        request = ScaffoldRequest(spec=spec)

        service_result = scaffold(request).model_dump(mode="json", exclude_none=True)
        mcp_result = scaffold_impl(ScaffoldArgs(**request.model_dump()))
        cli_result = CliRunner().invoke(
            app,
            ["scaffold", "-", "--format", "json"],
            input=json.dumps(spec),
        )

        assert cli_result.exit_code == 2
        assert json.loads(cli_result.stdout) == service_result == mcp_result
        repair = service_result["issues"][0]["repair"]
        assert repair["replacement_field"] == "product"
        assert repair["rejected_value"] == "producer"

    def test_v1_missing_role_evidence_is_identical_across_transports(self):
        """The missing consumer role remains structured through both adapters."""
        spec = json.loads(json.dumps(SPEC_V1_COMPLETE_MEMSTORE))
        spec["products"][1]["fields"][0]["roles"] = []
        request = ScaffoldRequest(spec=spec, max_count=5, sample_rows=1)

        service_result = scaffold(request).model_dump(mode="json", exclude_none=True)
        mcp_result = scaffold_impl(ScaffoldArgs(**request.model_dump()))
        cli_result = CliRunner().invoke(
            app,
            [
                "scaffold",
                "-",
                "--format",
                "json",
                "--max-count",
                "5",
                "--sample-rows",
                "1",
            ],
            input=json.dumps(spec),
        )

        assert cli_result.exit_code == 1
        assert json.loads(cli_result.stdout) == service_result == mcp_result
        memstore = next(
            item
            for item in service_result["acceptance"]["results"]
            if item["kind"] == "memstore_completeness"
        )
        assert memstore["required_consumer_foreign_key"]["observed_count"] == 0

    def test_cli_format_validation(self):
        """CLI validates --format option."""
        runner = CliRunner()
        spec_json = json.dumps(SPEC_VALID_NO_DRY_RUN)

        with TemporaryDirectory() as tmpdir:
            spec_file = Path(tmpdir) / "spec.json"
            spec_file.write_text(spec_json)

            result = runner.invoke(app, ["scaffold", str(spec_file), "--format", "banana"])
            assert result.exit_code == 2
            assert "Invalid format" in result.stdout

    def test_request_bounds_validation_max_count(self):
        """ScaffoldRequest validates max_count bounds."""
        # max_count must be >= 1
        with pytest.raises(ValueError):
            ScaffoldRequest(
                spec=SPEC_VALID_DRY_RUN,
                max_count=0,
            )

        # max_count must be <= 1000
        with pytest.raises(ValueError):
            ScaffoldRequest(
                spec=SPEC_VALID_DRY_RUN,
                max_count=1001,
            )

    def test_request_bounds_validation_sample_rows(self):
        """ScaffoldRequest validates sample_rows bounds."""
        # sample_rows must be >= 1
        with pytest.raises(ValueError):
            ScaffoldRequest(
                spec=SPEC_VALID_DRY_RUN,
                sample_rows=0,
            )

        # sample_rows must be <= 50
        with pytest.raises(ValueError):
            ScaffoldRequest(
                spec=SPEC_VALID_DRY_RUN,
                sample_rows=51,
            )

    def test_normalization_notes_preserved(self):
        """Normalization notes are carried through in ScaffoldResult."""
        # Create a spec that triggers normalization
        spec_with_alias = {
            "generates": [{
                "name": "data", "count": 5, "target": "JSON",
                "fields": [
                    {"name": "id", "kind": "id"},  # alias: id → increment
                    {"name": "email", "kind": "email"},  # alias: email → person_email
                ],
            }],
        }

        request = ScaffoldRequest(
            spec=spec_with_alias,
            response_format="concise",
        )
        result = scaffold(request)

        # Should have normalization notes for kind aliases
        assert len(result.normalization_notes) > 0

    def test_source_backed_unique_insufficient_range_service(self):
        """Source-backed unique range smaller than producer count fails with specific error."""
        spec = {
            "generates": [
                {
                    "name": "producer", "count": 5, "target": "mem,JSON",
                    "fields": [{"name": "id", "kind": "increment"}],
                },
                {
                    "name": "reader", "source": "mem", "source_type": "producer",
                    "fields": [
                        {"name": "id", "kind": "script", "script": "id"},
                        {"name": "seat", "kind": "int_range", "min": 1, "max": 2, "unique": True},
                    ],
                },
            ]
        }
        request = ScaffoldRequest(spec=spec)
        result = scaffold(request)

        assert result.ok is False
        assert result.stage is AuthoringStage.RENDER
        assert result.error is not None
        assert "unique" in result.error
        assert "insufficient" in result.error.lower() or "possible values" in result.error

    def test_source_backed_unique_sufficient_range_service(self):
        """Source-backed unique range sufficient for producer count succeeds."""
        request = ScaffoldRequest(
            spec=SPEC_V1_COMPLETE_MEMSTORE,
            max_count=5,
            sample_rows=3,
        )
        result = scaffold(request)

        assert result.ok is True
        assert result.stage is AuthoringStage.ACCEPTANCE
        assert result.verified is True, result.acceptance
        assert result.acceptance is not None
        assert any(
            item.kind == "memstore_completeness"
            and item.status is AcceptanceStatus.PASS
            for item in result.acceptance.results
        )
        assert result.xml is not None

    def test_mcp_source_backed_unique_insufficient_range(self):
        """MCP source-backed unique range validation matches service layer."""
        spec = {
            "generates": [
                {
                    "name": "producer", "count": 5, "target": "mem,JSON",
                    "fields": [{"name": "id", "kind": "increment"}],
                },
                {
                    "name": "reader", "source": "mem", "source_type": "producer",
                    "fields": [
                        {"name": "id", "kind": "script", "script": "id"},
                        {"name": "seat", "kind": "int_range", "min": 1, "max": 2, "unique": True},
                    ],
                },
            ]
        }
        args = ScaffoldArgs(spec=spec)
        result = scaffold_impl(args)

        assert result["ok"] is False
        assert result["stage"] == "render"
        assert "unique" in result["error"]
