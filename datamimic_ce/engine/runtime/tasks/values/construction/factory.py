# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import ast
import functools
import inspect
import logging
import random
import string
from decimal import Decimal
from typing import Protocol, get_args, runtime_checkable

from datamimic_ce.domains.api import (
    BaseDomainGenerator,
    BaseLiteralGenerator,
    IncrementGenerator,
    StateMachineDef,
    StateTransitionGenerator,
    iter_generator_types,
)
from datamimic_ce.engine.dsl.api import (
    ATTR_GENERATOR,
    DATA_TYPE_BINARY,
    DATA_TYPE_BOOL,
    DATA_TYPE_DECIMAL,
    DATA_TYPE_FLOAT,
    DATA_TYPE_INT,
    DATA_TYPE_STRING,
    EL_KEY,
    NumberDistribution,
    Statement,
)
from datamimic_ce.engine.io.api import DataSourcePagination
from datamimic_ce.engine.runtime.contexts.context import Context, SetupContext
from datamimic_ce.engine.runtime.tasks.values.construction.global_increment import GlobalIncrementGenerator
from datamimic_ce.engine.runtime.tasks.values.construction.sequence_table import SequenceTableGenerator
from datamimic_ce.errors import (
    DescriptorLocation,
    DomainError,
    IssueCode,
    UserErrorBase,
    generator_config_error,
    is_user_error,
)
from datamimic_ce.randomness import RandomSource

logger = logging.getLogger("DATAMIMIC")

RUNTIME_GENERATOR_TYPES: tuple[type[BaseLiteralGenerator], ...] = (
    GlobalIncrementGenerator,
    SequenceTableGenerator,
)


def generate_random_value_based_on_type(
    data_type: str | None,
    *,
    rng: RandomSource,
) -> str | int | bool | float | Decimal | bytes:
    # ``rng`` is required: callers inject the GenIterContext's rng so seeded runs propagate fully.
    if data_type == DATA_TYPE_STRING:
        min_len = 0
        max_len = 20
        return "".join(rng.choice(string.ascii_letters) for _ in range(rng.randint(min_len, max_len)))
    elif data_type == DATA_TYPE_INT:
        return rng.randint(0, 100)
    elif data_type == DATA_TYPE_FLOAT:
        return rng.uniform(0, 100)
    elif data_type == DATA_TYPE_DECIMAL:
        # fixed 2dp default for bare type="decimal"; use a DecimalGenerator for other scales
        return Decimal(str(round(rng.uniform(0, 100), 2)))
    elif data_type == DATA_TYPE_BOOL:
        return rng.choice((True, False))
    elif data_type == DATA_TYPE_BINARY:
        return rng.randbytes(rng.randint(1, 16))  # same default range as BinaryGenerator
    else:
        raise ValueError(f"Cannot generate random value for data type {data_type}")


@runtime_checkable
class CachePolicy(Protocol):
    cache_in_root: bool


@functools.cache  # a class's __init__ signature is static
def _is_rng_generator(obj: type) -> bool:
    """A generator class that owns a *seedable* rng: an rng-driven literal/domain generator whose __init__
    takes an ``rng`` kwarg. Increment/sequence generators subclass the base but override __init__ without
    ``rng`` (they don't draw on it), so they are excluded — passing rng to them would raise."""
    return issubclass(obj, BaseLiteralGenerator | BaseDomainGenerator) and "rng" in inspect.signature(obj).parameters


