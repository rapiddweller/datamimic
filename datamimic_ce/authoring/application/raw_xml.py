# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License. See LICENSE.

"""Validate and execute raw XML through the same bounded CE adapter."""

from __future__ import annotations

from pydantic import SecretBytes

from datamimic_ce.authoring.domain.build_rules import catalog_diagnostic
from datamimic_ce.authoring.domain.common import MAX_AUTHORING_XML_LENGTH
from datamimic_ce.authoring.domain.diagnostics import AuthoringRuleId, DiagnosticPhase
from datamimic_ce.authoring.domain.requests import BoundedExecutionRequest, RunPhase, RunRequest, RunResult
from datamimic_ce.authoring.ports import BoundedExecutor, DescriptorValidator
from datamimic_ce.authoring.projection.evidence import sample_evidence


class RawXmlUseCase:
    def __init__(self, validator: DescriptorValidator, executor: BoundedExecutor) -> None:
        self._validator = validator
        self._executor = executor

    def execute(
        self, request: RunRequest, *, phase: RunPhase, pseudonymization_key: SecretBytes | None = None
    ) -> RunResult:
        lint = self._validator.validate(request.xml, descriptor_path=request.descriptor_path)
        if not lint.ok:
            return RunResult(ok=False, phase=RunPhase.LINT, diagnostics=lint.diagnostics)
        if phase is RunPhase.DRY_RUN and request.allow_side_effects:
            return RunResult(
                ok=False,
                phase=phase,
                diagnostics=(
                    catalog_diagnostic(
                        AuthoringRuleId.SIDE_EFFECT,
                        "Dry-run cannot enable side effects.",
                        phase=DiagnosticPhase.POLICY,
                    ),
                ),
            )
        if len(request.xml) > MAX_AUTHORING_XML_LENGTH:
            return RunResult(
                ok=False,
                phase=phase,
                diagnostics=(
                    catalog_diagnostic(
                        AuthoringRuleId.LIMIT,
                        "Descriptor exceeds the bounded XML size limit.",
                        phase=DiagnosticPhase.POLICY,
                        path=("xml",),
                        expected=MAX_AUTHORING_XML_LENGTH,
                        actual=len(request.xml),
                    ),
                ),
            )
        evidence = self._executor.execute(
            BoundedExecutionRequest(
                xml=request.xml,
                descriptor_path=request.descriptor_path,
                max_count=request.max_count,
                allow_side_effects=request.allow_side_effects,
                timeout_seconds=request.timeout_seconds,
            ),
            pseudonymization_key=pseudonymization_key,
        )
        try:
            products = sample_evidence(evidence.captured, request.sample_rows)
        except ValueError:
            return RunResult(
                ok=False,
                phase=phase,
                diagnostics=(
                    *evidence.diagnostics,
                    catalog_diagnostic(
                        AuthoringRuleId.VALIDATION,
                        "Bounded capture cannot be represented faithfully.",
                        phase=DiagnosticPhase.EVIDENCE,
                    ),
                ),
            )
        return RunResult(
            ok=evidence.ok and evidence.base_run_ok, phase=phase, products=products, diagnostics=evidence.diagnostics
        )
