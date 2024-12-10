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
    def __init__(self):
        pass

    @staticmethod
    def get_task_util_cls():
        from datamimic_ce.tasks.task_util import TaskUtil

        return TaskUtil

    @staticmethod
    def get_data_generation_util():
        return DataGenerationCEUtil

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
    def get_datasource_util_cls():
        from datamimic_ce.data_sources.data_source_util import DataSourceUtil

        return DataSourceUtil

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
