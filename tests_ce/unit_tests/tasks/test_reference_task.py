# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import unittest
from unittest.mock import MagicMock

from datamimic_ce.clients.rdbms_client import RdbmsClient
from datamimic_ce.contexts.context import Context
from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination
from datamimic_ce.statements.reference_statement import ReferenceStatement
from datamimic_ce.tasks.reference_task import ReferenceTask


class TestReferenceTask(unittest.TestCase):
    def setUp(self):
        self.statement = MagicMock(spec=ReferenceStatement)
        self.statement.source = "test_source"
        self.statement.source_type = "test_type"
        self.statement.source_key = "test_key"
        self.statement.name = "test_name"
        self.pagination = MagicMock(spec=DataSourcePagination)
        self.pagination.limit = 2
        self.context = MagicMock(spec=Context)
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

    def test_execute_non_rdbms_client(self):
        """Test execution with non-RDBMS client."""
        self.context.root.clients.get.return_value = MagicMock()  # Not an RdbmsClient
        task = ReferenceTask(self.statement)

        with self.assertRaises(ValueError) as context:
            task.execute(self.context)

        self.assertEqual(str(context.exception), "Reference task currently only supports RDBMS data sources")

    def test_execute_empty_dataset(self):
        """Test execution with empty dataset."""
        self.rdbms_client.get_random_rows_by_column.return_value = []
        task = ReferenceTask(self.statement)

        with self.assertRaises(ValueError) as context:
            task.execute(self.context)

        self.assertEqual(str(context.exception), "No data found for reference test_name")

    def test_execute_unique_values(self):
        """Test execution with unique values requirement."""
        self.statement.unique = True
        dataset = [1, 2, 3, 4, 5]
        self.rdbms_client.get_random_rows_by_column.return_value = dataset
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
        self.rdbms_client.get_random_rows_by_column.return_value = dataset
        task = ReferenceTask(self.statement)

        result = task.execute(self.context)
        self.assertIn(result, dataset)

    def test_execute_unique_values_insufficient_data(self):
        """Test execution with unique values requirement but insufficient data."""
        self.statement.unique = True
        self.pagination.limit = 5
        dataset = [1, 2, 3]  # Only 3 values available
        self.rdbms_client.get_random_rows_by_column.return_value = dataset
        task = ReferenceTask(self.statement, self.pagination)

        with self.assertRaises(RuntimeError) as context:
            task.execute(self.context)

        self.assertIn("Cannot generate 5 unique values - only 3 available", str(context.exception))

    def test_execute_with_context_field_addition(self):
        """Test execution with context that supports field addition."""
        self.statement.unique = False
        dataset = [42]
        self.rdbms_client.get_random_rows_by_column.return_value = dataset
        self.context.add_current_product_field = MagicMock()

        task = ReferenceTask(self.statement)
        result = task.execute(self.context)

        self.assertEqual(result, 42)
        self.context.add_current_product_field.assert_called_once_with("test_name", 42)


if __name__ == "__main__":
    unittest.main()
