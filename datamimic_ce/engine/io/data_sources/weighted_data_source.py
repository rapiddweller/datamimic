# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path
from random import Random

from datamimic_ce.engine.io.data_sources.router import record_source_access
from datamimic_ce.engine.io.files.readers import FileUtil
from datamimic_ce.errors import IssueCode, invalid_source_error


class WeightedDataSource:
    """
    Generate data from weighted data source (.wgt.csv)
    """

    def __init__(self, file_path: Path, separator: str, rng: Random):
        self._file_path = file_path
        record_source_access("file_weighted_csv")
        self._df = FileUtil.read_weight_csv(file_path, separator)
        # Explicit RNG injection (no silent stdlib fallback) so <setup rngSeed>
        # propagates fully to weighted source reads.
        self._rng = rng

    def generate(self) -> str | None:
        """
        Get a random choice from dataframe with weight
        """
        try:
            value: object = self._rng.choices(list(self._df[0]), weights=list(self._df[1]), k=1)[0]
            if value is None or isinstance(value, str):
                return value
            raise TypeError("Weighted CSV values must be strings or None")
        except Exception as err:
            raise invalid_source_error(
                code=IssueCode.SOURCE_INVALID_CSV,
                name=self._file_path.name,
                guidance="Give at least one value row with a positive weight, and check the separator.",
            ) from err
