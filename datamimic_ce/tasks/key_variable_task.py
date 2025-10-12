# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import ast
import random
from abc import abstractmethod
from collections.abc import Iterable
from datetime import datetime, timedelta

import numpy

from datamimic_ce.constants.data_type_constants import DATA_TYPE_BOOL, DATA_TYPE_FLOAT, DATA_TYPE_INT, DATA_TYPE_STRING
from datamimic_ce.contexts.context import Context
from datamimic_ce.contexts.geniter_context import GenIterContext
from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination
from datamimic_ce.data_sources.weighted_data_source import WeightedDataSource
from datamimic_ce.domains.common.literal_generators.generator_util import GeneratorUtil
from datamimic_ce.domains.common.literal_generators.sequence_table_generator import SequenceTableGenerator
from datamimic_ce.domains.common.literal_generators.string_generator import StringGenerator
from datamimic_ce.statements.element_statement import ElementStatement
from datamimic_ce.statements.key_statement import KeyStatement
from datamimic_ce.statements.variable_statement import VariableStatement


class KeyVariableTask:
    # Specify which mode Attribute and Variable Task will use
    _SCRIPT_MODE = "script"
    _CONSTANT_MODE = "constant"
    _VALUES_MODE = "values"
    _GENERATOR_MODE = "generator"
    _LAZY_GENERATOR_MODE = "lazy_generator"
    _PATTERN_MODE = "pattern"
    _RANDOM_MODE = "random"
    _STRING_MODE = "string"

    def __init__(
        self,
        ctx: SetupContext,
        statement: KeyStatement | VariableStatement | ElementStatement,
        pagination: DataSourcePagination | None = None,
    ):
        from datamimic_ce.tasks.task_util import TaskUtil

        self._element_tag = "key" if isinstance(statement, KeyStatement) else "variable"
        self._statement = statement
        self._generator: WeightedDataSource | None = None
        self._pagination = pagination
        self._converter_list = TaskUtil.create_converter_list(ctx, statement.converter)

        self._mode: str | None = None

        self._simple_type_set = {
            DATA_TYPE_STRING,
            DATA_TYPE_INT,
            DATA_TYPE_FLOAT,
            DATA_TYPE_BOOL,
            "NoneType",
        }

    def _determine_generation_mode(self, ctx: SetupContext):
        """
        Determine data generation mode based on element attributes

        :param ctx:
        :param statement:
        :param pagination:
        :return:
        """
        if self._statement.script is not None:
            self._mode = self._SCRIPT_MODE
        elif self._statement.constant is not None:
            self._mode = self._CONSTANT_MODE
        elif self._statement.string is not None:
            self._mode = self._STRING_MODE
        elif self._statement.values is not None:
            # evaluate input values first to handle some list like input, e.g.: values="'1,2,3,4', '1,2,3', '1,2'"
            try:
                self._values = ast.literal_eval(self._statement.values)
                # If values is defined as single value (e.g. 'a', '1',...), convert into tuple
                if not isinstance(self._values, Iterable) and self._values is not None:
                    self._values = (self._values,)

            except (SyntaxError, ValueError):
                raise ValueError(
                    f"Error syntax, "
                    f"'values' element of <{self._element_tag}> '{self._statement.name}' "
                    f"is invalid: {self._statement.values}"
                ) from None
            self._mode = self._VALUES_MODE
        elif self._statement.generator is not None:
            # Try to init generator with or without args.
            try:
                self._generator = GeneratorUtil(ctx).create_generator(
                    self._statement.generator,
                    self._statement,
                    self._pagination,
                    key=self._statement.full_name,
                )
                self._mode = self._GENERATOR_MODE
            # If init generator failed while creating task, try to lazy-init in the first task execution
            except:  # noqa: E722
                self._mode = self._LAZY_GENERATOR_MODE
        elif self._statement.source is not None:
            source = self._statement.source
            if not source.endswith("wgt.csv"):
                raise ValueError(f"Data source of attribute '{self._statement.name}' must be type of: 'wgt.csv'")
            separator = self._statement.separator or ctx.default_separator
            self._generator = WeightedDataSource(file_path=ctx.descriptor_dir / source, separator=separator)
            self._mode = self._GENERATOR_MODE
        elif self._statement.pattern is not None:
            self._mode = self._PATTERN_MODE
        # IMPORTANT: always put this condition at the end
        # because this mode should only be active after checking all other ones
        elif self._statement.type is not None:
            self._mode = self._RANDOM_MODE
        else:
            raise ValueError(f"Cannot init generation mode for element '{self.statement.name}'")

    @abstractmethod
    def execute(self, ctx: Context | GenIterContext | SetupContext) -> None:
        pass

    @property
    @abstractmethod
    def statement(self) -> KeyStatement | VariableStatement | ElementStatement:
        return self._statement

    def _generate_value(self, ctx: Context):
        """
        Generate data based on generation mode
        :param ctx:
        """
        from datamimic_ce.tasks.task_util import TaskUtil

        if self._mode == self._SCRIPT_MODE:
            try:
                if self._statement.script is not None:
                    value = ctx.evaluate_python_expression(self._statement.script)
            except Exception as e:
                if self._statement.default_value is not None:
                    value = (
                        None
                        if self._statement.default_value == "None"
                        else ctx.evaluate_python_expression(self._statement.default_value)
                    )
                else:
                    raise ValueError(f"Failed when execute script of element '{self._statement.name}': {str(e)}") from e
            # Throw error if <key> evaluated script get not simple data type
            if (
                self._element_tag == "key"
                and isinstance(value, Iterable)
                and not isinstance(value, str)
                and not (isinstance(value, dict) and "#text" in value)
            ):
                raise ValueError(
                    f"<key> '{self._statement.name}' expects simple data type, "
                    f"but get invalid value '{value}' with type '{type(value).__name__}'"
                )
        elif self._mode == self._CONSTANT_MODE:
            value = self._statement.constant
        elif self._mode == self._STRING_MODE:
            self._prefix = self.statement.variable_prefix or ctx.root.default_variable_prefix
            self._suffix = self.statement.variable_suffix or ctx.root.default_variable_suffix
            value = TaskUtil.evaluate_variable_concat_prefix_suffix(
                context=ctx,
                expr=self.statement.string or "",
                prefix=self._prefix,
                suffix=self._suffix,
            )
        elif self._mode == self._VALUES_MODE:
            # Return None if self._values is None
            value = None if self._values is None else random.choice(self._values)
        elif self._mode == self._LAZY_GENERATOR_MODE:
            # Try to init generator again in first task execution
            self._generator = (
                GeneratorUtil(ctx).create_generator(
                    self._statement.generator,
                    self.statement,
                    self._pagination,
                    key=self._statement.full_name,
                )
                if self._statement.generator is not None
                else None
            )
            # Switch mode to GENERATE_MODE for next task execution
            self._mode = self._GENERATOR_MODE
            if self._generator is not None and isinstance(self._generator, SequenceTableGenerator):
                value = self._generator.generate(ctx)
            elif self._generator is not None:
                value = self._generator.generate()
            else:
                value = None
        elif self._mode == self._GENERATOR_MODE:
            if self._statement.generator is not None and self._generator is None:
                self._generator = GeneratorUtil(ctx).create_generator(
                    self._statement.generator,
                    self.statement,
                    self._pagination,
                    key=self._statement.full_name,
                )
            value = self._generator.generate() if self._generator is not None else None
            # Convert numpy.bool_ to bool for being compatible with consumer (db,...)
            if isinstance(value, numpy.bool_):
                value = bool(value)
        elif self._mode == self._PATTERN_MODE:
            if self._statement.pattern is None:
                raise ValueError(f"Pattern is missing for <{self._element_tag}> '{self._statement.name}'")
            value = StringGenerator.rnd_str_from_regex(self._statement.pattern)
        elif self._mode == self._RANDOM_MODE:
            value = TaskUtil.generate_random_value_based_on_type(self._statement.type)
        else:
            raise RuntimeError(f"Cannot find data generation mode for <{self._element_tag}> '{self._statement.name}'")

        return value

    def _convert_generated_value(self, value):
        """
        Format and convert value generated by generation mode

        :return:
        """
        # Convert datetime value with inDateFormat and outDateFormat

        try:
            if self._statement.in_date_format:
                value = KeyVariableTask._convert_string_to_datetime(
                    value=value, in_date_format=self._statement.in_date_format
                )
            if self._statement.out_date_format:
                value = KeyVariableTask._convert_datetime_to_string(
                    value=value, out_date_format=self._statement.out_date_format
                )
        except ValueError as e:
            raise ValueError(
                f"Failed to convert datetime value of <{self._element_tag}> '{self._statement.name}'"
            ) from e

        # Cast data to target type
        value = self._convert_to_type(self._statement.type, value)

        # Convert data with converters (postprocessing)
        try:
            for converter in self._converter_list:
                value = converter.convert(value)
        except Exception as e:
            raise ValueError(
                f"Failed to generate data for <{self._element_tag}> '{self._statement.name}': {str(e)}"
            ) from e

        return value

    def _convert_to_type(self, data_type: str, value):
        """
        Convert generated value to defined "type"

        :param data_type:
        :param value:
        :return:
        """
        # Set default datatype in mode pattern
        if data_type is None and self._mode == self._PATTERN_MODE:
            data_type = "string"

        # Not convert if value is None
        if value is None or data_type not in self._simple_type_set:
            return value

        # Check if current type is data type then no need to cast
        if data_type == str(type(value).__name__):
            return value

        if data_type == DATA_TYPE_STRING:
            return str(value)
        elif data_type == DATA_TYPE_INT:
            return int(value)
        elif data_type == DATA_TYPE_FLOAT:
            return float(value)
        elif data_type == DATA_TYPE_BOOL:
            if value == "" or value is None:
                return None
            return value not in ("false", "False", "0", 0, False)
        elif data_type is None:
            return value
        else:
            raise ValueError(
                f"Failed to convert datatype for <{self._element_tag}> '{self._statement.name}'. "
                f"Expect datatype {', '.join(self._simple_type_set)} but get '{data_type}'"
            )

    @staticmethod
    def _convert_string_to_datetime(value: str, in_date_format: str) -> datetime:
        """
        Convert string type 'value' into datetime type data with 'in_date_format' format structure.
        Supports epoch time in seconds, milliseconds, microseconds, and nanoseconds.

        :param value: The date or epoch string to be converted.
        :param in_date_format: The format of the input date string, or 'epoch' for epoch time.
        :return: A datetime object corresponding to the input value.
        """
        if not isinstance(value, str):
            raise ValueError(f"Cannot convert datatype '{type(value).__name__}' to datetime, expect datatype string")

        if value is None or value.isspace() or value == "":
            raise ValueError("Input value is empty")

        # Check if the input format indicates an epoch time
        if in_date_format == "epoch":
            try:
                epoch_time = int(value)
                if len(value) == 10:  # Seconds
                    return datetime.fromtimestamp(epoch_time)
                elif len(value) == 13:  # Milliseconds
                    return datetime.fromtimestamp(epoch_time / 1000.0)
                elif len(value) == 16:  # Microseconds
                    seconds = epoch_time // 1000000
                    microseconds = epoch_time % 1000000
                    return datetime.fromtimestamp(seconds) + timedelta(microseconds=microseconds)
                elif len(value) == 19:  # Nanoseconds
                    seconds = epoch_time // 1000000000
                    nanoseconds = epoch_time % 1000000000
                    return datetime.fromtimestamp(seconds) + timedelta(microseconds=nanoseconds / 1000)
                else:
                    raise ValueError(
                        f"Epoch value '{value}' is not in a valid range (must be 10, 13, 16, or 19 digits)."
                    )
            except (ValueError, TypeError) as e:
                raise ValueError(f"Cannot convert string value '{value}' to epoch time") from e

        # Fallback for handling other date formats
        try:
            return datetime.strptime(value, in_date_format)
        except ValueError as e:
            raise ValueError(f"Cannot convert string value '{value}' to datetime format '{in_date_format}'") from e

    @staticmethod
    def _convert_datetime_to_string(value: datetime, out_date_format: str) -> str:
        """
        Convert datetime type 'value' into string type data with 'out_date_format' format structure.
        Supports:
        - 'epoch': returns the time as an epoch in seconds.
        - 'epoch_millis': returns the time as an epoch in milliseconds.
        - 'epoch_micros': returns the time as an epoch in microseconds.
        - 'epoch_nanos': returns the time as an epoch in nanoseconds.
        - '%Nf': allows for custom fractional second digits, where N is a number between 1 and 6 (for microseconds).

        :param value: The datetime object to be converted.
        :param out_date_format: The format string, including support for custom fractional seconds or epoch.
        :return: The formatted string representation of the datetime, or the epoch time.
        """
        if value is None:
            raise ValueError("Input value is empty")
        if not isinstance(value, datetime):
            raise ValueError(f"Cannot convert datatype '{type(value).__name__}' to string, expect datatype 'datetime'")

        # Handle custom fractional seconds formatting (e.g., %3f for milliseconds, %9f for nanoseconds)
        import re

        fractional_second_match = re.search(r"%([1-9])f", out_date_format)

        # Handle epoch time conversion
        if out_date_format == "epoch":
            return str(int(value.timestamp()))
        elif out_date_format == "epoch_millis":
            return str(int(value.timestamp() * 1000))
        elif out_date_format == "epoch_micros":
            return str(int(value.timestamp() * 1000000))
        elif out_date_format == "epoch_nanos":
            return str(int(value.timestamp() * 1000000000))
        elif fractional_second_match:
            # Extract the number of fractional digits from the format
            digits = int(fractional_second_match.group(1))

            # Format the datetime using strftime (excluding %f)
            formatted_datetime = value.strftime(out_date_format.replace(f"%{digits}f", "%f"))

            # Truncate or extend the microseconds to the required number of digits
            fractional_seconds = f"{value.microsecond:06d}"  # Get 6-digit microsecond part

            if digits <= 6:
                # If we need fewer than 6 digits, just slice the microseconds
                fractional_seconds = fractional_seconds[:digits]
            else:
                # For nanoseconds (7-9 digits), append extra nanoseconds
                nanoseconds = int(value.timestamp() * 1e9) % 1000000000  # Get the full nanoseconds part
                fractional_seconds = f"{nanoseconds:09d}"[:digits]  # Use the first 'digits' digits from nanoseconds

            # Replace the full microsecond/nanosecond part with the truncated/extended version
            formatted_datetime = formatted_datetime.replace(f"{value.microsecond:06d}", fractional_seconds)
        else:
            # For regular datetime formatting, use strftime
            try:
                formatted_datetime = value.strftime(out_date_format)
            except ValueError:
                raise ValueError(
                    f"Invalid 'out_date_format': '{out_date_format}' for datetime conversion, "
                    f"should be a valid format string or 'epoch' / 'epoch_millis' / 'epoch_micros' / 'epoch_nanos'"
                ) from None

        return formatted_datetime
