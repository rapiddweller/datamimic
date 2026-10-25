# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import json
import logging
import re
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from decimal import Decimal
from typing import TypeGuard

from bson.decimal128 import Decimal128
from pymongo import MongoClient, UpdateOne
from pymongo.errors import PyMongoError

from datamimic_ce.engine.dsl.vocabulary.constants.attribute_constants import (
    META_SELECTOR,
    META_TARGET_ENTITY,
    META_TYPE,
)
from datamimic_ce.engine.io.clients.database_client import DatabaseClient
from datamimic_ce.engine.io.clients.entity_serialization import stringify_entity_value
from datamimic_ce.engine.io.connection_config.mongodb_connection_config import MongoDBConnectionConfig
from datamimic_ce.engine.io.contracts import DataSourcePagination
from datamimic_ce.errors import IssueCode, invalid_source_error, is_user_error, operation_error

logger = logging.getLogger("DATAMIMIC")


class MongoDBClient(DatabaseClient):
    def __init__(self, credential: MongoDBConnectionConfig):
        self._credential = credential

    def _require_write(self, operation: str) -> None:
        if self._credential.read_only:
            _read_only_blocked(operation, "connection is read-only")

    def _require_read_query(self, query: str) -> None:
        if not self._credential.read_only:
            return
        query_type = self._check_query_type(query)
        if query_type == "aggregate":
            parsed = self._decompose_aggregate_query(query)
            _require_read_only_pipeline(parsed.get("pipeline"))
        elif query_type == "find":
            _require_read_only_document(self._decompose_find_query(query))
        else:
            _read_only_blocked("MongoDB selector", "query is not a supported read operation")

    @staticmethod
    def _to_bson(value: object) -> object:
        """Recursively convert types BSON cannot encode. ``decimal.Decimal`` -> ``bson.Decimal128``
        (MongoDB's native 128-bit decimal): lossless, unlike a float cast. Applied on every write so a
        DATAMIMIC ``type="decimal"`` field round-trips through mongo."""
        if isinstance(value, Decimal):
            return Decimal128(value)
        value = stringify_entity_value(value)  # whole entity bound to a field -> str(entity.to_dict())
        if isinstance(value, Mapping):
            return {k: MongoDBClient._to_bson(v) for k, v in value.items()}
        if isinstance(value, list):
            return [MongoDBClient._to_bson(v) for v in value]
        return value

    @staticmethod
    def _from_bson(value: object) -> object:
        """Inverse of ``_to_bson``: ``bson.Decimal128`` -> ``decimal.Decimal`` on read, so a script that
        does arithmetic on a stored decimal (``product.price * qty``) gets a Python Decimal, not a
        Decimal128 (which has no numeric operators)."""
        if isinstance(value, Decimal128):
            return value.to_decimal()
        if isinstance(value, Mapping):
            return {k: MongoDBClient._from_bson(v) for k, v in value.items()}
        if isinstance(value, list):
            return [MongoDBClient._from_bson(v) for v in value]
        return value

    @staticmethod
    def _is_document(value: object) -> TypeGuard[dict[str, object]]:
        return isinstance(value, dict) and all(isinstance(key, str) for key in value)

    @staticmethod
    def _documents(value: object) -> list[dict[str, object]]:
        if not isinstance(value, list):
            raise TypeError("MongoDB result must be a list of documents")
        documents: list[dict[str, object]] = []
        for document in value:
            if not MongoDBClient._is_document(document):
                raise TypeError("MongoDB result must be a list of documents")
            documents.append(document)
        return documents

    @staticmethod
    def _values_at_path(value: object, parts: list[str]):
        """All values reachable by descending a dotted field path; lists along the way unwind
        (one value per nested element). How a <reference> resolves an entity nested inside a
        collection document (a converted legacy <part> element)."""
        if isinstance(value, list):
            for item in value:
                yield from MongoDBClient._values_at_path(item, parts)
        elif not parts:
            yield value
        elif isinstance(value, Mapping) and parts[0] in value:
            yield from MongoDBClient._values_at_path(value[parts[0]], parts[1:])

    @staticmethod
    def _shell_to_json(query: str) -> str:
        """A MongoDB-shell-style selector -> a JSON string ``json.loads`` accepts. Legacy migrated mongo
        selectors use shell syntax: single-quoted or BAREWORD object keys ($-operators, ``_id``,
        projection fields) and a trailing ``cursor: {}``. Wrap first so the leading key has a
        preceding ``{``; promote single quotes so quoted keys/strings are protected; then quote every
        remaining unquoted bareword key. A value like ``"$total_price"`` is preceded by ``:`` (not
        ``{``/``,``) and already quoted, so it is left untouched."""
        s = "{" + query.replace("'", '"') + "}"
        return re.sub(r"([{,]\s*)([$A-Za-z_][\w$]*)\s*:", r'\1"\2":', s)

    @contextmanager
    def _create_connection(self) -> Iterator[MongoClient]:
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

        connection: MongoClient
        try:
            with MongoClient(**ars) as connection:
                yield connection
        except PyMongoError as error:
            raise operation_error(
                code=IssueCode.OPERATION_EXECUTION_FAILED,
                target="MongoDB",
                error=type(error).__name__,
            ) from error

    def get(self, query: str, pagination: DataSourcePagination | None = None) -> list:
        """
        Get documents from collection
        :param query:
        :param pagination: when given and query_type is "find", pushed to MongoDB as a
            server-side skip/limit on the cursor instead of materializing the whole result.
            "aggregate" queries are unaffected: _query_aggregate_handler already returns a fully
            materialized list, so there is no cursor here to slice server-side.
        :return:
        """
        self._require_read_query(query)
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
                    raise invalid_source_error(
                        code=IssueCode.SOURCE_MONGO_SELECTOR_INVALID,
                        error=f"Syntax error: collection name '{collection_name}' not found",
                    )
                if pagination is not None and pagination.limit == 0:
                    return []  # pymongo's .limit(0) means "no limit", not "empty" - guard explicitly
                cursor = collection.find(find_filter, find_projection)
                if pagination is not None:
                    cursor = cursor.skip(pagination.skip).limit(pagination.limit)
                return self._documents(self._from_bson(list(cursor)))
            elif query_type == "aggregate":
                query_result = self._query_aggregate_handler(query=query, connection=conn)
                return query_result
            else:
                raise invalid_source_error(
                    code=IssueCode.SOURCE_MONGO_SELECTOR_INVALID,
                    error="Currently Mongodb selector only support 'find' and 'aggregate'",
                )

    def get_by_page_with_query(self, query: str, pagination: DataSourcePagination | None = None) -> list:
        """
        Get documents from MongoDB collection when there is a query by pagination.
        :param query:
        :param pagination:
        :return:
        """
        if pagination is None:
            return self.get(query)
        docs = self.get(query, pagination)
        if self._check_query_type(query=query) == "find":
            return docs  # already skip/limit-ed server-side by get() - avoid re-slicing it
        # "aggregate" queries aren't paginated by get() (already a fully materialized list) -
        # same Python-side skip/limit fallback this method has always used for them.
        return docs[pagination.skip : pagination.skip + pagination.limit]

    def get_by_page_with_type(self, collection_name: str, pagination: DataSourcePagination | None = None) -> list:
        """
        Get documents from MongoDB collection when 'type' (name of collection) is defined by pagination
        :param collection_name:
        :param pagination:
        :return:
        """
        return self.get_documents_by_collection(collection_name, pagination)

    def get_documents_by_collection(self, collection_name: str, pagination: DataSourcePagination | None = None) -> list:
        """
        Get documents in collection, optionally paginated server-side (skip/limit pushed to the
        MongoDB cursor instead of loading the full collection into memory).
        :param collection_name:
        :param pagination:
        :return:
        """
        with self._create_connection() as conn:
            db = conn[self._credential.database]
            if collection_name is not None and not collection_name.isspace():
                collection = db[collection_name]
            else:
                raise invalid_source_error(
                    code=IssueCode.SOURCE_MONGO_SELECTOR_INVALID,
                    error=f"Syntax error: collection name '{collection_name}' not found",
                )
            if pagination is not None and pagination.limit == 0:
                return []  # pymongo's .limit(0) means "no limit", not "empty" - guard explicitly
            cursor = collection.find({})
            if pagination is not None:
                cursor = cursor.skip(pagination.skip).limit(pagination.limit)
            return self._documents(self._from_bson(list(cursor)))

    def get_random_rows_by_columns(self, collection_name: str, column_names: list[str]) -> list[tuple]:
        """Fetch the given fields for a <reference> in a stable order, preserving row-tuple
        integrity (same contract as RdbmsClient.get_random_rows_by_columns). Sorted server-side
        on the selected fields (BSON total order): MongoDB's own $sample stage is NOT seedable
        and may repeat documents, so the reference task does the deterministic sampling itself
        via the seeded engine RNG over this stable order. A field missing on a document maps to
        None, like an SQL NULL."""
        if collection_name is None or collection_name.isspace():
            raise invalid_source_error(
                code=IssueCode.SOURCE_MONGO_SELECTOR_INVALID,
                error=f"Syntax error: collection name '{collection_name}' not found",
            )
        # A dotted sourceKey descends into nested documents (lists unwind): a reference to an entity
        # nested INSIDE a collection document. Unwinding several independent paths has no meaningful
        # row pairing, so a dotted path only combines with a single sourceKey.
        dotted = any("." in name for name in column_names)
        if dotted and len(column_names) > 1:
            raise invalid_source_error(
                code=IssueCode.SOURCE_MONGO_SELECTOR_INVALID,
                error="A dotted (nested) reference path only supports a single sourceKey",
            )
        with self._create_connection() as conn:
            collection = conn[self._credential.database][collection_name]
            projection = {name.split(".", 1)[0]: 1 for name in column_names}
            if "_id" not in projection:
                projection["_id"] = 0
            docs = list(collection.find({}, projection))
        docs = self._documents(self._from_bson(docs))
        if not dotted:
            rows = [tuple(doc.get(name) for name in column_names) for doc in docs]
        else:
            parts = column_names[0].split(".")
            rows = [(value,) for doc in docs for value in self._values_at_path(doc, parts)]
        # Stable order so the reference task's seeded sampling is reproducible run-to-run.
        # Numbers sort numerically (not lexicographically: "10" must stay after "2"), everything
        # else falls back to its string form; None sorts last, like an SQL NULL.
        return sorted(rows, key=lambda row: tuple(self._sort_key(v) for v in row))

    @staticmethod
    def _sort_key(value: object) -> tuple[int, float | str]:
        if value is None:
            return (2, "")
        if isinstance(value, int | float | Decimal):
            return (0, float(value))
        return (1, str(value))

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
                raise invalid_source_error(
                    code=IssueCode.SOURCE_MONGO_SELECTOR_INVALID,
                    error=f"Syntax error: collection name '{collection_name}' not found",
                )
            return collection.count_documents({})

    def count_query_length(self, query: str) -> int:
        """
        Count number of documents in collection
        :param query:
        :return:
        """
        self._require_read_query(query)
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
                    raise invalid_source_error(
                        code=IssueCode.SOURCE_MONGO_SELECTOR_INVALID,
                        error=f"Syntax error: collection name '{collection_name}' not found",
                    )
                if not isinstance(find_filter, Mapping):
                    raise invalid_source_error(
                        code=IssueCode.SOURCE_MONGO_SELECTOR_INVALID,
                        error="Syntax error: find filter must be an object",
                    )
                return collection.count_documents(find_filter)
            elif query_type == "aggregate":
                query_result = self._query_aggregate_handler(query=query, connection=conn)
                return len(query_result)
            else:
                raise invalid_source_error(
                    code=IssueCode.SOURCE_MONGO_SELECTOR_INVALID,
                    error="Currently Mongodb selector only support 'find' and 'aggregate'",
                )

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
        if self._credential.read_only:
            _require_read_only_pipeline(aggregate_pipeline)
        # validate pipeline value
        if not isinstance(aggregate_pipeline, list):
            raise invalid_source_error(
                code=IssueCode.SOURCE_MONGO_SELECTOR_INVALID, error="Syntax error: pipeline value must be a list"
            )
        # support multiprocessing working properly: add $sort if pipeline don't have
        if all(operation.get("$sort") is None for operation in aggregate_pipeline):
            aggregate_pipeline.append({"$sort": {"_id": 1}})
        # validate collection name and get MongoDB collection
        if collection_name is not None and not collection_name.isspace():
            collection = db[collection_name]
        else:
            raise invalid_source_error(
                code=IssueCode.SOURCE_MONGO_SELECTOR_INVALID,
                error=f"Syntax error: collection name '{collection_name}' not found",
            )
        if not isinstance(aggregate_pipeline, list):
            raise invalid_source_error(
                code=IssueCode.SOURCE_MONGO_SELECTOR_INVALID, error="Syntax error: pipeline must be a list"
            )
        # execute and return result
        return self._documents(self._from_bson(list(collection.aggregate(aggregate_pipeline))))

    def count_table_length(self, table_name: str) -> int:
        return self.count(table_name)

    def insert(self, collection_name: str, data: list, is_update: bool):
        """
        Insert data into collection
        :param collection_name:
        :param data:
        """
        self._require_write("insert")
        if collection_name is None or collection_name.isspace():
            raise invalid_source_error(
                code=IssueCode.SOURCE_MONGO_SELECTOR_INVALID,
                error=f"Syntax error: collection name '{collection_name}' not found",
            )
        with self._create_connection() as conn:
            db = conn[self._credential.database]
            collection = db[collection_name]
            data = self._documents([self._to_bson(document) for document in data])
            inserted_ids = collection.insert_many(data).inserted_ids
            # Retrieve all the inserted data
            if not is_update:
                return None
            return self._from_bson(list(collection.find({"_id": {"$in": inserted_ids}})))

    def update(self, query: dict, data: list) -> int:
        """
        Update data in collection
        :param query:
        :param data:
        :return: The number of documents matched for an update.
        """
        self._require_write("update")
        if META_TARGET_ENTITY in query:
            collection_name = query.get(META_TARGET_ENTITY)
        elif META_SELECTOR in query:
            value = query.get(META_SELECTOR)
            if value is None or value.isspace():
                raise invalid_source_error(
                    code=IssueCode.SOURCE_MONGO_SELECTOR_INVALID, error="Syntax error: selector is not found"
                )
            find_query = self._decompose_find_query(value)
            collection_name = find_query.get("find")
        elif META_TYPE in query:
            collection_name = query.get(META_TYPE)
        else:
            raise invalid_source_error(
                code=IssueCode.SOURCE_MONGO_SELECTOR_INVALID,
                error="'targetEntity', 'type' or 'selector' statement's attribute is missing",
            )
        if data:
            if collection_name is None or collection_name.isspace():
                raise invalid_source_error(
                    code=IssueCode.SOURCE_MONGO_SELECTOR_INVALID,
                    error=f"Syntax error: collection name '{collection_name}' not found",
                )
            with self._create_connection() as conn:
                db = conn[self._credential.database]
                collection = db[collection_name]
                operation = [UpdateOne({"_id": d["_id"]}, {"$set": self._to_bson(d)}) for d in data]
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
        self._require_write("upsert")
        # targetEntity/type name the collection; the selector (if any) still provides the match filter.
        collection_name = selector_dict.get(META_TARGET_ENTITY) or selector_dict.get(META_TYPE)
        filter_query: dict = {}
        if META_SELECTOR in selector_dict:
            selector_value = selector_dict.get(META_SELECTOR)
            if selector_value is None or selector_value.isspace():
                raise invalid_source_error(
                    code=IssueCode.SOURCE_MONGO_SELECTOR_INVALID, error="Syntax error: selector is not found"
                )
            find_query = self._decompose_find_query(selector_value)
            collection_name = collection_name or find_query.get("find")
            filter_query = find_query["filter"]
        elif collection_name is None:
            raise invalid_source_error(
                code=IssueCode.SOURCE_MONGO_SELECTOR_INVALID,
                error="'targetEntity', 'type' or 'selector' statement's attribute is missing",
            )
        # query = self._decompose_find_query(selector)

        # Merge updated_data and filter query
        updated_data = self._documents([self._to_bson({**filter_query, **data}) for data in updated_data])

        if collection_name is None or collection_name.isspace():
            raise invalid_source_error(
                code=IssueCode.SOURCE_MONGO_SELECTOR_INVALID,
                error=f"Syntax error: collection name '{collection_name}' not found",
            )
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
                return self._documents(
                    self._from_bson(list(collection.find({"_id": {"$in": [doc["_id"] for doc in updated_data]}})))
                )

    def _decompose_find_query(self, query: str) -> dict:
        """
        Decompose query from selector statement into database collection name, filter, and projection
        :param query:
        :return: dict-keys: find, filter, projection
        """
        self._validate_query_command(query)
        # change mongodb-shell query into a JSON string (bareword keys, $-operators, projection fields)
        input_query = self._shell_to_json(query)
        # check and return query as dict
        try:
            result = json.loads(input_query)
            if not isinstance(result, dict):
                raise invalid_source_error(
                    code=IssueCode.SOURCE_MONGO_SELECTOR_INVALID, error="selector must be an object"
                )
            if result.get("find") is None:
                raise invalid_source_error(
                    code=IssueCode.SOURCE_MONGO_SELECTOR_INVALID, error="Wrong query syntax 'find' component not found"
                )
            elif result.get("filter") is None:
                raise invalid_source_error(
                    code=IssueCode.SOURCE_MONGO_SELECTOR_INVALID,
                    error="Wrong query syntax 'filter' component not found",
                )
            else:
                return result
        except (json.JSONDecodeError, ValueError) as err:
            if is_user_error(err):
                raise
            raise invalid_source_error(
                code=IssueCode.SOURCE_MONGO_SELECTOR_INVALID,
                error="expected a valid selector object with required fields",
            ) from err

    def _decompose_aggregate_query(self, query: str) -> dict:
        """
        Decompose query from selector statement into database collection name, pipeline
        :param query:
        :return: dict-keys:  name, pipeline
        """
        self._validate_query_command(query)
        # change mongodb-shell query into a JSON string (bareword $-operators, _id, trailing cursor:{})
        input_query = self._shell_to_json(query)
        # check and return query as dict
        try:
            result = json.loads(input_query)
            if not isinstance(result, dict):
                raise invalid_source_error(
                    code=IssueCode.SOURCE_MONGO_SELECTOR_INVALID, error="selector must be an object"
                )
            if result.get("aggregate") is None:
                raise invalid_source_error(
                    code=IssueCode.SOURCE_MONGO_SELECTOR_INVALID,
                    error="Wrong query syntax 'aggregate' component not found",
                )
            elif result.get("pipeline") is None:
                raise invalid_source_error(
                    code=IssueCode.SOURCE_MONGO_SELECTOR_INVALID,
                    error="Wrong query syntax 'pipeline' component not found",
                )
            else:
                return result
        except (json.JSONDecodeError, ValueError) as err:
            if is_user_error(err):
                raise
            raise invalid_source_error(
                code=IssueCode.SOURCE_MONGO_SELECTOR_INVALID,
                error="expected a valid selector object with required fields",
            ) from err

    @staticmethod
    def _top_level_keys(query: str) -> list[str]:
        """Depth-0 keys of a mongo shell-style selector, in order of appearance. A single
        quote/brace/bracket-aware pass, not a regex guessing at quote style: a key is bareword,
        single-, or double-quoted, uniformly; a value's own colons/commas/braces (inside a quoted
        string, or nested one level down in a filter/pipeline) never leak into the top level, so a
        field literally named 'find' inside a nested value is never mistaken for the command key."""
        keys: list[str] = []
        depth = 0
        quote_char: str | None = None
        segment_start = 0
        for i, c in enumerate(query):
            if quote_char:
                if c == quote_char:
                    quote_char = None
            elif c in "'\"":
                quote_char = c
            elif c in "{[":
                depth += 1
            elif c in "}]":
                depth -= 1
            elif depth == 0 and c == ":":
                raw_key = query[segment_start:i].strip().lstrip(",").strip()
                if len(raw_key) >= 2 and raw_key[0] == raw_key[-1] and raw_key[0] in "'\"":
                    raw_key = raw_key[1:-1]
                keys.append(raw_key)
            elif depth == 0 and c == ",":
                segment_start = i
        return keys

    @staticmethod
    def _validate_query_command(query: str):
        """
        validate query string
        'find' query have elements: 'find', 'filter', 'projection'
        'aggregate' query have elements: 'aggregate', 'pipeline'
        :param query:
        """
        query = query.strip()
        keys = MongoDBClient._top_level_keys(query)
        find_count = keys.count("find")
        aggregate_count = keys.count("aggregate")
        if find_count and aggregate_count:
            raise invalid_source_error(
                code=IssueCode.SOURCE_MONGO_SELECTOR_INVALID,
                error="Error syntax, only one query type allow but found both 'find' and 'aggregate'",
            )
        if find_count:
            if find_count > 1:
                raise invalid_source_error(
                    code=IssueCode.SOURCE_MONGO_SELECTOR_INVALID,
                    error=f"Error syntax, only 1 'find' allow but found {find_count}",
                )
            filter_count = keys.count("filter")
            if filter_count > 1:
                raise invalid_source_error(
                    code=IssueCode.SOURCE_MONGO_SELECTOR_INVALID,
                    error=f"Error syntax, only 1 'filter' allow but found {filter_count}",
                )
            projection_count = keys.count("projection")
            if projection_count > 1:
                raise invalid_source_error(
                    code=IssueCode.SOURCE_MONGO_SELECTOR_INVALID,
                    error=f"Error syntax, only 1 'projection' allow but found {projection_count}",
                )
        elif aggregate_count:
            if aggregate_count > 1:
                raise invalid_source_error(
                    code=IssueCode.SOURCE_MONGO_SELECTOR_INVALID,
                    error=f"Error syntax, only 1 'aggregate' allow but found {aggregate_count}",
                )
            pipeline_count = keys.count("pipeline")
            if pipeline_count > 1:
                raise invalid_source_error(
                    code=IssueCode.SOURCE_MONGO_SELECTOR_INVALID,
                    error=f"Error syntax, only 1 'pipeline' allow but found {pipeline_count}",
                )

    @staticmethod
    def _check_query_type(query: str) -> str:
        """
        Check what kind of query need to process and return the name of it
        Currently only support 'find' and 'aggregate'
        :param query:
        """
        keys = MongoDBClient._top_level_keys(query)
        first_key = keys[0] if keys else None
        if first_key == "find":
            return "find"
        elif first_key == "aggregate":
            return "aggregate"
        else:
            raise invalid_source_error(
                code=IssueCode.SOURCE_MONGO_SELECTOR_INVALID,
                error=(
                    f"Error while executing query '{query}', "
                    "currently Mongodb selector only support 'find' and 'aggregate'"
                ),
            )

    def clear_collection(self, collection_name: str) -> None:
        """Delete every document and keep the collection, its indexes and options (target="mongo.clear")."""
        self._require_write("clear")
        collection_name = self._operation_collection(collection_name)
        with self._create_connection() as conn:
            deleted = conn[self._credential.database][collection_name].delete_many({}).deleted_count
        logger.info(
            "OPERATION | mongodb.clear | collection=%s | action=clear | deleted_count=%s", collection_name, deleted
        )

    def drop_collection(self, collection_name: str) -> None:
        """Drop the collection with its documents, indexes and options (target="mongo.drop")."""
        self._require_write("drop")
        collection_name = self._operation_collection(collection_name)
        with self._create_connection() as conn:
            conn[self._credential.database][collection_name].drop()
        logger.info("OPERATION | mongodb.drop | collection=%s | action=drop", collection_name)

    @staticmethod
    def _operation_collection(collection_name: str | None) -> str:
        if not collection_name or re.fullmatch(r"\s*", collection_name):
            raise invalid_source_error(
                code=IssueCode.SOURCE_MONGO_SELECTOR_INVALID,
                error=f"Syntax error: collection name '{collection_name}' not found",
            )
        return collection_name

    def delete(self, query: dict, data: list):
        """
        Delete data from collection
        :param query:
        :param data:
        """
        self._require_write("delete")
        if META_TARGET_ENTITY in query:
            collection_name = query.get(META_TARGET_ENTITY)
        elif META_SELECTOR in query:
            selector_value = query.get(META_SELECTOR)
            if selector_value is None or selector_value.isspace():
                raise invalid_source_error(
                    code=IssueCode.SOURCE_MONGO_SELECTOR_INVALID, error="Syntax error: selector is not found"
                )
            find_query = self._decompose_find_query(selector_value)
            collection_name = find_query.get("find")
        elif META_TYPE in query:
            collection_name = query.get(META_TYPE)
        else:
            raise invalid_source_error(
                code=IssueCode.SOURCE_MONGO_SELECTOR_INVALID,
                error="'targetEntity', 'type' or 'selector' statement's attribute is missing",
            )

        if collection_name is None or collection_name.isspace():
            raise invalid_source_error(
                code=IssueCode.SOURCE_MONGO_SELECTOR_INVALID,
                error=f"Syntax error: collection name '{collection_name}' not found",
            )
        with self._create_connection() as conn:
            db = conn[self._credential.database]
            collection = db[collection_name]
            data_id = []
            for d in data:
                # only delete by _id
                if d.get("_id"):
                    data_id.append(d["_id"])
            collection.delete_many({"_id": {"$in": data_id}})


