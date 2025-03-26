# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import copy
import uuid

from faker import Faker

from datamimic_ce.contexts.context import Context
from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination
from datamimic_ce.domains.common.literal_generators.academic_title_generator import AcademicTitleGenerator
from datamimic_ce.domains.common.literal_generators.birthdate_generator import BirthdateGenerator
from datamimic_ce.domains.common.literal_generators.boolean_generator import BooleanGenerator
from datamimic_ce.domains.common.literal_generators.cnpj_generator import CNPJGenerator
from datamimic_ce.domains.common.literal_generators.color_generators import ColorGenerator
from datamimic_ce.domains.common.literal_generators.company_name_generator import CompanyNameGenerator
from datamimic_ce.domains.common.literal_generators.cpf_generator import CPFGenerator
from datamimic_ce.domains.common.literal_generators.data_faker_generator import DataFakerGenerator
from datamimic_ce.domains.common.literal_generators.department_name_generator import DepartmentNameGenerator
from datamimic_ce.domains.common.literal_generators.domain_generator import DomainGenerator
from datamimic_ce.domains.common.literal_generators.ean_generator import EANGenerator
from datamimic_ce.domains.common.literal_generators.email_address_generator import EmailAddressGenerator
from datamimic_ce.domains.common.literal_generators.family_name_generator import FamilyNameGenerator
from datamimic_ce.domains.common.literal_generators.float_generator import FloatGenerator
from datamimic_ce.domains.common.literal_generators.gender_generator import GenderGenerator
from datamimic_ce.domains.common.literal_generators.given_name_generator import GivenNameGenerator
from datamimic_ce.domains.common.literal_generators.hash_generator import HashGenerator
from datamimic_ce.domains.common.literal_generators.increment_generator import IncrementGenerator
from datamimic_ce.domains.common.literal_generators.nobility_title_generator import NobilityTitleGenerator
from datamimic_ce.domains.common.literal_generators.password_generator import PasswordGenerator
from datamimic_ce.domains.common.literal_generators.phone_number_generator import PhoneNumberGenerator
from datamimic_ce.domains.common.literal_generators.sector_generator import SectorGenerator
from datamimic_ce.domains.common.literal_generators.sequence_table_generator import SequenceTableGenerator
from datamimic_ce.domains.common.literal_generators.ssn_generator import SSNGenerator
from datamimic_ce.domains.common.literal_generators.street_name_generator import StreetNameGenerator
from datamimic_ce.domains.common.literal_generators.token_generator import TokenGenerator
from datamimic_ce.domains.common.literal_generators.url_generator import UrlGenerator
from datamimic_ce.domains.common.literal_generators.uuid_generator import UUIDGenerator
from datamimic_ce.logger import logger
from datamimic_ce.statements.statement import Statement


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
        # Define all available generators
        self._class_dict = {
            # Basic Generators
            "IncrementGenerator": IncrementGenerator,
            "DateTimeGenerator": cls_factory_util.get_datetime_generator(),
            "IntegerGenerator": cls_factory_util.get_integer_generator(),
            "StringGenerator": cls_factory_util.get_string_generator(),
            "FloatGenerator": FloatGenerator,
            "BooleanGenerator": BooleanGenerator,
            "DataFakerGenerator": DataFakerGenerator,
            # Identity and Personal Information
            "SSNGenerator": SSNGenerator,
            "CNPJGenerator": CNPJGenerator,
            "CPFGenerator": CPFGenerator,
            "EANGenerator": EANGenerator,
            "GenderGenerator": GenderGenerator,
            "BirthdateGenerator": BirthdateGenerator,
            "PhoneNumberGenerator": PhoneNumberGenerator,
            # Names and Titles
            "FamilyNameGenerator": FamilyNameGenerator,
            "GivenNameGenerator": GivenNameGenerator,
            "AcademicTitleGenerator": AcademicTitleGenerator,
            "NobilityTitleGenerator": NobilityTitleGenerator,
            # Business and Organization
            "CompanyNameGenerator": CompanyNameGenerator,
            "DepartmentNameGenerator": DepartmentNameGenerator,
            "SectorGenerator": SectorGenerator,
            # Internet and Web
            "EmailAddressGenerator": EmailAddressGenerator,
            "DomainGenerator": DomainGenerator,
            "UrlGenerator": UrlGenerator,
            # Location
            "StreetNameGenerator": StreetNameGenerator,
            # Security
            "UUIDGenerator": UUIDGenerator,
            "HashGenerator": HashGenerator,
            "TokenGenerator": TokenGenerator,
            "PasswordGenerator": PasswordGenerator,
            # Visual and Design
            "ColorGenerator": ColorGenerator,
            # Healthcare
            "SequenceTableGenerator": SequenceTableGenerator,
        }

        self._generator_with_class_factory_util = (
            "IntegerGenerator",
            "StringGenerator",
            "BirthdateGenerator",
        )
        self._context = context

    def get_supported_generators(self) -> dict[str, list[str]]:
        """
        Get a dictionary of all supported generators organized by category.

        Returns:
            Dict[str, List[str]]: Dictionary with categories as keys and lists of generator names as values
        """
        return {
            "Basic": [
                "IncrementGenerator",
                "DateTimeGenerator",
                "IntegerGenerator",
                "StringGenerator",
                "FloatGenerator",
                "BooleanGenerator",
                "DataFakerGenerator",
            ],
            "Identity and Personal": [
                "SSNGenerator",
                "CNPJGenerator",
                "CPFGenerator",
                "EANGenerator",
                "GenderGenerator",
                "BirthdateGenerator",
                "PhoneNumberGenerator",
            ],
            "Names and Titles": [
                "FamilyNameGenerator",
                "GivenNameGenerator",
                "AcademicTitleGenerator",
                "NobilityTitleGenerator",
            ],
            "Business": [
                "CompanyNameGenerator",
                "DepartmentNameGenerator",
                "SectorGenerator",
                "JobTitleGenerator",
                "CreditCardGenerator",
                "CurrencyGenerator",
            ],
            "Internet": [
                "EmailAddressGenerator",
                "DomainGenerator",
                "UrlGenerator",
            ],
            "Location": [
                "StreetNameGenerator",
            ],
            "Document": [
                "ISBNGenerator",
                "FilePathGenerator",
                "MIMETypeGenerator",
            ],
            "Security": [
                "UUIDGenerator",
                "HashGenerator",
                "TokenGenerator",
                "MnemonicPhraseGenerator",
                "PasswordGenerator",
            ],
            "Text": [
                "ParagraphGenerator",
            ],
            "Visual": [
                "ColorGenerator",
            ],
            "Science": [
                "ChemicalFormulaGenerator",
                "NucleotideSequenceGenerator",
                "PhysicalConstantGenerator",
                "ScientificUnitGenerator",
            ],
            "Healthcare": [
                "AllergyGenerator",
                "DiagnosisGenerator",
                "ImmunizationGenerator",
                "LabResultGenerator",
                "MedicalAppointmentGenerator",
                "MedicalProcedureGenerator",
                "MedicationGenerator",
                "PatientHistoryGenerator",
                "SymptomGenerator",
                "VitalSignsGenerator",
            ],
            "Special": [
                "SequenceTableGenerator",
            ],
        }

    def get_all_generator_names(self) -> list[str]:
        """
        Get a flat list of all supported generator names.

        Returns:
            List[str]: List of all generator names
        """
        return sorted(self._class_dict.keys())

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
        try:
            # Get generator from element <generator>
            generator_from_ctx = self._context.root.generators.get(generator_str)
            if generator_from_ctx is not None:
                return generator_from_ctx

            # Parse generator string into type and parameters
            if "(" in generator_str:
                class_name, params_str = generator_str[:-1].split("(", 1)
                params: dict[str, str | bool | int | float] = {}

                # Special handling for DataFakerGenerator with positional argument
                if class_name == "DataFakerGenerator" and "'" in params_str:
                    # Extract the method name (first positional argument)
                    method = params_str.split(",")[0].strip("' ")
                    params["method"] = method

                    # Parse remaining parameters if any
                    if "," in params_str:
                        remaining_params = params_str[params_str.find(",") + 1 :].strip()
                        if remaining_params:
                            for param in remaining_params.split(","):
                                if "=" not in param:
                                    continue
                                key, value = param.split("=", 1)
                                key = key.strip()
                                value = value.strip()

                                # Handle string values
                                if value.startswith("'") and value.endswith("'"):
                                    value = value[1:-1]
                                # Handle boolean values
                                elif value.lower() in ("true", "false"):
                                    value = str(value.lower() == "true")
                                # Handle numeric values
                                elif value.isdigit():
                                    value = str(int(value))
                                elif value.replace(".", "").isdigit():
                                    value = str(float(value))

                                params[key] = value
                else:
                    # Normal parameter parsing for other generators
                    if params_str:
                        for param in params_str.split(","):
                            if "=" not in param:
                                continue
                            key, value = param.split("=", 1)
                            key = key.strip()
                            value = value.strip()

                            # Handle string values
                            if value.startswith("'") and value.endswith("'"):
                                value = value[1:-1]
                            # Handle boolean values
                            elif value.lower() in ("true", "false"):
                                value = str(value.lower() == "true")
                            # Handle numeric values
                            elif value.isdigit():
                                value = str(int(value))
                            elif value.replace(".", "").isdigit():
                                value = str(float(value))

                            params[key] = value
            else:
                class_name = generator_str
                params = {}

            # Get generator class
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
                if class_name in self._generator_with_class_factory_util:
                    class_name, args_str = generator_str[:-1].split("(")
                    # Filtering out empty arguments to avoid extra commas
                    args = [arg.strip() for arg in args_str.split(",") if arg.strip()]

                    args.append("class_factory_util=class_factory_util")
                    local_ns.update({"class_factory_util": self._context.root.class_factory_util})

                    new_args_str = ", ".join(args)
                    generator_str = f"{class_name}({new_args_str})"

                result = self._context.evaluate_python_expression(generator_str, local_ns)
            else:
                if class_name in ["EmailAddressGenerator", "FamilyNameGenerator", "GivenNameGenerator"]:
                    result = cls(
                        dataset=self._context.root.default_dataset,
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
