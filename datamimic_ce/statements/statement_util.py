# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import re

from datamimic_ce.contexts.context import Context


class StatementUtil:
    @staticmethod
    def parse_consumer(consumer_string: str | None) -> set[str]:
        """
        Parse the 'consumer' attribute into a set of consumers.
        Splits on commas not enclosed within parentheses.
        """
        if not consumer_string:
            return set()

            # Pattern to split on commas not inside parentheses
        pattern = r",\s*(?![^(]*\))"
        consumer_list = re.split(pattern, consumer_string)

        # Strip whitespace from each consumer
        consumer_list = [consumer.strip() for consumer in consumer_list if consumer.strip()]

        # Avoid duplicated consumers
        consumer_set = set(consumer_list)

        return consumer_set

    @staticmethod
    def get_int_count(count: str | None, ctx: Context):
        """
        Evaluate count (str) and return as int value for statement

        :param count:
        :param ctx:
        :return:
        """
        if count is None:
            return None
        elif count.isdigit():
            return int(count)
        else:
            return int(ctx.evaluate_python_expression(count[1:-1]))
