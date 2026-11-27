# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
from pathlib import Path

from datamimic_ce.domains.domain_core.base_domain_generator import normalize_dataset
from datamimic_ce.domains.domain_core.base_literal_generator import BaseLiteralGenerator
from datamimic_ce.domains.domain_core.datasets.path import dataset_path
from datamimic_ce.domains.shared.datasets.loader import read_weighted_values

_StreetFileKey = tuple[Path, int, int]

# Parsed street files, keyed by resolved path plus mtime/size, so one dataset never serves another's
# rows and an edited file is re-read. Per process (workers fill their own copy); one entry per country.
_street_files: dict[_StreetFileKey, tuple[tuple[str, ...], tuple[float, ...]]] = {}


def _load_street_file(file_path: Path) -> tuple[tuple[str, ...], tuple[float, ...]]:
    try:
        stat = file_path.stat()
    except OSError:
        values, weights = read_weighted_values(file_path)  # raises the reader's own error for a missing file
        return tuple(values), tuple(weights)
    key = (file_path, stat.st_mtime_ns, stat.st_size)
    cached = _street_files.get(key)
    if cached is None:
        values, weights = read_weighted_values(file_path)
        cached = _street_files[key] = (tuple(values), tuple(weights))
    return cached


class StreetNameGenerator(BaseLiteralGenerator):
    """
    Generate random street name
    """

    def __init__(self, dataset: str | None = None, rng: random.Random | None = None):
        street_code = normalize_dataset(dataset)[:2]

        # Prepare file path
        file_path = dataset_path("common", "street", f"street_{street_code}.csv", start=Path(__file__))

        # Load file data (parsed once per file and process; the rng stays per generator)
        self._values, self._wgt = _load_street_file(file_path)
        super().__init__(rng=rng)

    def generate(self) -> str:
        """
        Generate random street name
        Returns:
            Optional[str]: Returns a string if successful, otherwise returns None.
        """
        return self._rng.choices(self._values, self._wgt, k=1)[0]
