# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import ast
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
from datamimic_ce.domains.common.literal_generators.datetime_generator import DateTimeGenerator
from datamimic_ce.domains.common.literal_generators.department_name_generator import DepartmentNameGenerator
from datamimic_ce.domains.common.literal_generators.domain_generator import DomainGenerator
from datamimic_ce.domains.common.literal_generators.ean_generator import EANGenerator
from datamimic_ce.domains.common.literal_generators.email_address_generator import EmailAddressGenerator
from datamimic_ce.domains.common.literal_generators.family_name_generator import FamilyNameGenerator
from datamimic_ce.domains.common.literal_generators.float_generator import FloatGenerator
from datamimic_ce.domains.common.literal_generators.gender_generator import GenderGenerator
from datamimic_ce.domains.common.literal_generators.given_name_generator import GivenNameGenerator
from datamimic_ce.domains.common.literal_generators.global_increment_generator import GlobalIncrementGenerator
from datamimic_ce.domains.common.literal_generators.hash_generator import HashGenerator
from datamimic_ce.domains.common.literal_generators.increment_generator import IncrementGenerator
from datamimic_ce.domains.common.literal_generators.integer_generator import IntegerGenerator
from datamimic_ce.domains.common.literal_generators.nobility_title_generator import NobilityTitleGenerator
from datamimic_ce.domains.common.literal_generators.password_generator import PasswordGenerator
from datamimic_ce.domains.common.literal_generators.phone_number_generator import PhoneNumberGenerator
from datamimic_ce.domains.common.literal_generators.sector_generator import SectorGenerator
from datamimic_ce.domains.common.literal_generators.sequence_table_generator import SequenceTableGenerator
from datamimic_ce.domains.common.literal_generators.ssn_generator import SSNGenerator
from datamimic_ce.domains.common.literal_generators.street_name_generator import StreetNameGenerator
from datamimic_ce.domains.common.literal_generators.string_generator import StringGenerator
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
        # Define all available generators
        self._class_dict = {
            # Basic Generators
            "IncrementGenerator": IncrementGenerator,
            "DateTimeGenerator": DateTimeGenerator,
            "IntegerGenerator": IntegerGenerator,
            "StringGenerator": StringGenerator,
            "FloatGenerator": FloatGenerator,
            "BooleanGenerator": BooleanGenerator,
            "DataFakerGenerator": DataFakerGenerator,
            "GlobalIncrementGenerator": GlobalIncrementGenerator,
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
        key: str | None = None,
    ):
        """
        Create a generator based on the element's attribute "generator".
        Handles special cases for multi-process safe sequence generation.

        Args:
            generator_str (str): The generator string.
            stmt (Statement): The statement object.
            pagination (Optional[DataSourcePagination]): The pagination object.
            key (Optional[str]): Key used for root-level caching. If provided,
                the generator will be stored and retrieved using this key
                instead of the raw ``generator_str``.

        Returns:
            Any: The created generator instance.

        Raises:
            ValueError: If generator creation fails or configuration is invalid
        """
        try:
            # Get generator from element <generator>
            cache_key = key or generator_str
            generator_from_ctx = self._context.root.generators.get(cache_key)
            if generator_from_ctx is not None:
                return generator_from_ctx

            # Parse generator string into type and parameters
            class_name: str
            if "(" in generator_str:
                class_name_candidate, _ = generator_str.split("(", 1)
                class_name = class_name_candidate.strip()
            else:
                class_name = generator_str.strip()

            # Get generator class
            cls = self._class_dict.get(class_name)
            if cls is None:
                if isinstance(self._context, SetupContext):
                    cls = self._context.get_dynamic_class(class_name)
                elif isinstance(self._context, Context):
                    cls = self._context.root.get_dynamic_class(class_name)
                else:
                    raise ValueError(f"Cannot find generator class for '{class_name}'")

            result = None

            if class_name == "GlobalIncrementGenerator":
                # Build the fully qualified key path for uniqueness
                # Traverse up the statement tree to build the path
                path = []
                current = stmt
                while current is not None and hasattr(current, "name"):
                    path.append(current.name)
                    current = getattr(current, "parent", None)  # type: ignore
                qualified_key = ".".join(reversed(path))  # type: ignore
                result = cls(qualified_key=qualified_key, context=self._context)
                # Use unified cache key (may differ from generator_str when a key is provided)
                self._context.root.generators[cache_key] = result
                return result

            if class_name == "SequenceTableGenerator":
                result = cls(context=self._context, stmt=stmt)
                if pagination:
                    result.add_pagination(pagination=pagination)
                # Use unified cache key (may differ from generator_str when a key is provided)
                self._context.root.generators[cache_key] = result
                return result

            # --- DateTimeGenerator special parsing ---
            if class_name == "DateTimeGenerator":
                try:
                    module_node = ast.parse(generator_str)
                    if not (
                        module_node.body
                        and isinstance(module_node.body[0], ast.Expr)
                        and isinstance(module_node.body[0].value, ast.Call)
                    ):
                        pass
                    else:
                        call_node = module_node.body[0].value
                        if not (isinstance(call_node.func, ast.Name) and call_node.func.id == "DateTimeGenerator"):
                            pass
                        else:
                            parsed_constructor_args = {}
                            for kw in call_node.keywords:
                                param_name = kw.arg
                                if param_name is None:
                                    raise ValueError(f"Keyword argument name is None in {generator_str}")
                                value_str = ast.get_source_segment(generator_str, kw.value)
                                if value_str is None:
                                    raise ValueError(
                                        f"Could not extract source for param {param_name} in {generator_str}"
                                    )
                                if param_name in (
                                    "hour_weights",
                                    "minute_weights",
                                    "second_weights",
                                    "month_weights",
                                    "weekday_weights",
                                    "dom_weights",
                                ):
                                    # Typkorrektur: param_name ist str, nicht str | None
                                    # Entferne äußere Hochkommas, falls vorhanden
                                    if (value_str.startswith("'") and value_str.endswith("'")) or (
                                        value_str.startswith('"') and value_str.endswith('"')
                                    ):
                                        value_str = value_str[1:-1]
                                    try:
                                        parsed_constructor_args[param_name] = self._context.evaluate_python_expression(
                                            value_str
                                        )
                                    except (ValueError, SyntaxError, NameError, TypeError) as eval_exc:
                                        try:
                                            parsed_constructor_args[param_name] = ast.literal_eval(value_str)
                                        except (ValueError, SyntaxError) as lit_exc:
                                            logger.error(f"Fehler beim Parsen von {param_name}: {eval_exc} / {lit_exc}")
                                            raise ValueError(
                                                f"Konnte {param_name} nicht als Liste parsen: {value_str}"
                                            ) from eval_exc
                                else:
                                    parsed_constructor_args[param_name] = ast.literal_eval(value_str)
                            if call_node.args:
                                logger.warning(
                                    f"Positional args are not processed for DateTimeGenerator string: {generator_str}"
                                )
                            result = cls(**parsed_constructor_args)
                            # Use unified cache key for consistency with global cache
                            self._context.root.generators[cache_key] = result
                            return result
                except (ValueError, SyntaxError, TypeError) as e_dt_parse:
                    logger.error(
                        f"Failed to parse DateTimeGenerator arguments from '{generator_str}' using ast: {e_dt_parse}"
                    )
                    raise ValueError(
                        f"Error parsing parameters for DateTimeGenerator from '{generator_str}': {e_dt_parse}"
                    ) from e_dt_parse
            # --- End DateTimeGenerator special parsing ---

            # Fallback: evaluate_python_expression for other generators with params
            if "(" in generator_str:
                # A shallow copy is sufficient here and avoids recursion issues
                # with certain generator classes like ``SequenceTableGenerator``.
                local_ns = self._class_dict.copy()
                # Instanz-Namespaces getrennt halten, um Typkonflikte zu vermeiden
                local_ns_inst = {"context": self._context, "self": self}
                try:
                    result = self._context.evaluate_python_expression(generator_str, {**local_ns, **local_ns_inst})
                except (ValueError, SyntaxError, NameError, TypeError) as e_eval:
                    logger.error(
                        f"Error evaluating generator string '{generator_str}' with evaluate_python_expression: {e_eval}"
                    )
                    raise ValueError(
                        f"Cannot create generator '{class_name}' from string '{generator_str}' using evaluate: {e_eval}"
                    ) from e_eval
            else:
                if class_name in ["EmailAddressGenerator", "FamilyNameGenerator", "GivenNameGenerator"]:
                    result = cls(dataset=self._context.root.default_dataset)
                else:
                    result = cls()
            if isinstance(result, IncrementGenerator):
                if hasattr(result, "add_pagination") and callable(result.add_pagination):
                    result.add_pagination(pagination=pagination)
                else:
                    logger.warning(f"Generator {class_name} is IncrementGenerator but lacks add_pagination method.")
            if result is None:
                raise ValueError(f"Failed to create generator for '{generator_str}': result is None.")

            # Decide whether to cache the generator instance globally. Generators
            # can opt out by defining ``cache_in_root = False``.
            if getattr(result, "cache_in_root", True):
                self._context.root.generators[cache_key] = result

            return result
        except (ValueError, SyntaxError, NameError, TypeError) as e:
            current_class_name = class_name if "class_name" in locals() else generator_str
            element_name_str = f" of element '{stmt.name}'" if stmt and hasattr(stmt, "name") else ""
            logger.error(f"Error creating generator '{current_class_name}'{element_name_str}: {e}")
            if not isinstance(e, ValueError):
                raise ValueError(f"Cannot create generator '{current_class_name}'{element_name_str}: {e}") from e
            else:
                raise

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
