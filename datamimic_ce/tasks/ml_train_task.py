# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import pandas as pd

from datamimic_ce.clients.rdbms_client import RdbmsClient

from datamimic_ce.contexts.context import Context
from datamimic_ce.statements.ml_train_statement import MLTrainStatement
from datamimic_ce.tasks.task import Task
from mostlyai.sdk import MostlyAI


class MLTrainTask(Task):
    def __init__(self, statement: MLTrainStatement):
        self._statement = statement

    def execute(self, ctx: Context):
        mostly = MostlyAI(local=True)
        # TODO: get data here
        # Retrieving values from an RDBMS data source
        client = ctx.root.clients.get(self.statement.source)
        if not isinstance(client, RdbmsClient):
            raise ValueError("Reference task currently only supports RDBMS data sources")
        dataset = client.get_by_page_with_type(table_name=self._statement.table)
        if not dataset:
            raise ValueError(f"No data found for reference {self._statement.name}")

        df_data = pd.DataFrame(dataset)

        config = {
            "name": self._statement.name,
            "tables": [
                {"name": self._statement.table,
                 "data": df_data,
                 "tabular_model_configuration": {
                     "value_protection": False,
                     # "max_training_time": self._statement.get_float_train_time(ctx)
                     "max_training_time": 1
                 }
                 }
            ],
        }

        # configure a generator, but don't yet start the training thereof
        g = mostly.train(config=config, start=True, wait=True)
        df_samples = mostly.probe(g, size=1_000)
        print(df_samples)
        # TODO: write trained model to some where

    @property
    def statement(self) -> MLTrainStatement:
        return self._statement
