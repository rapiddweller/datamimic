# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
from pathlib import Path

from datamimic_ce.domains.domain_core.base_literal_generator import BaseLiteralGenerator
from datamimic_ce.domains.utils.dataset_path import dataset_path
from datamimic_ce.logger import logger
from datamimic_ce.utils.file_util import FileUtil


class AcademicTitleGenerator(BaseLiteralGenerator):
    """
    Generate random academic title
    """

    def __init__(self, dataset: str | None = None, quota: float = 0.5, rng: random.Random | None = None):
        if quota is None:
            quota = quota or 0.5
        elif quota > 1 or quota < 0:
            quota = 0.5
        self._quota = quota

        dataset = dataset.upper() if dataset else None

        # Always use dataset-suffixed files; rely on dataset_path to fall back to US and log once if missing
        if dataset is None:
            logger.info("Academic title dataset not specified; defaulting to US")
            parts = ("common", "person", "title_US.csv")
        else:
            parts = ("common", "person", f"title_{dataset}.csv")

        #  Build path via dataset_path to avoid duplicated 'domain_data'
        file_path = dataset_path(*parts, start=Path(__file__))
        self._values, self._weights = self._load_academy_csv(file_path)
        self._rng: random.Random = rng or random.Random()

    def generate(self) -> str | None:
        """
        Generate random academic title
            Returns:
                Optional[str]: Returns a string if successful, otherwise returns None.
        """
        if self._rng.random() < self._quota:
            return self._values and self._rng.choices(self._values, self._weights, k=1)[0] or None
        else:
            return ""

    def reset(self) -> None:
        pass

    @staticmethod
    def _load_academy_csv(file_path: Path):
        values, weights = FileUtil.read_wgt_file(file_path=file_path)

        # normalize weights
        total_weight = sum(weights) if weights else 0.0
        normalized_weights = [weight / total_weight for weight in weights] if total_weight else []

        return values, normalized_weights
