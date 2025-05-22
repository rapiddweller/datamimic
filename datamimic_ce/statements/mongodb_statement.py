# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.clients.mongodb_client import MongoDBClient
from datamimic_ce.connection_config.mongodb_connection_config import MongoDBConnectionConfig
from datamimic_ce.model.mongodb_model import MongoDBModel
from datamimic_ce.statements.statement import Statement


class MongoDBStatement(Statement):
import json # Required for parsing JSON strings
from typing import Any, Dict, List, Optional

from datamimic_ce.clients.mongodb_client import MongoDBClient
from datamimic_ce.connection_config.mongodb_connection_config import MongoDBConnectionConfig
from datamimic_ce.model.mongodb_model import MongoDBModel
from datamimic_ce.statements.statement import Statement


class MongoDBStatement(Statement):
    def __init__(
        self, 
        model: MongoDBModel,
        # Adding parsed structured query components
        operation_type: Optional[str] = None,
        collection_name: Optional[str] = None,
        filter_dict: Optional[Dict[str, Any]] = None,
        projection_dict: Optional[Dict[str, Any]] = None,
        pipeline_list: Optional[List[Dict[str, Any]]] = None
    ):
        super().__init__(model.id, None) # Assuming 'id' from model is the statement name
        self._model = model
        self._mongodb_connection_config = MongoDBConnectionConfig(**model.model_dump(exclude_none=True))
        self._mongodb_client = MongoDBClient(self._mongodb_connection_config)
        
        self.operation_type = operation_type
        self.collection_name = collection_name
        self.filter_dict = filter_dict
        self.projection_dict = projection_dict
        self.pipeline_list = pipeline_list

    @property
    def mongodb_id(self) -> str: # Added type hint
        return self._model.id

    @property
    def mongodb_connection_config(self) -> MongoDBConnectionConfig: # Added type hint
        return self._mongodb_connection_config

    @property
    def client(self) -> MongoDBClient: # Provide access to the client
        return self._mongodb_client

    # Add properties for new structured query components
    @property
    def operation(self) -> Optional[str]:
        return self.operation_type

    @property
    def collection(self) -> Optional[str]:
        return self.collection_name

    @property
    def filter(self) -> Optional[Dict[str, Any]]:
        return self.filter_dict

    @property
    def projection(self) -> Optional[Dict[str, Any]]:
        return self.projection_dict

    @property
    def pipeline(self) -> Optional[List[Dict[str, Any]]]:
        return self.pipeline_list

    def __repr__(self) -> str:
        return (
            f"MongoDBStatement(id={self.mongodb_id}, operation='{self.operation_type}', "
            f"collection='{self.collection_name}', ...)"
        )
