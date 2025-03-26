# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.config import settings
from datamimic_ce.exporters.exporter_util import ExporterUtil
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
        from datamimic_ce.domains.common.literal_generators.datetime_generator import DateTimeGenerator

        return DateTimeGenerator

    @staticmethod
    def get_integer_generator():
        from datamimic_ce.domains.common.literal_generators.integer_generator import IntegerGenerator

        return IntegerGenerator

    @staticmethod
    def get_string_generator():
        from datamimic_ce.domains.common.literal_generators.string_generator import StringGenerator

        return StringGenerator

    @staticmethod
    def get_exporter_util():
        return ExporterUtil

    @staticmethod
    def get_parser_util_cls():
        return ParserUtil

    @staticmethod
    def get_datasource_registry_cls():
        from datamimic_ce.data_sources.data_source_registry import DataSourceRegistry

        return DataSourceRegistry

    @staticmethod
    def get_setup_logger_func():
        """
        Returns:
            The setup logger function.
        """
        return setup_logger

    @staticmethod
    def get_app_settings():
        """Get application settings."""
        return settings
