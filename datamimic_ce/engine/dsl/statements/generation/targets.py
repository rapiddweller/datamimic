# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.

import re


def parse_consumer(consumer_string: str | None) -> set[str]:
    """Parse consumer targets, splitting commas outside parentheses."""
    if not consumer_string:
        return set()

    consumer_list = re.split(r",\s*(?![^(]*\))", consumer_string)
    return {consumer.strip() for consumer in consumer_list if consumer.strip()}
