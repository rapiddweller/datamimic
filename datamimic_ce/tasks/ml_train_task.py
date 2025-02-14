# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import os

import pandas as pd
from datamimic_ce.contexts.setup_context import SetupContext

from datamimic_ce.clients.rdbms_client import RdbmsClient
from datamimic_ce.statements.ml_train_statement import MLTrainStatement
from datamimic_ce.tasks.task import Task
from mostlyai.sdk import MostlyAI


class MLTrainTask(Task):
    def __init__(self, statement: MLTrainStatement):
        self._statement = statement
        self._ml_dir = None

    @property
    def statement(self) -> MLTrainStatement:
        return self._statement

    def execute(self, ctx: SetupContext):
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
        max_training_time = self.get_float_train_time()
        config = {
            "name": self._statement.name,
            "tables": [
                {"name": self._statement.table,
                 "data": df_data,
                 "tabular_model_configuration": {
                     "value_protection": False,
                     "max_training_time": max_training_time
                    }
                 }
            ],
        }

        # configure a generator and save to file
        g = mostly.train(config=config, start=True, wait=True)
        # TODO: write trained model to some where
        export_dir = ctx.descriptor_dir / f"generators"
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)
        self._ml_dir = g.export_to_file(export_dir)

    def get_float_train_time(self):
        if self._statement.maxTrainingTime:
            try:
                float_value = float(self._statement.maxTrainingTime)
                return float_value
            except ValueError or TypeError:
                return None
        else:
            return None

    def __del__(self):
        """
        Deletes trained model when object is garbage collected.
        """
        try:
            if os.path.exists(self._ml_dir):
                os.remove(self._ml_dir)
        except Exception as e:
            print(f"Error deleting file {self._ml_dir}")
