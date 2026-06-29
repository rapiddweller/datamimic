# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import ast
import uuid

from datamimic_ce.contexts.context import Context
from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.data_sources.data_source_pagination import DataSourcePagination
from datamimic_ce.domains.common.literal_generators.increment_generator import IncrementGenerator
from datamimic_ce.domains.common.literal_generators.state_transition_generator import (
    StateMachineDef,
    StateTransitionGenerator,
)
from datamimic_ce.domains.domain_core.generator_registry import generator_namespace
from datamimic_ce.enums.distribution_enums import NumberDistribution
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
        # All DSL-exposable generators, auto-discovered from the
        # literal_generators packages (no hand-maintained list).
        self._class_dict = generator_namespace()
        self._context = context

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

            # A <state-machine id="..."> registers a definition under its id; each
            # generator="<id>" reference builds its own stateful walk from it. Seed the
            # walk from <setup rngSeed> so the named state machine replays deterministically
            # (derive_seeded_rng returns None without rngSeed -> wall-clock random).
            machine_def = self._context.root.generators.get(class_name)
            if isinstance(machine_def, StateMachineDef):
                generator = StateTransitionGenerator(
                    machine_def.rules,
                    start=machine_def.start,
                    rng=self._context.root.derive_seeded_rng(),
                )
                self._context.root.generators[cache_key] = generator  # per-field reuse across rows
                return generator

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
                # Instanz-Namespaces getrennt halten, um Typkonflikte zu vermeiden.
                # NumberDistribution so the DSL can pass the real enum type, not a magic string,
                # e.g. IntegerGenerator(min=1, max=27, distribution=NumberDistribution.CUMULATED).
                local_ns_inst = {"context": self._context, "self": self, "NumberDistribution": NumberDistribution}
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
