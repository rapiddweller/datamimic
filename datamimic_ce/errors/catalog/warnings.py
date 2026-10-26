# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.

from datamimic_ce.errors.catalog.definition import IssueDefinition
from datamimic_ce.errors.codes import IssueCode, IssueSeverity

ISSUES: list[IssueDefinition] = [
    IssueDefinition(
        code=IssueCode.ECHO_PLACEHOLDER_UNRESOLVED,
        name="ECHO_PLACEHOLDER_UNRESOLVED",
        title="Echo Placeholder Unresolved",
        template=(
            "<echo>: could not evaluate diagnostic placeholder text '{value}'{error_clause}; "
            "logging the literal text instead."
        ),
        cause=("The echo text referenced a name or expression that is not available in the current runtime scope."),
        resolution="Fix the placeholder expression, or remove it if the echo is only diagnostic output.",
        severity=IssueSeverity.WARNING,
    ),
    IssueDefinition(
        code=IssueCode.EXECUTE_BASH_NONDETERMINISTIC,
        name="EXECUTE_BASH_NONDETERMINISTIC",
        title="Bash Execution Is Not Deterministic",
        template=(
            "<execute type='bash'> runs a shell command — this breaks DATAMIMIC's "
            "determinism/reproducibility. Use it for environment side effects, not data generation."
        ),
        cause="A descriptor executes a shell command outside deterministic data generation.",
        resolution="Use Bash only for reviewed environment side effects; generate data through the DSL.",
        severity=IssueSeverity.WARNING,
    ),
    IssueDefinition(
        code=IssueCode.EXECUTE_SEEDED_LOAD_TIME_ENTROPY,
        name="EXECUTE_SEEDED_LOAD_TIME_ENTROPY",
        title="Seeded Script Draws Entropy While It Loads",
        template=(
            "<execute> script '{script}' line {line} {draw}: two runs with the same <setup rngSeed> can differ. "
            "Draw inside a function the model calls, from the run's seeded random."
        ),
        cause=(
            "Under <setup rngSeed> a script's names are rebound to the seeded stand-ins after its body has run, so "
            "a draw in the module body, a default argument, or an import inside a function body is not seeded."
        ),
        resolution=(
            "Move the draw into a function the model calls: in a function the script's random, uuid4 and datetime "
            "are the run's seeded ones. os.urandom and uuid1 have no seeded replacement; use random.randbytes or "
            "uuid4 instead. Or pass the value in from the descriptor. A time or secrets draw has no seeded "
            "stand-in; take that value from the descriptor."
        ),
        severity=IssueSeverity.WARNING,
    ),
]
