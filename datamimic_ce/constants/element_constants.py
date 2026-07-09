# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

EL_SETUP = "setup"
EL_MONGODB = "mongodb"
EL_GENERATE = "generate"
EL_ITERATE = "iterate"  # human-readable alias of <generate> (source-driven intent), same parser/model/statement
EL_DATABASE = "database"
EL_KEY = "key"
EL_ID = "id"  # human-readable alias of <key> (marks an identifier field), same parser/model/statement
EL_VARIABLE = "variable"
EL_NESTED_KEY = "nestedKey"
EL_ARRAY = "array"
EL_VALUE = "value"  # <array type="literal"> child: <value constant="..."/>
EL_INCLUDE = "include"
EL_MEMSTORE = "memstore"
EL_EXECUTE = "execute"
EL_REFERENCE = "reference"
EL_LIST = "list"
EL_ITEM = "item"
EL_IF = "if"
EL_ECHO = "echo"
EL_ELEMENT = "element"
EL_GENERATOR = "generator"
EL_CONDITION = "condition"
EL_ELSE_IF = "else-if"
EL_ELSE = "else"
EL_DEMOGRAPHICS = "demographics"
EL_COMMENT = "comment"  # documentation-only element (legacy DSL compatibility), ignored (no-op) wherever it appears
EL_STATE_MACHINE = "state-machine"  # named, reusable weighted state machine (builds StateTransitionGenerator)
EL_TRANSITION = "transition"  # one weighted edge of a <state-machine>
EL_FIELD = "field"  # one source-column -> target-field mapping of a composite <reference>
EL_WHILE = "while"  # repeat child statements while a condition holds (per-row loop)
EL_ASSERT = "assert"  # fail the run when a condition does not hold (per record in <generate>, once under <setup>)
