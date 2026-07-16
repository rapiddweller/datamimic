"""Evaluate authoring-intent diagnostics before compiling and running XML."""

from datamimic_ce.authoring.contracts import CompilePlan
from datamimic_ce.authoring.diagnostics import Diagnostic
from datamimic_ce.authoring.rules import ALL_INTENT_RULES, IntentLintContext
from datamimic_ce.authoring.spec import AuthoringSpecV1


def lint_intent(spec: AuthoringSpecV1, plan: CompilePlan) -> list[Diagnostic]:
    """Return stable, non-blocking advisories from the validated intent model."""

    context = IntentLintContext()
    diagnostics: list[Diagnostic] = []
    for rule in ALL_INTENT_RULES:
        diagnostics.extend(rule().check(context, spec, plan))
    return diagnostics
