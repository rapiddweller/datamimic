# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
from datamimic_ce.config import settings
from datamimic_ce.exporters.exporter_util import ExporterUtil
from datamimic_ce.generators.datetime_generator import DateTimeGenerator
from datamimic_ce.generators.integer_generator import IntegerGenerator
from datamimic_ce.generators.string_generator import StringGenerator
from datamimic_ce.logger import setup_logger
from datamimic_ce.parsers.parser_util import ParserUtil
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil
from datamimic_ce.utils.data_generation_ce_util import DataGenerationCEUtil


class ClassFactoryCEUtil(BaseClassFactoryUtil):
    # Singleton instance of DataGenerationCEUtil
    _data_generation_util_instance = None

    def __init__(self):
        pass

    @staticmethod
    def get_task_util_cls():
        from datamimic_ce.tasks.task_util import TaskUtil

        return TaskUtil

    @staticmethod
    def get_city_entity(country_code):
        """
        Create and return a CityEntity instance for the given country_code.
        
        Args:
            country_code: The country code to use as dataset.
            
        Returns:
            A CityEntity instance configured with the specified country_code.
        """
        from datamimic_ce.entities.city_entity import CityEntity
        return CityEntity(ClassFactoryCEUtil(), dataset=country_code)

    @staticmethod
    def get_name_entity(locale):
        """
        Create and return a simple mock NameEntity.
        
        Args:
            locale: The locale to use (not used in this mock implementation).
            
        Returns:
            A simple mock object with the necessary methods.
        """
        # Create a simple mock object with the required methods
        class MockNameEntity:
            def reset(self):
                pass  # No-op reset method
                
        return MockNameEntity()

    @staticmethod
    def get_data_generation_util():
        """
        Get an instance of the data generation utility.

        Returns:
            An instance of DataGenerationCEUtil.
        """
        # Use the singleton pattern to ensure we only create one instance
        if ClassFactoryCEUtil._data_generation_util_instance is None:
            ClassFactoryCEUtil._data_generation_util_instance = DataGenerationCEUtil()
        return ClassFactoryCEUtil._data_generation_util_instance

    @staticmethod
    def get_datetime_generator():
        return DateTimeGenerator

    @staticmethod
    def get_integer_generator():
        return IntegerGenerator

    @staticmethod
    def get_string_generator():
        return StringGenerator

    @staticmethod
    def get_exporter_util():
        return ExporterUtil

    @staticmethod
    def get_parser_util_cls():
        return ParserUtil

    @staticmethod
    def get_datasource_registry():
        from datamimic_ce.data_sources.data_source_registry import DataSourceRegistry

        return DataSourceRegistry()

    @staticmethod
    def get_setup_logger_func():
        """
        Returns:
            The setup logger function.
        """
        return setup_logger

    @staticmethod
    def get_app_settings():
        """
        Abstract method to get the app settings.

        Returns:
            The app settings.
        """
        return settings
