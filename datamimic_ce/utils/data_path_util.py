# # DATAMIMIC
# # Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# # This software is licensed under the MIT License.
# # See LICENSE file for the full text of the license.
# # For questions and support, contact: info@rapiddweller.com

# import os
# from pathlib import Path

# from datamimic_ce.logger import logger


# class DataPathUtil:
#     """Utility class for handling data paths in a unified way across all entity classes."""

#     # Base data directory path (will be initialized on first use)
#     _BASE_DATA_DIR: Path | None = None

#     # Cache for entity-specific data directories
#     _ENTITY_DATA_DIRS: dict[str, Path] = {}

#     @classmethod
#     def get_base_data_dir(cls) -> Path:
#         """Get the base data directory for all entities.

#         Returns:
#             Path: The base data directory path.
#         """
#         if cls._BASE_DATA_DIR is None:
#             # Try to get the base data directory from environment variable
#             env_data_dir = os.environ.get("DATAMIMIC_DATA_DIR")
#             if env_data_dir:
#                 cls._BASE_DATA_DIR = Path(env_data_dir)
#                 logger.info(f"Using data directory from environment: {cls._BASE_DATA_DIR}")
#             else:
#                 # Default to the standard location
#                 # First, find the datamimic_ce package directory
#                 import datamimic_ce

#                 package_dir = Path(datamimic_ce.__file__).parent
#                 cls._BASE_DATA_DIR = package_dir / "entities" / "data"
#                 logger.info(f"Using default data directory: {cls._BASE_DATA_DIR}")

#         return cls._BASE_DATA_DIR

#     @classmethod
#     def set_base_data_dir(cls, path: str | Path) -> None:
#         """Set the base data directory for all entities.

#         Args:
#             path: The path to the base data directory.
#         """
#         cls._BASE_DATA_DIR = Path(path)
#         # Clear the entity data directory cache to force recalculation
#         cls._ENTITY_DATA_DIRS.clear()
#         logger.info(f"Base data directory set to: {cls._BASE_DATA_DIR}")

#     @classmethod
#     def get_entity_data_dir(cls, entity_type: str) -> Path:
#         """Get the data directory for a specific entity type.

#         Args:
#             entity_type: The entity type (e.g., "healthcare", "organization").

#         Returns:
#             Path: The entity-specific data directory path.
#         """
#         if entity_type not in cls._ENTITY_DATA_DIRS:
#             base_dir = cls.get_base_data_dir()
#             cls._ENTITY_DATA_DIRS[entity_type] = base_dir / entity_type

#             # Create the directory if it doesn't exist
#             os.makedirs(cls._ENTITY_DATA_DIRS[entity_type], exist_ok=True)

#         return cls._ENTITY_DATA_DIRS[entity_type]

#     @classmethod
#     def get_data_file_path(cls, entity_type: str, file_name: str) -> Path:
#         """Get the path to a specific data file for an entity type.

#         Args:
#             entity_type: The entity type (e.g., "healthcare", "organization").
#             file_name: The name of the data file.

#         Returns:
#             Path: The path to the data file.
#         """
#         entity_dir = cls.get_entity_data_dir(entity_type)
#         return entity_dir / file_name

#     @classmethod
#     def get_country_specific_data_file_path(cls, entity_type: str, data_type: str, country_code: str) -> Path:
#         """Get the path to a country-specific data file.

#         Args:
#             entity_type: The entity type (e.g., "healthcare", "organization").
#             data_type: The type of data (e.g., "test_types", "lab_names").
#             country_code: The country code (e.g., "US", "DE").

#         Returns:
#             Path: The path to the country-specific data file.
#         """
#         entity_dir = cls.get_entity_data_dir(entity_type)
#         return entity_dir / f"{data_type}_{country_code}.csv"

#     @classmethod
#     def get_subdirectory_path(cls, entity_type: str, subdirectory: str) -> Path:
#         """Get the path to a subdirectory within an entity's data directory.

#         Args:
#             entity_type: The entity type (e.g., "healthcare", "organization").
#             subdirectory: The name of the subdirectory.

#         Returns:
#             Path: The path to the subdirectory.
#         """
#         entity_dir = cls.get_entity_data_dir(entity_type)
#         subdir_path = entity_dir / subdirectory

#         # Create the subdirectory if it doesn't exist
#         os.makedirs(subdir_path, exist_ok=True)

#         return subdir_path

#     @classmethod
#     def file_exists(cls, file_path: Path) -> bool:
#         """Check if a file exists.

#         Args:
#             file_path: The path to the file.

#         Returns:
#             bool: True if the file exists, False otherwise.
#         """
#         return file_path.exists() and file_path.is_file()
