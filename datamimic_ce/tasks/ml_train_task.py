# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import csv
import json
import os
from collections import OrderedDict

import pandas as pd
import xmltodict

from datamimic_ce.clients.mongodb_client import MongoDBClient
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
        dataset = self._get_data_from_source(ctx)
        if not dataset:
            raise ValueError(f"No data found for reference {self._statement.name}")

        df_data = pd.DataFrame(dataset)
        tabular_model_configuration = self._get_tabular_model_configuration()
        config = {
            "name": self._statement.name,
            "tables": [
                {
                    "name": self._statement.type,
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

    def _get_data_from_source(self, ctx: SetupContext):
        root_ctx = ctx.root
        source_type = self.statement.type or self.statement.mode
        source_str = self.statement.source
        file_path = root_ctx.descriptor_dir / source_str
        separator = self.statement.separator or root_ctx.default_separator
        source_data = None
        # TODO: accept data from all kind of source
        if source_str.endswith(".csv"):
            with file_path.open(newline="") as csvfile:
                source_data = csv.DictReader(csvfile, delimiter=separator)
        elif source_str.endswith(".json"):
            with file_path.open("r") as file:
                source_data = json.load(file)
        elif source_str.endswith(".xml"):
            with file_path.open("r") as file:
                source_data = xmltodict.parse(file.read(), attr_prefix="@", cdata_key="#text")
        elif root_ctx.memstore_manager.contain(source_str):
            source_data = root_ctx.memstore_manager.get_memstore(source_str).get_data_by_type(
                product_type=source_type, pagination=None, cyclic=False
            )
        elif root_ctx.clients.get(source_str) is not None:
            client = root_ctx.clients.get(source_str)
            if isinstance(client, MongoDBClient):
                source_data = client.get_by_page_with_type(collection_name=source_type)
            elif isinstance(client, RdbmsClient):
                source_data = client.get_by_page_with_type(table_name=source_type)
            else:
                raise ValueError(f"Cannot load data from client: {type(client).__name__}")

        return source_data

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