def _bind_rng(obj: object, rng: random.Random) -> object:
    """Construct-time seeding: wrap an rng-driven generator class so it is built with the seeded rng."""
    return functools.partial(obj, rng=rng) if isinstance(obj, type) and _is_rng_generator(obj) else obj


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
        # Domain literals are discovered; database sequence generation is runtime-owned.
        self._class_dict: dict[str, type] = {
            generator_type.__name__: generator_type
            for generator_type in (*iter_generator_types(), *RUNTIME_GENERATOR_TYPES)
        }
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
            object: The created generator instance.

        Raises:
            ValueError: If generator creation fails or configuration is invalid
        """
        diagnostic_class_name = "generator"
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

            # A setup <generator name="..."> is one explicitly shared instance.
            # Ordinary constructor fields still use their own qualified cache keys;
            # machine definitions above still build independent per-field walks.
            if generator_str.strip() == class_name and machine_def is not None:
                self._context.root.generators[cache_key] = machine_def
                return machine_def

            # Get generator class
            cls = self._class_dict.get(class_name)
            if cls is None:
                dynamic_class: object | None
                if isinstance(self._context, SetupContext):
                    dynamic_class = self._context.get_dynamic_class(class_name)
                elif isinstance(self._context, Context):
                    dynamic_class = self._context.root.get_dynamic_class(class_name)
                else:
                    raise ValueError(f"Cannot find generator class for '{class_name}'")
                cls = dynamic_class if isinstance(dynamic_class, type) else None
            if cls is not None:
                diagnostic_class_name = cls.__name__

            result = None

            if class_name == "GlobalIncrementGenerator":
                if cls is None:
                    raise TypeError("'NoneType' object is not callable")
                # Build the fully qualified key path for uniqueness
                # Traverse up the statement tree to build the path
                path: list[str] = []
                current: Statement | None = stmt
                while current is not None:
                    if current.name is not None:
                        path.append(current.name)
                    current = current.parent_stmt
                qualified_key = ".".join(reversed(path))
                result = cls(qualified_key=qualified_key, context=self._context)
                # Use unified cache key (may differ from generator_str when a key is provided)
                self._context.root.generators[cache_key] = result
                return result

            if class_name == "SequenceTableGenerator":
                if cls is None:
                    raise TypeError("'NoneType' object is not callable")
                # Optional explicit sequence name: SequenceTableGenerator(sequence='zsv.t_angebote_id_seq')
                # (explicitly named native DB sequences, migration parity). ast-parsed like DateTimeGenerator below, but
                # keyword-only and single-kwarg - anything else raises, args are never silently dropped.
                parsed_sequence = GeneratorUtil._parse_sequence_kwarg(generator_str)
                result = cls(context=self._context, stmt=stmt, sequence=parsed_sequence)
                if pagination:
                    result.add_pagination(pagination=pagination)
                    # Cache only generation-ready (paginated) instances. GenerateTask.pre_execute
                    # builds its sub-tasks with pagination=None; caching that instance under the
                    # same full_name|generator cache key the paginated page-tasks use later made
                    # every single-process run hit _current=None -> StopIteration on the first
                    # record -> 0 rows (only the numProcess=2 path had coverage, masking this).
                    self._context.root.generators[cache_key] = result
                return result

            # --- DateTimeGenerator special parsing ---
            if class_name == "DateTimeGenerator":
                if cls is None:
                    raise TypeError("'NoneType' object is not callable")
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
                                            value_str, diagnostic_expression=f"DateTimeGenerator.{param_name}"
                                        )
                                    except (UserErrorBase, DomainError):
                                        raise
                                    except (ValueError, SyntaxError, NameError, TypeError) as eval_exc:
                                        try:
                                            parsed_constructor_args[param_name] = ast.literal_eval(value_str)
                                        except (ValueError, SyntaxError):
                                            raise generator_config_error(
                                                reason=f"DateTimeGenerator {param_name} must be a valid list."
                                            ) from eval_exc
                                else:
                                    parsed_constructor_args[param_name] = ast.literal_eval(value_str)
                            if call_node.args:
                                logger.warning(
                                    "Positional args are not processed for DateTimeGenerator; use keyword arguments"
                                )
                            # Seed at construction under <setup rngSeed> (this branch bypasses the eval-path
                            # rng binding below), unless the DSL already pinned seed=/rng= explicitly.
                            dt_rng = self._context.root.derive_seeded_rng()
                            if dt_rng is not None and not {"rng", "seed"} & parsed_constructor_args.keys():
                                parsed_constructor_args["rng"] = dt_rng
                            result = cls(**parsed_constructor_args)
                            # Use unified cache key for consistency with global cache
                            self._context.root.generators[cache_key] = result
                            return result
                except (UserErrorBase, DomainError):
                    raise
                except (ValueError, SyntaxError, TypeError) as e_dt_parse:
                    raise generator_config_error(
                        code=IssueCode.GENERATOR_CREATE_FAILED,
                        class_name="DateTimeGenerator",
                        element_name=stmt.name,
                        error=type(e_dt_parse).__name__,
                    ) from e_dt_parse
            # --- End DateTimeGenerator special parsing ---

            # Seed at CONSTRUCTION under <setup rngSeed>: an rng-driven generator (literal OR domain) must
            # receive the seeded rng in __init__ so a COMPOSITE domain generator threads it to the children
            # it builds there (post-construction rebinding cannot reach already-built children). Without a
            # seed, derive_seeded_rng() returns None and generators keep their own wall-clock rng.
            seeded_rng = self._context.root.derive_seeded_rng()

            # Fallback: evaluate_python_expression for other generators with params
            if "(" in generator_str:
                # A shallow copy is sufficient here and avoids recursion issues
                # with certain generator classes like ``SequenceTableGenerator``.
                local_ns = self._class_dict.copy()
                # Instanz-Namespaces getrennt halten, um Typkonflikte zu vermeiden.
                # NumberDistribution so the DSL can pass the real enum type, not a magic string,
                # e.g. IntegerGenerator(min=1, max=27, distribution=NumberDistribution.CUMULATED).
                local_ns_inst = {"context": self._context, "self": self, "NumberDistribution": NumberDistribution}
                namespace = {**local_ns, **local_ns_inst}
                if seeded_rng is not None:
                    namespace = {name: _bind_rng(obj, seeded_rng) for name, obj in namespace.items()}
                try:
                    result = self._context.evaluate_python_expression(
                        generator_str, namespace, diagnostic_expression=diagnostic_class_name
                    )
                except (UserErrorBase, DomainError):
                    raise
                except (ValueError, SyntaxError, NameError, TypeError) as e_eval:
                    raise generator_config_error(
                        code=IssueCode.GENERATOR_CREATE_FAILED,
                        class_name=diagnostic_class_name,
                        element_name=stmt.name,
                        error=type(e_eval).__name__,
                    ) from e_eval
            else:
                seed_kw = (
                    {"rng": seeded_rng} if seeded_rng is not None and cls is not None and _is_rng_generator(cls) else {}
                )
                if cls is None:
                    raise TypeError("'NoneType' object is not callable")
                if class_name in ["EmailAddressGenerator", "FamilyNameGenerator", "GivenNameGenerator"]:
                    result = cls(dataset=self._context.root.default_dataset, **seed_kw)
                else:
                    result = cls(**seed_kw)
            if isinstance(result, IncrementGenerator) and pagination is not None:
                result.add_pagination(skip=pagination.skip, limit=pagination.limit)
            if result is None:
                raise ValueError(f"Failed to create generator for '{generator_str}': result is None.")

            # Decide whether to cache the generator instance globally. Generators
            # can opt out by defining ``cache_in_root = False``.
            if not isinstance(result, CachePolicy) or result.cache_in_root:
                self._context.root.generators[cache_key] = result

            return result
        except (ValueError, SyntaxError, NameError, TypeError) as e:
            if is_user_error(e):
                raise
            raise generator_config_error(
                code=IssueCode.GENERATOR_CREATE_FAILED,
                class_name=diagnostic_class_name,
                element_name=stmt.name,
                error=type(e).__name__,
            ) from e

    def attribute_call(self, generator: str, arguments: dict[str, str], key_name: str) -> str:
        """Render <key generator="G" min="1" max="9"> as the call G(min=1, max=9), so the attribute form and the
        call form build the same generator from the same seed. The constructor signature decides what G takes."""
        location = DescriptorLocation(EL_KEY, attribute=ATTR_GENERATOR)
        try:
            expression: ast.expr | None = ast.parse(generator.strip(), mode="eval").body
        except SyntaxError:
            expression = None
        if isinstance(expression, ast.Call):
            raise generator_config_error(
                code=IssueCode.GENERATOR_ARGUMENTS_IN_TWO_FORMS, element_name=key_name, location=location
            )
        cls = self._class_dict.get(expression.id) if isinstance(expression, ast.Name) else None
        if cls is None:
            # Only a built-in class has a signature to check against; an unknown name is descriptor text, so the
            # message names the role, as create_generator does.
            raise generator_config_error(
                code=IssueCode.GENERATOR_CREATE_FAILED,
                class_name="generator",
                element_name=key_name,
                error=NameError.__name__,
                location=location,
            )
        parameters = inspect.signature(cls, eval_str=True).parameters
        rendered: list[str] = []
        for name, text in arguments.items():
            parameter = parameters.get(name)
            if parameter is None:
                raise generator_config_error(
                    code=IssueCode.GENERATOR_ARGUMENT_UNKNOWN,
                    element_name=key_name,
                    class_name=cls.__name__,
                    attribute=name,
                    location=DescriptorLocation(EL_KEY, attribute=name),
                )
            # A text parameter (DateTimeGenerator min) takes the attribute as written; the call form quotes it.
            if str in (get_args(parameter.annotation) or (parameter.annotation,)):
                rendered.append(f"{name}={text!r}")
                continue
            try:
                rendered.append(f"{name}={ast.literal_eval(text)!r}")
            except (ValueError, SyntaxError) as error:
                raise generator_config_error(
                    code=IssueCode.GENERATOR_CREATE_FAILED,
                    class_name=cls.__name__,
                    element_name=key_name,
                    error=type(error).__name__,
                    location=DescriptorLocation(EL_KEY, attribute=name),
                ) from None
        return f"{cls.__name__}({', '.join(rendered)})"

    @staticmethod
    def _parse_sequence_kwarg(generator_str: str) -> str | None:
        """Extract the optional sequence='...' kwarg from a SequenceTableGenerator generator
        string. Bare "SequenceTableGenerator" and empty "SequenceTableGenerator()" return None
        (convention-derived name). Positional args, unknown kwargs, non-string values, and
        malformed syntax all raise ValueError - this generator's args used to be silently
        discarded, which is exactly the failure mode this replaces."""
        if "(" not in generator_str:
            return None
        try:
            module_node = ast.parse(generator_str)
        except SyntaxError as e_syn:
            raise generator_config_error(
                reason="SequenceTableGenerator requires valid syntax; use sequence='...'"
            ) from e_syn
        if not (
            module_node.body
            and isinstance(module_node.body[0], ast.Expr)
            and isinstance(module_node.body[0].value, ast.Call)
            and isinstance(module_node.body[0].value.func, ast.Name)
            and module_node.body[0].value.func.id == "SequenceTableGenerator"
        ):
            raise generator_config_error(reason="SequenceTableGenerator arguments must use only sequence='...'")
        call_node = module_node.body[0].value
        if call_node.args:
            raise generator_config_error(
                reason="SequenceTableGenerator does not accept positional arguments; use sequence='...'"
            )
        parsed_sequence: str | None = None
        for kw in call_node.keywords:
            if kw.arg != "sequence":
                raise generator_config_error(
                    reason="SequenceTableGenerator supports only the 'sequence' keyword argument"
                )
            if not isinstance(kw.value, ast.Constant) or not isinstance(kw.value.value, str):
                raise generator_config_error(reason="SequenceTableGenerator sequence must be a string literal")
            parsed_sequence = kw.value.value
        return parsed_sequence
