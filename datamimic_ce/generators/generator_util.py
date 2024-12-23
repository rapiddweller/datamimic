# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import copy
import uuid

from faker import Faker

from datamimic_ce.contexts.context import Context
from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination
from datamimic_ce.generators.academic_title_generator import AcademicTitleGenerator
from datamimic_ce.generators.birthdate_generator import BirthdateGenerator
from datamimic_ce.generators.boolean_generator import BooleanGenerator
from datamimic_ce.generators.cnpj_generator import CNPJGenerator
from datamimic_ce.generators.company_name_generator import CompanyNameGenerator
from datamimic_ce.generators.cpf_generator import CPFGenerator
from datamimic_ce.generators.data_faker_generator import DataFakerGenerator
from datamimic_ce.generators.department_name_generator import DepartmentNameGenerator
from datamimic_ce.generators.domain_generator import DomainGenerator
from datamimic_ce.generators.ean_generator import EANGenerator
from datamimic_ce.generators.email_address_generator import EmailAddressGenerator
from datamimic_ce.generators.family_name_generator import FamilyNameGenerator
from datamimic_ce.generators.float_generator import FloatGenerator
from datamimic_ce.generators.gender_generator import GenderGenerator
from datamimic_ce.generators.given_name_generator import GivenNameGenerator
from datamimic_ce.generators.increment_generator import IncrementGenerator
from datamimic_ce.generators.nobility_title_generator import NobilityTitleGenerator
from datamimic_ce.generators.phone_number_generator import PhoneNumberGenerator
from datamimic_ce.generators.sector_generator import SectorGenerator
from datamimic_ce.generators.sequence_table_generator import SequenceTableGenerator
from datamimic_ce.generators.ssn_generator import SSNGenerator
from datamimic_ce.generators.street_name_generator import StreetNameGenerator
from datamimic_ce.generators.url_generator import UrlGenerator
from datamimic_ce.generators.uuid_generator import UUIDGenerator
from datamimic_ce.logger import logger
from datamimic_ce.statements.statement import Statement
from datamimic_ce.utils.string_util import StringUtil


