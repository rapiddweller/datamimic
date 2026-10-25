# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.

from datamimic_ce.engine.dsl.vocabulary.enums.operation_enums import split_targets


def parse_consumer(consumer_string: str | None) -> set[str]:
    """Parse consumer targets, splitting commas outside parentheses."""
    return set(split_targets(consumer_string))
