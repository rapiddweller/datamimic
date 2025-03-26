# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
from pathlib import Path

from datamimic_ce.domain_core.base_literal_generator import BaseLiteralGenerator
from datamimic_ce.logger import logger
from datamimic_ce.utils.file_util import FileUtil


class AcademicTitleGenerator(BaseLiteralGenerator):
    """
    Generate random academic title
    """

    def __init__(self, dataset: str | None = None, quota: float = 0.5):
        if quota is None:
            quota = quota or 0.5
        elif quota > 1 or quota < 0:
            quota = 0.5
        self._quota = quota

        dataset = dataset.upper() if dataset else dataset

        sp_dataset = ("DE", "US", "IT", "CN", "FR")
        if dataset is None:
            logger.info("Academic title for dataset not set, use default Academic title")
            file_name = "domain_data/common/person/title.csv"
        elif dataset not in sp_dataset:
            logger.info(f"Academic title for dataset {dataset} is not supported, change to default Academic title")
            file_name = "domain_data/common/person/title.csv"
        else:
            file_name = f"domain_data/common/person/title_{dataset}.csv"

        file_path = Path(__file__).parent.parent.parent.parent.joinpath(file_name)
        self._values, self._weights = self._load_academy_csv(file_path)

    def generate(self) -> str | None:
        """
        Generate random academic title
            Returns:
                Optional[str]: Returns a string if successful, otherwise returns None.
        """
        if random.random() < self._quota:
            return random.choices(self._values, self._weights, k=1)[0] if self._values else None
        else:
            return ""

    def reset(self) -> None:
        pass

    @staticmethod
    def _load_academy_csv(file_path: Path):
        values, weights = FileUtil.read_wgt_file(file_path=file_path)

        # normalize weights
        total_weight = sum(weights)
        normalized_weights = [weight / total_weight for weight in weights]

        return values, normalized_weights
