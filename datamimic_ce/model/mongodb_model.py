# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from pydantic import BaseModel, ConfigDict, field_validator

from datamimic_ce.model.model_util import ModelUtil


class MongoDBModel(BaseModel):
    id: str
    host: str
    port: str
    database: str
    environment: str | None = None
    user: str | None = None
    password: str | None = None

    # New attributes for structured queries
    operation_type: str | None = None  # 'find' or 'aggregate'
    collection_name: str | None = None # Target collection
    filter_json: str | None = None     # JSON string for find's filter
    projection_json: str | None = None # JSON string for find's projection
    pipeline_json: str | None = None   # JSON string for aggregate's pipeline

    model_config = ConfigDict(extra="allow")

    # @model_validator(mode="before")
    # @classmethod
    # def check_database_valid_attributes(cls, values: Dict):
    #     return ModelUtil.check_valid_attributes(
    #         values=values,
    #         valid_attributes={
    #             ATTR_ID,
    #             ATTR_HOST,
    #             ATTR_PORT,
    #             ATTR_DATABASE,
    #             ATTR_USER,
    #             ATTR_PASSWORD,
    #             ATTR_SYSTEM,
    #             ATTR_ENVIRONMENT,
    #         },
    #     )

    @field_validator("id", "host", "port", "database")
    @classmethod
    def validate_connection_fields(cls, value): # Renamed for clarity
        return ModelUtil.check_not_empty(value=value)

    @field_validator("port")
    @classmethod
    def validate_port_format(cls, value): # Renamed for clarity
        return ModelUtil.check_is_digit(value=value)
    
    @field_validator("operation_type")
    @classmethod
    def validate_operation_type(cls, value: str | None):
        if value is not None and value not in ("find", "aggregate"):
            raise ValueError("operation_type must be 'find' or 'aggregate'")
        return value

    # Validators for collection_name based on operation_type
    @field_validator("collection_name")
    @classmethod
    def validate_collection_name_presence(cls, value: str | None, values):
        # This validator depends on 'operation_type' being processed first or available.
        # Pydantic v2 runs field validators in order of field definition.
        # If operation_type is defined, collection_name must also be defined.
        data = values.data # Pydantic v2 way to access other field values
        if data.get("operation_type") and not value:
            raise ValueError("collection_name is required if operation_type is specified")
        if value: # If collection_name is provided, ensure it's not empty
            return ModelUtil.check_not_empty(value=value)
        return value

    # Further validation can be added in a model_validator if there are cross-field dependencies
    # e.g., if operation_type is 'find', then filter_json might be mandatory (though currently MongoDBClient handles default empty filter)
    # if operation_type is 'aggregate', then pipeline_json is mandatory.
    # For now, these are kept optional at Pydantic model level, client will handle errors if essential parts are missing.
