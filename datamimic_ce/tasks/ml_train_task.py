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
        df_data = self._get_data_from_source(ctx)
        if df_data is None or df_data.empty:
            raise ValueError(f"No data found for reference {self._statement.name}")

        tabular_model_configuration = self._get_tabular_model_configuration()
        config = {
            "name": self._statement.name,
            "tables": [
                {
                    "name": self._statement.type or self._statement.name,
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
        """

        """
        root_ctx = ctx.root
        source_type = self.statement.type or self.statement.mode
        source_str = self.statement.source
        file_path = root_ctx.descriptor_dir / source_str
        separator = self.statement.separator or root_ctx.default_separator
        source_data = None

        # TODO: accept data from all kind of source
        if source_str.endswith(".csv"):
            source_data = pd.read_csv(file_path, delimiter=separator)
        elif source_str.endswith(".json"):
            source_data = pd.read_json(file_path)
        elif source_str.endswith(".xml"):
            # TODO: need to do this
            with file_path.open("r") as file:
                source_data = xmltodict.parse(file.read(), attr_prefix="@", cdata_key="#text")
        elif root_ctx.memstore_manager.contain(source_str):
            mem_data = root_ctx.memstore_manager.get_memstore(source_str).get_data_by_type(
                product_type=source_type, pagination=None, cyclic=False
            )
            source_data = pd.DataFrame(mem_data)
        elif root_ctx.clients.get(source_str) is not None:
            client = root_ctx.clients.get(source_str)
            database_data = []
            if isinstance(client, MongoDBClient):
                database_data = client.get_by_page_with_type(collection_name=source_type)
            elif isinstance(client, RdbmsClient):
                database_data = client.get_by_page_with_type(table_name=source_type)
            else:
                raise ValueError(f"Cannot load data from client: {type(client).__name__}")
            source_data = pd.DataFrame(database_data)
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
