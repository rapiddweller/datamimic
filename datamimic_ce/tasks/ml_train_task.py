# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import os

import pandas as pd
from mostlyai.sdk import MostlyAI

from datamimic_ce.clients.rdbms_client import RdbmsClient
from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.statements.ml_train_statement import MLTrainStatement
from datamimic_ce.tasks.task import Task


class MLTrainTask(Task):
    def __init__(self, statement: MLTrainStatement):
        self._statement = statement
        self._ml_dir = None
        self._ml_export_name = statement.name
        self._mode = statement.mode

    @property
    def statement(self) -> MLTrainStatement:
        return self._statement

    def execute(self, ctx: SetupContext):
        mostly = MostlyAI(local=True)
        # Retrieving values from an RDBMS data source
        client = ctx.root.clients.get(self.statement.source)
        if not isinstance(client, RdbmsClient):
            raise ValueError("Reference task currently only supports RDBMS data sources")
        dataset = client.get_by_page_with_type(table_name=self._statement.table)
        if not dataset:
            raise ValueError(f"No data found for reference {self._statement.name}")

        df_data = pd.DataFrame(dataset)
        tabular_model_configuration = self._get_tabular_model_configuration()
        config = {
            "name": self._statement.name,
            "tables": [
                {
                    "name": self._statement.table,
                    "data": df_data,
                    "tabular_model_configuration": tabular_model_configuration,
                }
            ],
        }

        # train model and save file in generators folder
        g = mostly.train(config=config, start=True, wait=True)
        export_dir = ctx.descriptor_dir / "generators"
        if not os.path.exists(export_dir):
            os.makedirs(export_dir)
        self._ml_dir = g.export_to_file(f"{export_dir}/{self._ml_export_name}.zip")

    def _get_tabular_model_configuration(self) -> dict:
        tabular_model_configuration: dict[str, bool | float | str] = {"value_protection": False}
        max_training_time: float | None = None
        if self._statement.maxTrainingTime:
            try:
                float_value = float(self._statement.maxTrainingTime)
                max_training_time = float_value
            except ValueError:
                max_training_time = None
            except TypeError:
                max_training_time = None

        if max_training_time is not None:
            tabular_model_configuration["max_training_time"] = max_training_time
        return tabular_model_configuration

    def __del__(self):
        """
        Deletes trained model when object is garbage collected.
        """
        if self._mode != "persist":
            try:
                if os.path.exists(self._ml_dir):
                    os.remove(self._ml_dir)
            except Exception:
                print(f"Error deleting file {self._ml_dir}")
