"""Task that installs demographic profiles into the setup context."""

from __future__ import annotations

from pathlib import Path
from random import Random

from datamimic_ce.contexts.demographic_context import DemographicContext
from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.domains.common.demographics.loader import load_demographic_profile
from datamimic_ce.domains.common.demographics.sampler import DemographicSampler
from datamimic_ce.domains.common.models.demographic_config import DemographicConfig
from datamimic_ce.statements.demographics_statement import DemographicsStatement
from datamimic_ce.tasks.task import SetupSubTask


class DemographicsTask(SetupSubTask):
    def __init__(self, statement: DemographicsStatement):
        self._statement = statement

    def execute(self, ctx: SetupContext) -> None:
        directory = Path(self._statement.directory)
        profile = load_demographic_profile(directory, self._statement.dataset, self._statement.version)
        sampler = DemographicSampler(profile)
        rng = Random(self._statement.rng_seed) if self._statement.rng_seed is not None else Random()
        demographic_context = DemographicContext(
            profile_id=profile.profile_id,
            sampler=sampler,
            overrides=DemographicConfig(),
            rng=rng,
        )
        # Store the context once so every entity derives deterministic child RNGs without hidden globals.
        ctx.set_demographic_context(demographic_context)

    @property
    def statement(self) -> DemographicsStatement:
        return self._statement
