# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import json
import re
from collections.abc import Mapping
from typing import Any, cast

from pymongo import MongoClient, UpdateOne

from datamimic_ce.clients.database_client import DatabaseClient
from datamimic_ce.credentials.mongodb_credential import MongoDBCredential
from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination


class MongoDBClient(DatabaseClient):
    def __init__(self, credential: MongoDBCredential):
        self._credential = credential

    def _create_connection(self) -> MongoClient:
        ars = {
            "host": self._credential.host,
            "port": self._credential.port,
            "username": self._credential.user,
            "password": self._credential.password,
        }

        # Add authSource and authMechanism if they are in credential
        cred_dump = self._credential.model_dump()
        if "authSource" in cred_dump:
            ars["authSource"] = cred_dump["authSource"]
        if "authMechanism" in cred_dump:
            ars["authMechanism"] = cred_dump["authMechanism"]

        return MongoClient(**ars)

    def get(self, query: str) -> list:
        """
        Get documents from collection
        :param query:
        :return:
        """
        with self._create_connection() as conn:
            query_type = self._check_query_type(query=query)
            if query_type == "find":
                db = conn[self._credential.database]
                find_query = self._decompose_find_query(query)
                collection_name = find_query.get("find")
                find_filter = find_query.get("filter")
                # TODO: Validate find_filter syntax
                find_projection = find_query.get("projection")
                if collection_name is not None and not collection_name.isspace():
                    collection = db[collection_name]
                else:
                    raise ValueError(f"Syntax error: collection name '{collection_name}' not found")
                return list(collection.find(find_filter, find_projection))
            elif query_type == "aggregate":
                query_result = self._query_aggregate_handler(query=query, connection=conn)
                return query_result
            else:
                raise ValueError("Currently Mongodb selector only support 'find' and 'aggregate'")

    def get_by_page_with_query(self, query: str, pagination: DataSourcePagination | None = None) -> list:
        """
        Get documents from MongoDB collection when there is a query by pagination
        :param query:
        :param pagination:
        :return:
        """
        # TODO: cache queried result for better performance
        docs = self.get(query)
        if pagination is None:
            return docs
        else:
            skip = pagination.skip
            limit = pagination.limit
            result = docs[skip : (skip + limit)]
            return result

    def get_by_page_with_type(self, collection_name: str, pagination: DataSourcePagination | None = None) -> list:
        """
        Get documents from MongoDB collection when 'type' (name of collection) is defined by pagination
        :param collection_name:
        :param pagination:
        :return:
        """
        # TODO: cache queried result for better performance
        docs = self.get_documents_by_collection(collection_name)
        if pagination is None:
            return docs
        else:
            skip = pagination.skip
            limit = pagination.limit
            result = docs[skip : (skip + limit)]
            return result

    def get_documents_by_collection(self, collection_name: str) -> list:
        """
        Get all documents in collection
        :param collection_name:
        :return:
        """
        with self._create_connection() as conn:
            db = conn[self._credential.database]
            if collection_name is not None and not collection_name.isspace():
                collection = db[collection_name]
            else:
                raise ValueError(f"Syntax error: collection name '{collection_name}' not found")
            return list(collection.find({}))

    def count(self, collection_name: str) -> int:
        """
        Count number of documents in collection
        :param collection_name:
        :return:
        """
        with self._create_connection() as conn:
            db = conn[self._credential.database]
            if collection_name is not None and not collection_name.isspace():
                collection = db[collection_name]
            else:
                raise ValueError(f"Syntax error: collection name '{collection_name}' not found")
            return collection.count_documents({})

    def count_query_length(self, query: str) -> int:
        """
        Count number of documents in collection
        :param query:
        :return:
        """
        with self._create_connection() as conn:
            query_type = self._check_query_type(query=query)
            if query_type == "find":
                db = conn[self._credential.database]
                find_query = self._decompose_find_query(query)
                collection_name = find_query.get("find")
                find_filter = find_query.get("filter")
                # TODO: Validate find_filter syntax
                if collection_name is not None and not collection_name.isspace():
                    collection = db[collection_name]
                else:
                    raise ValueError(f"Syntax error: collection name '{collection_name}' not found")
                return collection.count_documents(cast(Mapping[str, Any], find_filter))
            elif query_type == "aggregate":
                query_result = self._query_aggregate_handler(query=query, connection=conn)
                return len(query_result)
            else:
                raise ValueError("Currently Mongodb selector only support 'find' and 'aggregate'")

    def _query_aggregate_handler(self, query: str, connection: MongoClient) -> list:
        """
        Execute mongodb aggregate query
        This function help decompose aggregate query
        then execute it and return the list of collection's documents as result
        :return: list of documents
        """
        # Decompose aggregate query
        db = connection[self._credential.database]
        aggregate_query = self._decompose_aggregate_query(query)
        collection_name = aggregate_query.get("aggregate")
        aggregate_pipeline = aggregate_query.get("pipeline")
        # validate pipeline value
        if not isinstance(aggregate_pipeline, list):
            raise ValueError("Syntax error: pipeline value must be a list")
        # support multiprocessing working properly: add $sort if pipeline don't have
        if all(operation.get("$sort") is None for operation in aggregate_pipeline):
            aggregate_pipeline.append({"$sort": {"_id": 1}})
        # validate collection name and get MongoDB collection
        if collection_name is not None and not collection_name.isspace():
            collection = db[collection_name]
        else:
            raise ValueError(f"Syntax error: collection name '{collection_name}' not found")
        if not isinstance(aggregate_pipeline, list):
            raise ValueError("Syntax error: pipeline must be a list")
        # execute and return result
        return list(collection.aggregate(aggregate_pipeline))

    def count_table_length(self, table_name: str):
        pass

    def insert(self, collection_name: str, data: list, is_update: bool):
        """
        Insert data into collection
        :param collection_name:
        :param data:
        """
        if collection_name is None or collection_name.isspace():
            raise ValueError(f"Syntax error: collection name '{collection_name}' not found")
        with self._create_connection() as conn:
            db = conn[self._credential.database]
            collection = db[collection_name]
            inserted_ids = collection.insert_many(data).inserted_ids
            # Retrieve all the inserted data
            return list(collection.find({"_id": {"$in": inserted_ids}})) if is_update else None

    def update(self, query: dict, data: list) -> int:
        """
        Update data in collection
        :param query:
        :param data:
        :return: The number of documents matched for an update.
        """
        if "selector" in query:
            value = query.get("selector")
            if value is None or value.isspace():
                raise ValueError("Syntax error: selector is not found")
            find_query = self._decompose_find_query(value)
            collection_name = find_query.get("find")
        elif "type" in query:
            collection_name = query.get("type")
        else:
            raise ValueError("'type' or 'selector' statement's attribute is missing")
        if data:
            if collection_name is None or collection_name.isspace():
                raise ValueError(f"Syntax error: collection name '{collection_name}' not found")
            with self._create_connection() as conn:
                db = conn[self._credential.database]
                collection = db[collection_name]
                operation = [UpdateOne({"_id": d["_id"]}, {"$set": d}) for d in data]
                result = collection.bulk_write(operation)
                return result.matched_count
        else:
            return 0

    def upsert(self, selector_dict: dict, updated_data: list[dict]) -> list:
        """
        Get value inside selector of query, merge it with data, then insert into database
        :param collection_name:
        :param selector_dict:
        :param updated_data:
        :return: merged data
        """
        if "selector" in selector_dict:
            selector_value = selector_dict.get("selector")
            if selector_value is None or selector_value.isspace():
                raise ValueError("Syntax error: selector is not found")
            find_query = self._decompose_find_query(selector_value)
            collection_name = find_query.get("find")
            filter_query = find_query["filter"]
        # TODO: handle upsert for mongodb having no attribute selector
        # elif "type" in selector_dict:
        #     collection_name = selector_dict.get("type")
        else:
            raise ValueError("'type' or 'selector' statement's attribute is missing")
        # query = self._decompose_find_query(selector)

        # Merge updated_data and filter query
        updated_data = [{**filter_query, **data} for data in updated_data]

        if collection_name is None or collection_name.isspace():
            raise ValueError(f"Syntax error: collection name '{collection_name}' not found")
        # Write new data to database in case no data found by query
        if updated_data[0].get("_id") is None:
            return self.insert(collection_name, updated_data, True)
        # Update data in database
        else:
            with self._create_connection() as conn:
                db = conn[self._credential.database]
                collection = db[collection_name]
                for doc in updated_data:
                    filter = {"_id": doc["_id"]}
                    update = {"$set": doc}
                    collection.update_one(filter, update, upsert=True)
                # Return updated data
                return list(collection.find({"_id": {"$in": [doc["_id"] for doc in updated_data]}}))

    def _decompose_find_query(self, query: str) -> dict:
        """
        Decompose query from selector statement into database collection name, filter, and projection
        :param query:
        :return: dict-keys: find, filter, projection
        """
        self._validate_query_command(query)
        # change mongodb query into JSON string
        input_query = query.replace("'", '"')
        input_query = re.sub(r"\s*find\s*:", r'"find":', input_query)
        input_query = re.sub(r"\s*filter\s*:", r'"filter":', input_query)
        input_query = re.sub(r"\s*projection\s*:", r'"projection":', input_query)
        input_query = f"{{{input_query}}}"
        # check and return query as dict
        try:
            result = json.loads(input_query)
            if result.get("find") is None:
                raise ValueError("Wrong query syntax 'find' component not found")
            elif result.get("filter") is None:
                raise ValueError("Wrong query syntax 'filter' component not found")
            else:
                return result
        except Exception as err:
            raise ValueError(f"Wrong mongodb selector syntax: {query}, error: {err}") from err

    def _decompose_aggregate_query(self, query: str) -> dict:
        """
        Decompose query from selector statement into database collection name, pipeline
        :param query:
        :return: dict-keys:  name, pipeline
        """
        self._validate_query_command(query)
        # change mongodb query into JSON string
        input_query = query.replace("'", '"')
        input_query = re.sub(r"(?<!\")\s*aggregate\s*:(?!\")", r'"aggregate":', input_query)
        input_query = re.sub(r"(?<!\")\s*pipeline\s*:(?!\")", r'"pipeline":', input_query)
        input_query = f"{{{input_query}}}"
        # check and return query as dict
        try:
            result = json.loads(input_query)
            if result.get("aggregate") is None:
                raise ValueError("Wrong query syntax 'aggregate' component not found")
            elif result.get("pipeline") is None:
                raise ValueError("Wrong query syntax 'pipeline' component not found")
            else:
                return result
        except Exception as err:
            raise ValueError(f"Wrong mongodb selector syntax: {query}, error: {err}") from err

    @staticmethod
    def _validate_query_command(query: str):
        """
        validate query string
        'find' query have elements: 'find', 'filter', 'projection'
        'aggregate' query have elements: 'aggregate', 'pipeline'
        :param query:
        """
        # validate find
        query = query.strip()
        find_match = re.findall(r"find\s*:", query)
        aggregate_match = re.findall(r"aggregate\s*:", query)
        if find_match and aggregate_match:
            raise ValueError("Error syntax, only one query type allow but found both 'find' and 'aggregate'")
        if find_match:
            find_count = len(find_match) if find_match else 0
            if find_count > 1:
                raise ValueError(f"Error syntax, only 1 'find' allow but found {find_count}")
            # validate filter
            filter_match = re.findall(r"filter\s*:", query)
            filter_count = len(filter_match) if filter_match else 0
            if filter_count > 1:
                raise ValueError(f"Error syntax, only 1 'filter' allow but found {filter_count}")
            # validate projection
            projection_match = re.findall(r"projection\s*:", query)
            projection_count = len(projection_match) if projection_match else 0
            if projection_count > 1:
                raise ValueError(f"Error syntax, only 1 'projection' allow but found {projection_count}")
        elif aggregate_match:
            aggregate_count = len(aggregate_match) if aggregate_match else 0
            if aggregate_count > 1:
                raise ValueError(f"Error syntax, only 1 'aggregate' allow but found {aggregate_count}")
            # validate pipeline
            pipeline_match = re.findall(r"pipeline\s*:", query)
            pipeline_count = len(pipeline_match) if pipeline_match else 0
            if pipeline_count > 1:
                raise ValueError(f"Error syntax, only 1 'pipeline' allow but found {pipeline_count}")

    @staticmethod
    def _check_query_type(query: str) -> str:
        """
        Check what kind of query need to process and return the name of it
        Currently only support 'find' and 'aggregate'
        :param query:
        """
        find_pattern = r"^\s*find\s*:"
        aggregate_pattern = r"^\s*aggregate\s*:"
        is_find = re.match(find_pattern, query) is not None
        is_aggregate = re.match(aggregate_pattern, query) is not None
        if is_find:
            return "find"
        elif is_aggregate:
            return "aggregate"
        else:
            raise ValueError(
                f"Error while executing query '{query}', currently Mongodb selector only support 'find' and 'aggregate'"
            )

    def delete(self, query: dict, data: list):
        """
        Delete data from collection
        :param query:
        :param data:
        """
        if "selector" in query:
            selector_value = query.get("selector")
            if selector_value is None or selector_value.isspace():
                raise ValueError("Syntax error: selector is not found")
            find_query = self._decompose_find_query(selector_value)
            collection_name = find_query.get("find")
        elif "type" in query:
            collection_name = query.get("type")
        else:
            raise ValueError("'type' or 'selector' statement's attribute is missing")

        if collection_name is None or collection_name.isspace():
            raise ValueError(f"Syntax error: collection name '{collection_name}' not found")
        with self._create_connection() as conn:
            db = conn[self._credential.database]
            collection = db[collection_name]
            data_id = []
            for d in data:
                # only delete by _id
                if d.get("_id"):
                    data_id.append(d["_id"])
            collection.delete_many({"_id": {"$in": data_id}})
