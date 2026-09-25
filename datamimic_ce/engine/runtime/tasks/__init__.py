"""Runtime task implementations and statement dispatch registrations."""

from datamimic_ce.engine.dsl.api import (
    ArrayStatement,
    AssertStatement,
    ConditionStatement,
    DatabaseStatement,
    DemographicsStatement,
    EchoStatement,
    ElementStatement,
    ElseIfStatement,
    ElseStatement,
    ExecuteStatement,
    GenerateStatement,
    GeneratorStatement,
    IfStatement,
    IncludeStatement,
    ItemStatement,
    KeyStatement,
    ListStatement,
    MemstoreStatement,
    MongoDBStatement,
    NestedKeyStatement,
    ReferenceStatement,
    StateMachineStatement,
    Statement,
    VariableStatement,
    WhileStatement,
)
from datamimic_ce.engine.io.api import DataSourcePagination
from datamimic_ce.engine.runtime.contexts.setup_context import SetupContext
from datamimic_ce.engine.runtime.tasks.array_task import ArrayTask
from datamimic_ce.engine.runtime.tasks.assert_task import AssertTask
from datamimic_ce.engine.runtime.tasks.condition_task import ConditionTask
from datamimic_ce.engine.runtime.tasks.database_task import DatabaseTask
from datamimic_ce.engine.runtime.tasks.demographics_task import DemographicsTask
from datamimic_ce.engine.runtime.tasks.echo_task import EchoTask
from datamimic_ce.engine.runtime.tasks.element_task import ElementTask
from datamimic_ce.engine.runtime.tasks.else_if_task import ElseIfTask
from datamimic_ce.engine.runtime.tasks.else_task import ElseTask
from datamimic_ce.engine.runtime.tasks.execute_task import ExecuteTask
from datamimic_ce.engine.runtime.tasks.generate.task import GenerateTask
from datamimic_ce.engine.runtime.tasks.generator_task import GeneratorTask
from datamimic_ce.engine.runtime.tasks.if_task import IfTask
from datamimic_ce.engine.runtime.tasks.include_task import IncludeTask
from datamimic_ce.engine.runtime.tasks.item_task import ItemTask
from datamimic_ce.engine.runtime.tasks.key_task import KeyTask
from datamimic_ce.engine.runtime.tasks.list_task import ListTask
from datamimic_ce.engine.runtime.tasks.memstore_task import MemstoreTask
from datamimic_ce.engine.runtime.tasks.mongodb_task import MongoDBTask
from datamimic_ce.engine.runtime.tasks.nested_key_task import NestedKeyTask
from datamimic_ce.engine.runtime.tasks.reference_task import ReferenceTask
from datamimic_ce.engine.runtime.tasks.state_machine_task import StateMachineTask
from datamimic_ce.engine.runtime.tasks.task import Task
from datamimic_ce.engine.runtime.tasks.task_factory import create_task
from datamimic_ce.engine.runtime.tasks.variable_task import VariableTask
from datamimic_ce.engine.runtime.tasks.while_task import WhileTask


@create_task.register
def _(statement: GenerateStatement, context: SetupContext, pagination: DataSourcePagination | None = None) -> Task:
    return GenerateTask(statement)


@create_task.register
def _(statement: MongoDBStatement, context: SetupContext, pagination: DataSourcePagination | None = None) -> Task:
    return MongoDBTask(statement)


@create_task.register
def _(statement: DatabaseStatement, context: SetupContext, pagination: DataSourcePagination | None = None) -> Task:
    return DatabaseTask(statement)


@create_task.register
def _(statement: IncludeStatement, context: SetupContext, pagination: DataSourcePagination | None = None) -> Task:
    return IncludeTask(statement)


@create_task.register
def _(statement: MemstoreStatement, context: SetupContext, pagination: DataSourcePagination | None = None) -> Task:
    return MemstoreTask(statement)


@create_task.register
def _(statement: ExecuteStatement, context: SetupContext, pagination: DataSourcePagination | None = None) -> Task:
    return ExecuteTask(statement)


@create_task.register
def _(statement: KeyStatement, context: SetupContext, pagination: DataSourcePagination | None = None) -> Task:
    return KeyTask(context, statement, pagination)


@create_task.register
def _(statement: VariableStatement, context: SetupContext, pagination: DataSourcePagination | None = None) -> Task:
    return VariableTask(context, statement, pagination)


@create_task.register
def _(statement: NestedKeyStatement, context: SetupContext, pagination: DataSourcePagination | None = None) -> Task:
    return NestedKeyTask(context, statement)


@create_task.register
def _(statement: ArrayStatement, context: SetupContext, pagination: DataSourcePagination | None = None) -> Task:
    return ArrayTask(statement)


@create_task.register
def _(statement: ReferenceStatement, context: SetupContext, pagination: DataSourcePagination | None = None) -> Task:
    return ReferenceTask(statement, pagination)


@create_task.register
def _(statement: ListStatement, context: SetupContext, pagination: DataSourcePagination | None = None) -> Task:
    return ListTask(ctx=context, statement=statement)


@create_task.register
def _(statement: ItemStatement, context: SetupContext, pagination: DataSourcePagination | None = None) -> Task:
    return ItemTask(context, statement)


@create_task.register
def _(statement: IfStatement, context: SetupContext, pagination: DataSourcePagination | None = None) -> Task:
    return IfTask(statement)


@create_task.register
def _(statement: ConditionStatement, context: SetupContext, pagination: DataSourcePagination | None = None) -> Task:
    return ConditionTask(statement)


@create_task.register
def _(statement: WhileStatement, context: SetupContext, pagination: DataSourcePagination | None = None) -> Task:
    return WhileTask(statement)


@create_task.register
def _(
    statement: DemographicsStatement, context: SetupContext, pagination: DataSourcePagination | None = None
) -> Task:
    return DemographicsTask(statement)


@create_task.register
def _(statement: ElseIfStatement, context: SetupContext, pagination: DataSourcePagination | None = None) -> Task:
    return ElseIfTask(statement)


@create_task.register
def _(statement: ElseStatement, context: SetupContext, pagination: DataSourcePagination | None = None) -> Task:
    return ElseTask(statement)


@create_task.register
def _(statement: EchoStatement, context: SetupContext, pagination: DataSourcePagination | None = None) -> Task:
    return EchoTask(statement)


@create_task.register
def _(statement: AssertStatement, context: SetupContext, pagination: DataSourcePagination | None = None) -> Task:
    return AssertTask(statement)


@create_task.register
def _(statement: ElementStatement, context: SetupContext, pagination: DataSourcePagination | None = None) -> Task:
    return ElementTask(context, statement)


@create_task.register
def _(statement: GeneratorStatement, context: SetupContext, pagination: DataSourcePagination | None = None) -> Task:
    return GeneratorTask(statement)


@create_task.register
def _(
    statement: StateMachineStatement, context: SetupContext, pagination: DataSourcePagination | None = None
) -> Task:
    return StateMachineTask(statement)


@create_task.register
def _(statement: Statement, context: SetupContext, pagination: DataSourcePagination | None = None) -> Task:
    raise ValueError(f"Cannot create a task for statement {statement.__class__.__name__}")
