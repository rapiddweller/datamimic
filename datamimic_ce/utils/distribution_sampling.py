# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random


def cumulated_index(rng: random.Random, span: int) -> int:
    """Benerator 'cumulated' sampler: index in [0, span] with a symmetric bell shape,
    mean = span/2, both endpoints reachable (rarely on wide spans).

    Mean of 5 uniform draws (Irwin-Hall n=5); the +2 rounds the integer //5. Exactly
    mirrors com.rapiddweller.benerator...CumulatedLongGenerator. Shared by the numeric
    literal generators (value = min + index*granularity) and source-row selection
    (data[index]).
    """
    return (sum(rng.randint(0, span) for _ in range(5)) + 2) // 5
