"""Typed public entry points for authoring application operations."""

from datamimic_ce.authoring.application import service
from datamimic_ce.authoring.contracts import (
    CapabilitiesRequest,
    CapabilitiesResult,
    CheckRequest,
    LintResult,
    ReferenceRequest,
    ReferenceResult,
    RunRequest,
    RunResult,
    ScaffoldRequest,
    ScaffoldResult,
)


def capabilities(request: CapabilitiesRequest | None = None) -> CapabilitiesResult:
    return service.capabilities(request)


def check(request: CheckRequest) -> LintResult:
    return service.check(request)


def reference(request: ReferenceRequest) -> ReferenceResult:
    return service.reference(request)


def run(request: RunRequest) -> RunResult:
    return service.run(request)


def scaffold(request: ScaffoldRequest) -> ScaffoldResult:
    return service.scaffold(request)


__all__ = ["capabilities", "check", "reference", "run", "scaffold"]
