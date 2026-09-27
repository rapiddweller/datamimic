"""Bind built-in parsers after loading the model-owned DSL grammar."""

from datamimic_ce.engine.dsl.parsers.flow.branches.condition_parser import ConditionParser
from datamimic_ce.engine.dsl.parsers.flow.branches.else_if_parser import ElseIfParser
from datamimic_ce.engine.dsl.parsers.flow.branches.else_parser import ElseParser
from datamimic_ce.engine.dsl.parsers.flow.branches.if_parser import IfParser
from datamimic_ce.engine.dsl.parsers.flow.commands.assert_parser import AssertParser
from datamimic_ce.engine.dsl.parsers.flow.commands.echo_parser import EchoParser
from datamimic_ce.engine.dsl.parsers.flow.commands.execute_parser import ExecuteParser
from datamimic_ce.engine.dsl.parsers.flow.loops.while_parser import WhileParser
from datamimic_ce.engine.dsl.parsers.generation.generate_parser import GenerateParser
from datamimic_ce.engine.dsl.parsers.parser_util import _BUILTIN_PARSERS
from datamimic_ce.engine.dsl.parsers.setup.database_parser import DatabaseParser
from datamimic_ce.engine.dsl.parsers.setup.demographics_parser import DemographicsParser
from datamimic_ce.engine.dsl.parsers.setup.generator_parser import GeneratorParser
from datamimic_ce.engine.dsl.parsers.setup.include_parser import IncludeParser
from datamimic_ce.engine.dsl.parsers.setup.memstore_parser import MemstoreParser
from datamimic_ce.engine.dsl.parsers.setup.mongodb_parser import MongoDBParser
from datamimic_ce.engine.dsl.parsers.setup.state_machine_parser import StateMachineParser
from datamimic_ce.engine.dsl.parsers.values.references.reference_parser import ReferenceParser
from datamimic_ce.engine.dsl.parsers.values.scalar.element_parser import ElementParser
from datamimic_ce.engine.dsl.parsers.values.scalar.key_parser import KeyParser
from datamimic_ce.engine.dsl.parsers.values.structured.array_parser import ArrayParser
from datamimic_ce.engine.dsl.parsers.values.structured.item_parser import ItemParser
from datamimic_ce.engine.dsl.parsers.values.structured.list_parser import ListParser
from datamimic_ce.engine.dsl.parsers.values.structured.nested_key_parser import NestedKeyParser
from datamimic_ce.engine.dsl.parsers.values.variables.variable_parser import VariableParser
from datamimic_ce.engine.dsl.vocabulary.constants import element_constants as tags

_BUILTIN_PARSERS.update(
    {
        tags.EL_GENERATE: GenerateParser,
        tags.EL_KEY: KeyParser,
        tags.EL_VARIABLE: VariableParser,
        tags.EL_NESTED_KEY: NestedKeyParser,
        tags.EL_ARRAY: ArrayParser,
        tags.EL_LIST: ListParser,
        tags.EL_ITEM: ItemParser,
        tags.EL_REFERENCE: ReferenceParser,
        tags.EL_INCLUDE: IncludeParser,
        tags.EL_MEMSTORE: MemstoreParser,
        tags.EL_EXECUTE: ExecuteParser,
        tags.EL_DATABASE: DatabaseParser,
        tags.EL_MONGODB: MongoDBParser,
        tags.EL_IF: IfParser,
        tags.EL_ELSE_IF: ElseIfParser,
        tags.EL_ELSE: ElseParser,
        tags.EL_CONDITION: ConditionParser,
        tags.EL_ECHO: EchoParser,
        tags.EL_ELEMENT: ElementParser,
        tags.EL_GENERATOR: GeneratorParser,
        tags.EL_DEMOGRAPHICS: DemographicsParser,
        tags.EL_STATE_MACHINE: StateMachineParser,
        tags.EL_WHILE: WhileParser,
        tags.EL_ASSERT: AssertParser,
    }
)
