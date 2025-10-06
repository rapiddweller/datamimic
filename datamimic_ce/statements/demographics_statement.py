"""Statement object representing the <demographics> node."""

from __future__ import annotations

from datamimic_ce.model.demographics_model import DemographicsModel
from datamimic_ce.statements.statement import Statement


class DemographicsStatement(Statement):
    def __init__(self, model: DemographicsModel):
        super().__init__(None, None)
        self._dataset = model.dataset
        self._version = model.version
        self._directory = model.directory
        self._rng_seed = model.rng_seed

    @property
    def dataset(self) -> str:
        return self._dataset

    @property
    def version(self) -> str:
        return self._version

    @property
    def directory(self) -> str:
        return self._directory

    @property
    def rng_seed(self) -> int | None:
        return self._rng_seed
