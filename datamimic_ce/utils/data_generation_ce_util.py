# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
import re
import string
from datetime import datetime, timedelta

import exrex  # type: ignore

from datamimic_ce.constants.data_type_constants import DATA_TYPE_BOOL, DATA_TYPE_FLOAT, DATA_TYPE_INT, DATA_TYPE_STRING
from datamimic_ce.generators.generator_util import GeneratorUtil
from datamimic_ce.utils.base_data_generation_util import BaseDataGenerationUtil


class DataGenerationCEUtil(BaseDataGenerationUtil):
    @staticmethod
    def generate_random_value_based_on_type(
        data_type: str | None = None,
    ) -> str | int | bool | float:
        if data_type == DATA_TYPE_STRING:
            min_len = 0
            max_len = 20
            return "".join(random.choice(string.ascii_letters) for _ in range(random.randint(min_len, max_len)))
        elif data_type == DATA_TYPE_INT:
            return random.randint(0, 100)
        elif data_type == DATA_TYPE_FLOAT:
            return random.uniform(0, 100)
        elif data_type == DATA_TYPE_BOOL:
            return random.choice((True, False))
        else:
            raise ValueError(f"Cannot generate random value for data type {data_type}")

    @staticmethod
    def rnd_str_from_regex(pattern: str) -> str:
        pattern = r"" + pattern
        return exrex.getone(pattern, 1)

    @staticmethod
    def convert_string_to_datetime(value: str, in_date_format: str) -> datetime:
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
        except ValueError:
            raise ValueError(f"Cannot convert string value '{value}' to datetime format '{in_date_format}'") from None

    @staticmethod
    def convert_datetime_to_string(value: datetime, out_date_format: str) -> str:
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

    @staticmethod
    def generate_credit_card_number(locale_input: str) -> str:
        """
        Generate a random credit card number for a given locale.

        :param locale_input: The locale for which the credit card number should be generated.
        :return: A random credit card number in the specified locale.
        """
        return GeneratorUtil.faker_generator(method="credit_card_number", locale=locale_input)

    @staticmethod
    def generate_card_holder(locale_input: str) -> str:
        return GeneratorUtil.faker_generator(method="name", locale=locale_input)

    @staticmethod
    def generate_cvc_number() -> str:
        return str(random.randint(100, 999))

    @staticmethod
    def generate_expiration_date(locale_input: str) -> str:
        return GeneratorUtil.faker_generator(method="credit_card_expire", locale=locale_input)

    @staticmethod
    def rnd_int(min_val: int, max_val: int) -> int:
        return random.randint(min_val, max_val)

    @staticmethod
    def rnd_str(
        char_set: str,
        min_val: int,
        max_val: int,
        unique: bool,
        prefix: str = "",
        suffix: str = "",
    ) -> str:
        try:
            # regex
            if any(c in char_set for c in ".^$*+?{}[]|()"):
                compiled_regex = re.compile(char_set)
                char_set_list = list(set(compiled_regex.findall(string.printable)))
            else:
                # simple character
                char_set_list = list(set(char_set))
        except re.error:
            char_set_list = list(set(char_set))

        # If unique, ensure each character only appears once
        if unique:
            length = random.randint(min_val, max_val)
            if len(char_set_list) < length:
                raise ValueError("Character set is too small to generate a unique string of this length.")
            result = random.sample(char_set_list, length)  # random.sample ensures uniqueness
        else:
            length = random.randint(min_val, max_val)
            result = [random.choice(char_set_list) for _ in range(length)]

        return prefix + "".join(result) + suffix

    @staticmethod
    def get_current_datetime() -> datetime:
        dt = datetime.now()
        return dt

    @staticmethod
    def get_random_datetime(start_dt: str, start_format: str, end_dt: str, end_format: str) -> datetime | str:
        try:
            start_naive_datetime = datetime.strptime(start_dt, start_format)
            end_naive_datetime = datetime.strptime(end_dt, end_format)
            # Calculate the duration between the two datetime objects
            duration = (end_naive_datetime - start_naive_datetime).total_seconds()
            # Generate random seconds in the range [0, duration]
            random_seconds = random.uniform(0, duration)
            # Add random seconds to the start time
            random_datetime = start_naive_datetime + timedelta(seconds=random_seconds)
            return random_datetime
        except Exception as e:
            return f"Error occurred while getting random datetime: {str(e)}"
