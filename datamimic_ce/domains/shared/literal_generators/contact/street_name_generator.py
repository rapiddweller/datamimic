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

_StreetRows = tuple[tuple[str, ...], tuple[float, ...]]

# Parsed street files, keyed by resolved path; each entry carries the (mtime, size) it was parsed at, so one
# dataset never serves another's rows and an edited file replaces its old entry. Per process (workers fill
# their own copy); at most one entry per path.
_street_files: dict[Path, tuple[tuple[int, int], _StreetRows]] = {}


def _load_street_file(file_path: Path) -> _StreetRows:
    try:
        stat = file_path.stat()
    except OSError:
        values, weights = read_weighted_values(file_path)  # raises the reader's own error for a missing file
        return tuple(values), tuple(weights)
    stamp = (stat.st_mtime_ns, stat.st_size)
    cached = _street_files.get(file_path)
    if cached is None or cached[0] != stamp:
        values, weights = read_weighted_values(file_path)
        cached = _street_files[file_path] = (stamp, (tuple(values), tuple(weights)))
    return cached[1]


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