class GeneratorUtil:
    """
    Utility class for creating and managing data generators.
    """

    def __init__(self, context: Context):
        """
        Initialize the GeneratorUtil.

        Args:
            context (Context): The context in which the generators are used.
        """
        cls_factory_util = context.root.class_factory_util
        # IMPORTANT: (Recommend) Only define generator existed in XML model
        # Should not define sub-generators (such as FamilyName, GivenName, Gender,...) here
        # because it may make users confused which ways to get FamilyName correctly
        self._class_dict = {
            "CNPJGenerator": CNPJGenerator,
            "CPFGenerator": CPFGenerator,
            "IncrementGenerator": IncrementGenerator,
            "DateTimeGenerator": cls_factory_util.get_datetime_generator(),
            "DepartmentNameGenerator": DepartmentNameGenerator,
            "BirthdateGenerator": BirthdateGenerator,
            "EmailAddressGenerator": EmailAddressGenerator,
            "DomainGenerator": DomainGenerator,
            "EANGenerator": EANGenerator,
            "SectorGenerator": SectorGenerator,
            "UUIDGenerator": UUIDGenerator,
            "BooleanGenerator": BooleanGenerator,
            "PhoneNumberGenerator": PhoneNumberGenerator,
            "IntegerGenerator": cls_factory_util.get_integer_generator(),
            "StringGenerator": cls_factory_util.get_string_generator(),
            "FloatGenerator": FloatGenerator,
            "SSNGenerator": SSNGenerator,
            "DataFakerGenerator": DataFakerGenerator,
            "AcademicTitleGenerator": AcademicTitleGenerator,
            "CompanyNameGenerator": CompanyNameGenerator,
            "FamilyNameGenerator": FamilyNameGenerator,
            "GenderGenerator": GenderGenerator,
            "GivenNameGenerator": GivenNameGenerator,
            "StreetNameGenerator": StreetNameGenerator,
            "UrlGenerator": UrlGenerator,
            "SequenceTableGenerator": SequenceTableGenerator,
            "NobilityTitleGenerator": NobilityTitleGenerator,
        }
        self._generator_with_count = (
            "DomainGenerator",
            "EmailAddressGenerator",
            "FamilyNameGenerator",
            "GivenNameGenerator",
        )
        self._generator_with_class_factory_util = (
            "IntegerGenerator",
            "StringGenerator",
            "BirthdateGenerator",
        )
        self._context = context

    def create_generator(
        self,
        generator_str: str,
        stmt: Statement,
        pagination: DataSourcePagination | None = None,
    ):
        """
        Create a generator based on the element's attribute "generator".
        Handles special cases for multi-process safe sequence generation.

        Args:
            generator_str (str): The generator string.
            stmt (Statement): The statement object.
            pagination (Optional[DataSourcePagination]): The pagination object.

        Returns:
            Any: The created generator instance.

        Raises:
            ValueError: If generator creation fails or configuration is invalid
        """
        # Set generated_count as 1 for inner geniter_context which has no pagination
        generated_count = 1 if pagination is None else pagination.limit

        try:
            # Get generator from element <generator>
            generator_from_ctx = self._context.root.generators.get(generator_str)
            if generator_from_ctx is not None:
                return generator_from_ctx

            # Get classname from constructor string
            class_name = StringUtil.get_class_name_from_constructor_string(generator_str)
            cls = self._class_dict.get(class_name)
            if cls is None:
                if isinstance(self._context, SetupContext):
                    cls = self._context.get_dynamic_class(class_name)
                elif isinstance(self._context, Context):
                    cls = self._context.root.get_dynamic_class(class_name)
                else:
                    raise ValueError(f"Cannot find generator {class_name}")

            # Initialize result variable
            result = None

            # Special handling for sequence generator in multi-process environment
            if class_name == "SequenceTableGenerator":
                # Create sequence generator with process-aware context
                result = cls(context=self._context, stmt=stmt)

                # Add pagination with process-specific adjustments if needed
                if pagination:
                    result.add_pagination(pagination=pagination)
                return result

            # Handle other generators with constructor parameters
            if class_name != generator_str:
                local_ns = copy.deepcopy(self._class_dict)
                if class_name in self._generator_with_count or class_name in self._generator_with_class_factory_util:
                    class_name, args_str = generator_str[:-1].split("(")
                    args = args_str.split(",")
                    args = [arg.strip() for arg in args]

                    if class_name in self._generator_with_count:
                        args.append(f"generated_count={generated_count}")
                    else:
                        args.append("class_factory_util=class_factory_util")
                        local_ns.update({"class_factory_util": self._context.root.class_factory_util})

                    new_args_str = ", ".join(args)
                    generator_str = f"{class_name}({new_args_str})"

                result = self._context.evaluate_python_expression(generator_str, local_ns)
            else:
                # Handle simple instance initialization
                if class_name in self._generator_with_count:
                    if class_name == "DomainGenerator":
                        result = cls(generated_count=generated_count)
                    else:
                        result = cls(
                            dataset=self._context.root.default_dataset,
                            generated_count=generated_count,
                        )
                elif class_name in self._generator_with_class_factory_util:
                    result = cls(class_factory_util=self._context.root.class_factory_util)
                else:
                    result = cls()

            # Add pagination for increment generators
            if isinstance(result, IncrementGenerator):
                result.add_pagination(pagination=pagination)

            return result

        except Exception as e:
            logger.error("Error creating generator: %s", e)
            raise ValueError(f"Cannot create generator '{class_name}' of element '{stmt.name}': {e}") from e

    @staticmethod
    def is_valid_uuid(input_string: str) -> bool:
        """
        Validate that a UUID string is in fact a valid uuid4.

        Args:
            input_string (str): The input string to validate.

        Returns:
            bool: True if the input string is a valid uuid4, False otherwise.
        """
        try:
            val = uuid.UUID(input_string, version=4)
        except ValueError:
            # If it's a value error, then the string is not a valid hex code for a UUID.
            return False

        # If the uuid_string is a valid hex code, but an invalid uuid4,
        # the UUID.__init__ will convert it to a valid uuid4. This is bad for validation purposes.
        return val.hex == input_string.replace("-", "")

    @staticmethod
    def faker_generator(
        method: str,
        locale: str | None = "en_US",
        args: str | list | None = None,
        kwargs: dict | None = None,
    ):
        """
        Generate fake data using the Faker library.

        Args:
            method (str): The Faker method to use.
            locale (Optional[str]): The locale for the Faker instance. Defaults to "en_US".
            args (Optional[Union[str, list]]): The positional arguments for the Faker method.
            kwargs (Optional[dict]): The keyword arguments for the Faker method.

        Returns:
            Any: The generated fake data.
        """
        faker = Faker(locale)
        # validation support methods
        not_support_method = [
            "seed",
            "seed_instance",
            "seed_locale",
            "provider",
            "get_providers",
            "add_provider",
        ]
        if method in not_support_method or method.startswith("_"):
            raise ValueError(f"Faker method '{method}' is not supported")
        # check worked methods
        faker_method = getattr(faker, method, "method does not exist")
        if faker_method == "method does not exist" or not callable(faker_method):
            raise ValueError(f"Wrong Faker method: {method} does not exist")
        # generate data
        if args and kwargs:
            result = faker_method(*args, **kwargs)
        elif args:
            result = faker_method(*args)
        elif kwargs:
            result = faker_method(**kwargs)
        else:
            result = faker_method()
        return result
