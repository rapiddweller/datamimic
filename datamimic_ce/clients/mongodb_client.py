# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import json
import re
from collections.abc import Mapping
from typing import Any, cast

from pymongo import MongoClient, UpdateOne

from datamimic_ce.clients.database_client import DatabaseClient
from datamimic_ce.connection_config.mongodb_connection_config import MongoDBConnectionConfig
from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination


class MongoDBClient(DatabaseClient):
    def __init__(self, credential: MongoDBConnectionConfig):
        self._credential = credential
        # Caches for paginated results
        self._paginated_find_cache: dict[str, list] = {}
        self._paginated_aggregate_cache: dict[str, list] = {}
        self._paginated_collection_cache: dict[str, list] = {}
        
        # Caches for full results (when no pagination is initially requested)
        self._full_find_cache: dict[str, list] = {}
        self._full_aggregate_cache: dict[str, list] = {}
        self._full_collection_cache: dict[str, list] = {}


    def _create_connection(self) -> MongoClient:
        ars = {
            "host": self._credential.host,
            "port": self._credential.port,
            "username": self._credential.user,
            "password": self._credential.password,
        }

        cred_dump = self._credential.model_dump()
        if "authSource" in cred_dump:
            ars["authSource"] = cred_dump["authSource"]
        if "authMechanism" in cred_dump:
            ars["authMechanism"] = cred_dump["authMechanism"]

        return MongoClient(**ars)

    def get_find_by_page(
        self,
        collection_name: str,
        filter_dict: dict | None = None,
        projection_dict: dict | None = None,
        pagination: DataSourcePagination | None = None,
    ) -> list:
        """
        Get documents using a find query with optional pagination.
        If pagination is None, fetches all documents matching the find query.
        """
        actual_filter = filter_dict if filter_dict is not None else {}
        # actual_projection is allowed to be None for pymongo's find

        if pagination is None:
            filter_str = json.dumps(actual_filter, sort_keys=True)
            projection_str = json.dumps(projection_dict, sort_keys=True) if projection_dict is not None else "None"
            full_cache_key = f"find_{collection_name}_{filter_str}_{projection_str}"

            if full_cache_key in self._full_find_cache:
                return self._full_find_cache[full_cache_key]
            
            with self._create_connection() as conn:
                db = conn[self._credential.database]
                collection = db[collection_name]
                docs = list(collection.find(actual_filter, projection_dict))
                self._full_find_cache[full_cache_key] = docs
                return docs

        # Paginated request
        paginated_cache_key = (
            f"find_{collection_name}_"
            f"{json.dumps(actual_filter, sort_keys=True)}_"
            f"{json.dumps(projection_dict, sort_keys=True) if projection_dict is not None else 'None'}_"
            f"{pagination.skip}_{pagination.limit}"
        )

        if paginated_cache_key in self._paginated_find_cache:
            return self._paginated_find_cache[paginated_cache_key]

        with self._create_connection() as conn:
            db = conn[self._credential.database]
            collection = db[collection_name]
            docs = list(
                collection.find(actual_filter, projection_dict)
                .skip(pagination.skip)
                .limit(pagination.limit)
            )
            self._paginated_find_cache[paginated_cache_key] = docs
            return docs

    def get_aggregate_by_page(
        self,
        collection_name: str,
        pipeline_list: list,
        pagination: DataSourcePagination | None = None,
    ) -> list:
        """
        Get documents using an aggregate query with optional pagination.
        If pagination is None, fetches all documents resulting from the aggregation.
        """
        pipeline_str = json.dumps(pipeline_list, sort_keys=True) 

        if pagination is None:
            full_cache_key = f"agg_{collection_name}_{pipeline_str}"
            if full_cache_key in self._full_aggregate_cache:
                return self._full_aggregate_cache[full_cache_key]

            with self._create_connection() as conn:
                db = conn[self._credential.database]
                collection = db[collection_name]
                current_pipeline = [p for p in pipeline_list] 
                if all(stage.get("$sort") is None for stage in current_pipeline): # Ensure sort for full results
                    current_pipeline.append({"$sort": {"_id": 1}})
                docs = list(collection.aggregate(current_pipeline))
                self._full_aggregate_cache[full_cache_key] = docs
                return docs

        paginated_cache_key = f"agg_{collection_name}_{pipeline_str}_{pagination.skip}_{pagination.limit}"
        if paginated_cache_key in self._paginated_aggregate_cache:
            return self._paginated_aggregate_cache[paginated_cache_key]
        
        with self._create_connection() as conn:
            db = conn[self._credential.database]
            collection = db[collection_name]
            
            current_pipeline = [p for p in pipeline_list] 
            if all(stage.get("$sort") is None for stage in current_pipeline): # Ensure sort before pagination
                current_pipeline.append({"$sort": {"_id": 1}})
            
            paginated_pipeline = current_pipeline + [
                {"$skip": pagination.skip},
                {"$limit": pagination.limit},
            ]
            docs = list(collection.aggregate(paginated_pipeline))
            self._paginated_aggregate_cache[paginated_cache_key] = docs
            return docs

    def get_by_page_with_type(self, collection_name: str, pagination: DataSourcePagination | None = None) -> list:
        """
        Get documents from MongoDB collection (by collection name only) with optional pagination.
        If pagination is None, fetches all documents from the collection.
        """
        if pagination is None:
            if collection_name in self._full_collection_cache:
                return self._full_collection_cache[collection_name]
            else:
                docs = self.get_documents_by_collection(collection_name) 
                self._full_collection_cache[collection_name] = docs
                return docs

        cache_key = f"{collection_name}_{pagination.skip}_{pagination.limit}"
        if cache_key in self._paginated_collection_cache:
            return self._paginated_collection_cache[cache_key]

        with self._create_connection() as conn:
            db = conn[self._credential.database]
            if collection_name is None or collection_name.isspace():
                raise ValueError(f"Syntax error: collection name '{collection_name}' not found")
            collection = db[collection_name]
            docs = list(collection.find({}).skip(pagination.skip).limit(pagination.limit))
            self._paginated_collection_cache[cache_key] = docs
            return docs

    def get_documents_by_collection(self, collection_name: str) -> list:
        """
        Get all documents in a collection.
        """
        with self._create_connection() as conn:
            db = conn[self._credential.database]
            if collection_name is None or collection_name.isspace():
                raise ValueError(f"Syntax error: collection name '{collection_name}' not found")
            collection = db[collection_name]
            return list(collection.find({}))

    def count(self, collection_name: str) -> int: # This is equivalent to count_table_length
        """
        Count all documents in a collection.
        """
        with self._create_connection() as conn:
            db = conn[self._credential.database]
            if collection_name is None or collection_name.isspace():
                raise ValueError(f"Syntax error: collection name '{collection_name}' not found")
            collection = db[collection_name]
            return collection.count_documents({})

    def count_find_query_length(self, collection_name: str, filter_dict: dict | None = None) -> int:
        """
        Count number of documents returned by a find query.
        """
        actual_filter = filter_dict if filter_dict is not None else {}
        with self._create_connection() as conn:
            db = conn[self._credential.database]
            if collection_name is None or collection_name.isspace():
                raise ValueError(f"Syntax error: collection name '{collection_name}' not found")
            collection = db[collection_name]
            return collection.count_documents(cast(Mapping[str, Any], actual_filter))

    def count_aggregate_query_length(self, collection_name: str, pipeline_list: list) -> int:
        """
        Count number of documents returned by an aggregate query.
        """
        with self._create_connection() as conn:
            db = conn[self._credential.database]
            if collection_name is None or collection_name.isspace():
                raise ValueError(f"Syntax error: collection name '{collection_name}' not found")
            collection = db[collection_name]
            
            count_pipeline = [stage for stage in pipeline_list if "$limit" not in stage and "$skip" not in stage]
            count_pipeline.append({"$count": "total_count"})
            
            count_result = list(collection.aggregate(count_pipeline))
            return count_result[0]["total_count"] if count_result else 0

    def count_table_length(self, table_name: str): # type: ignore[override]
        # In MongoDB context, a "table" is a collection.
        return self.count(table_name)

    def insert(self, collection_name: str, data: list, is_update: bool):
        if collection_name is None or collection_name.isspace():
            raise ValueError(f"Syntax error: collection name '{collection_name}' not found")
        with self._create_connection() as conn:
            db = conn[self._credential.database]
            collection = db[collection_name]
            if not data: 
                return [] if is_update else None
            inserted_ids = collection.insert_many(data).inserted_ids
            return list(collection.find({"_id": {"$in": inserted_ids}})) if is_update else None


    def update(self, collection_specifier: dict, data_to_update: list) -> int:
        """
        Update data in collection.
        collection_specifier is expected to define collection_name (e.g., via 'collection_name' or 'type' key).
        Updates are performed based on '_id' present in items of 'data_to_update'.
        """
        collection_name = collection_specifier.get("collection_name")
        if not collection_name and "type" in collection_specifier: # Fallback to 'type'
            collection_name = collection_specifier.get("type")

        if not collection_name or collection_name.isspace():
            raise ValueError("Update 'collection_specifier' must define 'collection_name' or 'type'")
        
        if not data_to_update:
            return 0
            
        with self._create_connection() as conn:
            db = conn[self._credential.database]
            collection = db[collection_name]
            # Assuming data_to_update is a list of full documents, where each dict has an '_id'.
            operations = [
                UpdateOne({"_id": doc["_id"]}, {"$set": {k: v for k, v in doc.items() if k != "_id"}})
                for doc in data_to_update
                if isinstance(doc, dict) and "_id" in doc
            ]
            if not operations:
                return 0 # No valid operations (e.g., data items missing _id)
            result = collection.bulk_write(operations)
            return result.matched_count

    def upsert(self, target_specifier: dict, data_to_upsert: list[dict]) -> list:
        """
        Upsert data into collection.
        target_specifier is expected to define collection_name (e.g., via 'collection_name' or 'type' key)
        and optionally a base 'filter' for merging with each data item.
        """
        collection_name = target_specifier.get("collection_name")
        base_filter_for_merge = target_specifier.get("filter", {}) 

        if not collection_name and "type" in target_specifier: # Fallback to 'type'
            collection_name = target_specifier.get("type")
        
        if not collection_name or collection_name.isspace():
            raise ValueError("Upsert 'target_specifier' must define 'collection_name' or 'type'")

        if not data_to_upsert:
            return []

        final_docs_for_upsert_ops = []
        for item in data_to_upsert:
            # Merge item with base_filter if provided; item's values take precedence
            doc_to_op = {**base_filter_for_merge, **item} 
            final_docs_for_upsert_ops.append(doc_to_op)
        
        if not final_docs_for_upsert_ops: # Should not happen if data_to_upsert was not empty
            return []

        ids_for_retrieval = []
        with self._create_connection() as conn:
            db = conn[self._credential.database]
            collection = db[collection_name]
            
            for doc in final_docs_for_upsert_ops:
                query_filter = {"_id": doc["_id"]} if "_id" in doc else doc 
                update_doc = {"$set": {k:v for k,v in doc.items() if k != '_id'}} # Ensure not to $set _id itself
                if not update_doc: # if doc only contained _id
                    if "_id" in doc: # if it's an existing doc, no update needed from this item
                        ids_for_retrieval.append(doc["_id"])
                        continue
                    else: # if it's an empty doc to insert, this case is ambiguous
                        # For now, let it proceed, mongo might create an _id
                        pass

                result = collection.update_one(query_filter, update_doc, upsert=True)
                
                if result.upserted_id:
                    ids_for_retrieval.append(result.upserted_id)
                elif "_id" in doc: 
                    ids_for_retrieval.append(doc["_id"])
                elif result.matched_count > 0:
                    # Matched a document but no _id in input doc, try to find it if needed for retrieval
                    # This scenario is complex, for robust retrieval, _id should be known or generated
                    # For now, if we can't identify a specific ID, we might not retrieve this specific doc later
                    pass


            if ids_for_retrieval:
                return list(collection.find({"_id": {"$in": ids_for_retrieval}}))
            # If no IDs were captured (e.g., all updates on existing docs identified by content not _id)
            # This part might need more sophisticated logic for retrieval post-upsert.
            # Returning the processed list that was intended for upsert might be an option.
            return final_docs_for_upsert_ops # Or an empty list if retrieval is strictly ID based

    def delete(self, collection_specifier: dict, data_with_ids: list):
        """
        Delete data from collection based on _id values in the data_with_ids list.
        collection_specifier is used to determine the collection (e.g., via 'collection_name' or 'type' key).
        """
        collection_name = collection_specifier.get("collection_name")
        if not collection_name and "type" in collection_specifier: # Fallback to 'type'
            collection_name = collection_specifier.get("type")
        
        if not collection_name or collection_name.isspace():
            raise ValueError("Delete 'collection_specifier' must define 'collection_name' or 'type'")
        
        ids_to_delete = [d["_id"] for d in data_with_ids if isinstance(d, dict) and d.get("_id")]
        if not ids_to_delete:
            return 

        with self._create_connection() as conn:
            db = conn[self._credential.database]
            collection = db[collection_name]
            collection.delete_many({"_id": {"$in": ids_to_delete}})
