# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import re

from datamimic_ce.contexts.context import Context


class StatementUtil:
    @staticmethod
    def resolve_source_entity(stmt) -> str:
        """Physical entity to READ where a name fallback is valid (RDBMS table, memstore type):
        sourceEntity -> type -> name. The single resolver for the name-fallback read families.
        """
        return stmt.source_entity or stmt.type or stmt.name

    @staticmethod
    def resolve_source_collection(stmt) -> str | None:
        """Physical entity to READ where the statement name is NOT a valid fallback (MongoDB requires
        an explicit collection): sourceEntity -> type, else None (the caller raises). The single
        resolver for the explicit-only read families.
        """
        return stmt.source_entity or stmt.type

    @staticmethod
    def resolve_target_entity(target_entity: str | None, type_: str | None, name: str) -> str:
        """Physical entity to WRITE (table/collection/basename): targetEntity -> type -> name.

        The single write-entity resolver, used by every target family (RDBMS/MongoDB exporters,
        the file-exporter basename, the memstore key). Callers pass type_=None where their family
        never routed by type (file basenames), so behaviour is unchanged without targetEntity.
        """
        return target_entity or type_ or name

    @staticmethod
    def resolve_target_entity_from_metadata(name: str, metadata: dict | None) -> str:
        """resolve_target_entity for an exporter that only has the product metadata, not the statement."""
        md = metadata or {}
        return StatementUtil.resolve_target_entity(md.get("target_entity"), md.get("type"), name)

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

    @staticmethod
    def resolve_count(count: int | None, min_count: int | None, max_count: int | None, rng) -> int | None:
        """Single source of truth for resolving an effective row count from an explicit
        count or a [minCount, maxCount] range. Shared by <generate> and <nestedKey>.

        - explicit count wins
        - none set -> None (caller falls back to source length)
        - only one bound -> a ±5 window around it
        - both -> rng.randint(min, max)
        """
        if count is not None:
            return count
        if min_count is not None and max_count is not None:
            return rng.randint(min_count, max_count)
        if max_count is not None:
            return rng.randint(max(0, max_count - 5), max_count)
        if min_count is not None:
            return rng.randint(min_count, min_count + 5)
        return None
