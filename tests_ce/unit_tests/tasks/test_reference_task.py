# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
import unittest
from random import Random
from unittest.mock import MagicMock, patch

from datamimic_ce.clients.rdbms_client import RdbmsClient
from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination
from datamimic_ce.statements.reference_statement import ReferenceStatement
from datamimic_ce.tasks.reference_task import ReferenceTask


class TestReferenceTask(unittest.TestCase):
    def setUp(self):
        self.statement = MagicMock(spec=ReferenceStatement)
        self.statement.source = "test_source"
        self.statement.source_type = "test_type"
        self.statement.source_key = "test_key"
        self.statement.source_keys = ["test_key"]
        self.statement.targets = ["test_name"]
        self.statement.is_composite = False
        self.statement.name = "test_name"
        # No selection modifier: default with-replacement path (spec-mocked attrs are truthy otherwise).
        self.statement.distribution = None
        self.statement.cyclic = None
        self.pagination = MagicMock(spec=DataSourcePagination)
        self.pagination.limit = 2
        self.pagination.skip = 0
        self.context = MagicMock(spec=GenIterContext)
        # ReferenceTask reads ctx.rng directly; the random module exposes the
        # same callable API as a Random instance, so it works as a drop-in.
        self.context.rng = random
        # unique selection routes via DataSourceRegistry.get_unique_data (stable per-statement seed).
        self.context.root.stable_distribution_seed.return_value = 42
        self.rdbms_client = MagicMock(spec=RdbmsClient)
        self.context.root.clients.get.return_value = self.rdbms_client

    def test_init(self):
        """Test initialization of ReferenceTask."""
        task = ReferenceTask(self.statement)
        self.assertEqual(task.statement, self.statement)
        self.assertIsNone(task._pagination)
        self.assertIsNone(task._iterator)

        task_with_pagination = ReferenceTask(self.statement, self.pagination)
        self.assertEqual(task_with_pagination._pagination, self.pagination)

    def test_execute_unsupported_client(self):
        """A source that is neither an RDBMS nor a MongoDB client is rejected with a
        message naming the reference and both supported client kinds."""
        self.context.root.clients.get.return_value = MagicMock()  # neither Rdbms nor MongoDB
        task = ReferenceTask(self.statement)

        with self.assertRaises(ValueError) as context:
            task.execute(self.context)

        message = str(context.exception)
        self.assertIn("RDBMS and MongoDB are supported", message)

    def test_execute_empty_dataset(self):
        """Test execution with empty dataset."""
        self.rdbms_client.get_random_rows_by_columns.return_value = []
        task = ReferenceTask(self.statement)

        with self.assertRaises(ValueError) as context:
            task.execute(self.context)

        self.assertEqual(str(context.exception), "No data found for reference test_name")

    def test_execute_unique_values(self):
        """Test execution with unique values requirement."""
        self.statement.unique = True
        dataset = [1, 2, 3, 4, 5]
        self.rdbms_client.get_random_rows_by_columns.return_value = [(v,) for v in dataset]
        task = ReferenceTask(self.statement, self.pagination)

        # First execution
        result1 = task.execute(self.context)
        self.assertIn(result1, dataset)

        # Second execution
        result2 = task.execute(self.context)
        self.assertIn(result2, dataset)
        self.assertNotEqual(result1, result2)  # Values should be unique

    def test_execute_non_unique_values(self):
        """Test execution without unique values requirement."""
        self.statement.unique = False
        dataset = [1, 2, 3]
        self.rdbms_client.get_random_rows_by_columns.return_value = [(v,) for v in dataset]
        task = ReferenceTask(self.statement)

        result = task.execute(self.context)
        self.assertIn(result, dataset)

    def test_execute_unique_values_insufficient_data(self):
        """Test execution with unique values requirement but insufficient data."""
        self.statement.unique = True
        self.pagination.limit = 5
        dataset = [1, 2, 3]  # Only 3 values available
        self.rdbms_client.get_random_rows_by_columns.return_value = [(v,) for v in dataset]
        task = ReferenceTask(self.statement, self.pagination)

        with self.assertRaises(ValueError) as context:
            task.execute(self.context)

        self.assertIn("Cannot generate 5 unique values", str(context.exception))

    def test_seeded_rng_makes_reference_replay_identically(self):
        """<reference> picks must replay byte-identically when ctx.rng is seeded.

        Stands in for a full DSL-level reference scenario (which requires RDBMS
        scaffolding). Locks in that ReferenceTask honours ctx.rng for both the
        unique (rng.sample) and non-unique (rng.choice) paths.
        """
        dataset = list(range(20))
        self.rdbms_client.get_random_rows_by_columns.return_value = [(v,) for v in dataset]

        def _collect(unique: bool) -> list:
            self.statement.unique = unique
            picks: list = []
            for _ in range(2):
                self.context.rng = Random(42)
                task = ReferenceTask(self.statement, self.pagination)
                picks.append(task.execute(self.context))
            return picks

        unique_picks = _collect(True)
        self.assertEqual(unique_picks[0], unique_picks[1])
        non_unique_picks = _collect(False)
        self.assertEqual(non_unique_picks[0], non_unique_picks[1])

    def test_execute_with_context_field_addition(self):
        """Test execution with context that supports field addition."""
        self.statement.unique = False
        dataset = [42]
        self.rdbms_client.get_random_rows_by_columns.return_value = [(v,) for v in dataset]
        self.context.add_current_product_field = MagicMock()

        task = ReferenceTask(self.statement)
        result = task.execute(self.context)

        self.assertEqual(result, 42)
        self.context.add_current_product_field.assert_called_once_with("test_name", 42)

    def test_task_delegates_loading_mapping_and_selection_to_registry(self):
        """ReferenceTask owns iteration/context mutation, not datasource policy."""
        selected = [{"test_name": 17}, {"test_name": 23}]
        task = ReferenceTask(self.statement, self.pagination)

        with patch(
            "datamimic_ce.tasks.reference_task.DataSourceRegistry.load_reference_source",
            return_value=selected,
        ) as load_reference_source:
            assert task.execute(self.context) == 17
            assert task.execute(self.context) == 23

        load_reference_source.assert_called_once_with(self.context, self.statement, self.pagination)
        self.rdbms_client.get_random_rows_by_columns.assert_not_called()


if __name__ == "__main__":
    unittest.main()