_READ_ONLY_STAGES = frozenset(
    {
        "$match",
        "$project",
        "$sort",
        "$limit",
        "$skip",
        "$group",
        "$unwind",
        "$addFields",
        "$set",
        "$unset",
        "$replaceRoot",
        "$replaceWith",
        "$count",
        "$sortByCount",
        "$lookup",
        "$graphLookup",
        "$facet",
        "$unionWith",
        "$sample",
        "$bucket",
        "$bucketAuto",
        "$setWindowFields",
        "$densify",
        "$fill",
        "$documents",
        "$redact",
        "$geoNear",
    }
)
_WRITE_OR_SCRIPT_OPERATORS = frozenset({"$out", "$merge", "$where", "$function", "$accumulator"})


def _read_only_blocked(target: str, reason: str) -> None:
    raise operation_error(code=IssueCode.OPERATION_READ_ONLY_WRITE_BLOCKED, target=target, reason=reason)


def _require_read_only_pipeline(pipeline: object) -> None:
    if not isinstance(pipeline, list):
        _read_only_blocked("MongoDB aggregate", "pipeline must be a parsed array")
        return
    for stage in pipeline:
        if not isinstance(stage, dict) or len(stage) != 1 or next(iter(stage)) not in _READ_ONLY_STAGES:
            _read_only_blocked("MongoDB aggregate", "pipeline contains a write or unsupported stage")
        _require_read_only_document(stage)


def _require_read_only_document(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in _WRITE_OR_SCRIPT_OPERATORS:
                _read_only_blocked("MongoDB selector", "query contains a write or server-side script operator")
            if key == "pipeline":
                _require_read_only_pipeline(item)
            elif key == "$facet":
                if not isinstance(item, dict):
                    _read_only_blocked("MongoDB aggregate", "facet must contain parsed pipelines")
                    return
                for pipeline in item.values():
                    _require_read_only_pipeline(pipeline)
            else:
                _require_read_only_document(item)
    elif isinstance(value, list):
        for item in value:
            _require_read_only_document(item)
