from typing import get_type_hints

import pytest
from pydantic import ValidationError

from datamimic_ce.engine.dsl.model.flow.branches.else_if_model import ElseIfModel
from datamimic_ce.engine.dsl.model.setup.database_model import DatabaseModel
from datamimic_ce.engine.dsl.model.setup.generators.generator_model import GeneratorModel
from datamimic_ce.engine.dsl.model.setup.memstore_model import MemstoreModel
from datamimic_ce.engine.dsl.model.setup.mongodb_model import MongoDBModel
from datamimic_ce.engine.dsl.model.values.structured.item_model import ItemModel
from datamimic_ce.engine.dsl.model.values.structured.list_model import ListModel
from datamimic_ce.engine.dsl.statements.base.composite_statement import CompositeStatement
from datamimic_ce.engine.dsl.statements.flow.branches.else_if_statement import ElseIfStatement
from datamimic_ce.engine.dsl.statements.setup.database_statement import DatabaseStatement
from datamimic_ce.engine.dsl.statements.setup.generator_statement import GeneratorStatement
from datamimic_ce.engine.dsl.statements.setup.memstore_statement import MemstoreStatement
from datamimic_ce.engine.dsl.statements.setup.mongodb_statement import MongoDBStatement
from datamimic_ce.engine.dsl.statements.values.structured.item_statement import ItemStatement
from datamimic_ce.engine.dsl.statements.values.structured.list_statement import ListStatement
from datamimic_ce.engine.dsl.vocabulary.enums.dbms_enums import Dbms


def test_statement_scalar_getters_have_public_return_annotations() -> None:
    getters = [
        ("GeneratorStatement.name", GeneratorStatement.name.fget, str),
        ("GeneratorStatement.generator", GeneratorStatement.generator.fget, str),
        ("DatabaseStatement.db_id", DatabaseStatement.db_id.fget, str),
        ("MongoDBStatement.mongodb_id", MongoDBStatement.mongodb_id.fget, str),
        ("MemstoreStatement.id", MemstoreStatement.id.fget, str),
        ("ElseIfStatement.condition", ElseIfStatement.condition.fget, str),
        ("ListStatement.converter", ListStatement.converter.fget, str | None),
        ("ItemStatement.condition", ItemStatement.condition.fget, str | None),
    ]
    missing = [
        name
        for name, getter, expected in getters
        if getter is None or get_type_hints(getter).get("return") != expected
    ]

    assert not missing, f"{len(missing)} missing return annotations: {missing}"


def test_statement_scalar_getters_preserve_model_values() -> None:
    generator = GeneratorStatement(GeneratorModel(name="ids", generator="IncrementGenerator(start=3)"))
    database = DatabaseStatement(DatabaseModel(id="db", dbms=Dbms.SQLITE))
    mongodb = MongoDBStatement(MongoDBModel(id="mongo", host="localhost", port="27017", database="sample"))
    memstore = MemstoreStatement(MemstoreModel(id="mem"))
    parent = CompositeStatement("parent", None)
    else_if = ElseIfStatement(ElseIfModel(condition="active"), parent)
    list_without_converter = ListStatement(ListModel(name="items"))
    list_with_converter = ListStatement(ListModel(name="items", converter="Trim"))
    list_with_empty_converter = ListStatement(ListModel(name="items", converter=""))
    item_without_condition = ItemStatement(ItemModel())
    item_with_condition = ItemStatement(ItemModel(condition="active"))
    item_with_empty_condition = ItemStatement(ItemModel(condition=""))

    assert (generator.name, generator.generator) == ("ids", "IncrementGenerator(start=3)")
    assert database.db_id == "db"
    assert mongodb.mongodb_id == "mongo"
    assert memstore.id == "mem"
    assert else_if.condition == "active"
    assert list_without_converter.converter is None
    assert list_with_converter.converter == "Trim"
    assert list_with_empty_converter.converter == ""
    assert item_without_condition.condition is None
    assert item_with_condition.condition == "active"
    assert item_with_empty_condition.condition == ""


def test_generator_model_rejects_missing_or_null_name() -> None:
    with pytest.raises(ValidationError) as missing_name:
        GeneratorModel.model_validate({"generator": "IncrementGenerator(start=3)"})
    assert missing_name.value.errors()[0]["loc"] == ("name",)

    with pytest.raises(ValidationError) as null_name:
        GeneratorModel.model_validate({"name": None, "generator": "IncrementGenerator(start=3)"})
    assert null_name.value.errors()[0]["loc"] == ("name",)
