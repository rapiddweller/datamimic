# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from pathlib import Path
from xml.etree.ElementTree import Element

from datamimic_ce.constants.element_constants import EL_MONGODB
import json # For parsing JSON strings
import re   # For variable substitution
from pathlib import Path
from xml.etree.ElementTree import Element
from typing import Any, Dict, List, Optional, cast


from datamimic_ce.constants.element_constants import EL_MONGODB
from datamimic_ce.model.mongodb_model import MongoDBModel
from datamimic_ce.parsers.parser_util import ParserUtil # Already has this
from datamimic_ce.parsers.statement_parser import StatementParser
from datamimic_ce.statements.mongodb_statement import MongoDBStatement
from datamimic_ce.logger import logger # For logging issues


class MongoDBParser(StatementParser):
    """
    Parse element "mongodb" into MongoDBStatement
    """

    def __init__(
        self,
        element: Element,
        properties: dict,
    ):
        super().__init__(
            element,
            properties,
            valid_element_tag=EL_MONGODB,
        )

    def parse(self, descriptor_dir: Path) -> MongoDBStatement:
        """
        Parse element "mongodb" into MongoDBStatement
        :return:
        """
        mongodb_attributes = ParserUtil.fulfill_credentials(
            descriptor_dir=descriptor_dir,
            descriptor_attr=self._element.attrib,
            env_props=self.properties,
            system_type="mongo",
        )

        return MongoDBStatement(
            model=validated_model,
            operation_type=validated_model.operation_type,
            collection_name=validated_model.collection_name,
            filter_dict=filter_dict,
            projection_dict=projection_dict,
            pipeline_list=pipeline_list,
        )

    def _evaluate_json_string_content(self, json_str: Optional[str], context_vars: Dict[str, Any]) -> Optional[str]:
        """
        Evaluates variables like ${var} within the given JSON string.
        """
        if json_str is None:
            return None

        # Pattern to find ${variable_name}
        pattern = r"\$\{(.*?)\}"

        def replace_var(match):
            var_name = match.group(1)
            return str(context_vars.get(var_name, match.group(0))) # Keep original if var not found

        return re.sub(pattern, replace_var, json_str)


    def _parse_json_string(self, json_str: Optional[str], field_name: str, statement_id: str) -> Optional[Any]:
        """
        Parses a JSON string into a Python object (dict or list).
        """
        if json_str is None:
            return None
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON for field '{field_name}' in MongoDB statement ID '{statement_id}': {e}\nJSON string was: {json_str}")
            raise ValueError(f"Invalid JSON in field '{field_name}' for MongoDB statement ID '{statement_id}'.") from e

    def parse(self, descriptor_dir: Path) -> MongoDBStatement:
        """
        Parse element "mongodb" into MongoDBStatement, including new structured query attributes.
        :return: MongoDBStatement
        """
        # Fulfill credentials and basic attributes first
        # Note: `self.properties` here are environment properties from CLI/platform, not full context
        mongodb_attributes_raw = ParserUtil.fulfill_credentials(
            descriptor_dir=descriptor_dir,
            descriptor_attr=self._element.attrib,
            env_props=self.properties, # These are env properties
            system_type="mongo",
        )

        # Validate core model attributes (connection details, new string fields for queries)
        validated_model = self.validate_attributes(model=MongoDBModel, fulfilled_credentials=mongodb_attributes_raw)
        
        # Initialize structured query components to None
        filter_dict: Optional[Dict[str, Any]] = None
        projection_dict: Optional[Dict[str, Any]] = None
        pipeline_list: Optional[List[Dict[str, Any]]] = None

        # Evaluate content of JSON strings for variables using self.properties as context
        # For a richer context (functions, etc.), a full SetupContext/GenIterContext would be needed here.
        # This simplified evaluation uses the 'properties' dict passed to the parser.
        
        evaluated_filter_json = self._evaluate_json_string_content(validated_model.filter_json, self.properties)
        evaluated_projection_json = self._evaluate_json_string_content(validated_model.projection_json, self.properties)
        evaluated_pipeline_json = self._evaluate_json_string_content(validated_model.pipeline_json, self.properties)

        # Parse the (potentially variable-resolved) JSON strings
        if validated_model.operation_type == "find":
            if not validated_model.collection_name:
                 raise ValueError(f"MongoDB 'find' operation for ID '{validated_model.id}' requires 'collection_name'.")
            # filter_json is technically optional for find (empty filter), but if provided, must be valid JSON
            filter_dict = self._parse_json_string(evaluated_filter_json, "filter_json", validated_model.id) or {} # Default to empty dict
            if evaluated_projection_json: # Projection is optional
                projection_obj = self._parse_json_string(evaluated_projection_json, "projection_json", validated_model.id)
                if not isinstance(projection_obj, dict) and projection_obj is not None: # Ensure it's a dict if provided
                    raise ValueError(f"Parsed 'projection_json' for MongoDB ID '{validated_model.id}' must be a dictionary.")
                projection_dict = cast(Optional[Dict[str, Any]], projection_obj)

        elif validated_model.operation_type == "aggregate":
            if not validated_model.collection_name:
                 raise ValueError(f"MongoDB 'aggregate' operation for ID '{validated_model.id}' requires 'collection_name'.")
            if not evaluated_pipeline_json:
                raise ValueError(f"MongoDB 'aggregate' operation for ID '{validated_model.id}' requires 'pipeline_json'.")
            
            pipeline_obj = self._parse_json_string(evaluated_pipeline_json, "pipeline_json", validated_model.id)
            if not isinstance(pipeline_obj, list):
                raise ValueError(f"Parsed 'pipeline_json' for MongoDB ID '{validated_model.id}' must be a list.")
            pipeline_list = cast(List[Dict[str, Any]], pipeline_obj)
        
        elif validated_model.operation_type is None and validated_model.id:
            # This could be a connection-only definition, no operation specified at this element level.
            # It might be used by a <generate source="mongo_id_conn_only"> statement which then specifies the query.
            # In this case, filter_dict, etc., remain None.
            logger.debug(f"MongoDB statement ID '{validated_model.id}' defined without specific operation. Assumed connection definition.")
        elif validated_model.id : # operation_type is something else or other attributes are there
             pass # Allow for connection-only definitions or future types. Client will validate if operation components are sufficient.


        return MongoDBStatement(
            model=validated_model,
            operation_type=validated_model.operation_type,
            collection_name=validated_model.collection_name,
            filter_dict=filter_dict,
            projection_dict=projection_dict,
            pipeline_list=pipeline_list,
        )
