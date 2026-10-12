"""Parser for <demographics> elements."""

from __future__ import annotations

from pathlib import Path

from datamimic_ce.engine.dsl.model.setup.demographics_model import DemographicsModel
from datamimic_ce.engine.dsl.parsers.base.statement_parser import StatementParser
from datamimic_ce.engine.dsl.parsers.input.xml import XmlElement
from datamimic_ce.engine.dsl.statements.setup.demographics_statement import DemographicsStatement
from datamimic_ce.engine.dsl.vocabulary.constants.element_constants import EL_DEMOGRAPHICS


class DemographicsParser(StatementParser):
    def __init__(self, element: XmlElement, properties: dict | None):
        super().__init__(element, properties, valid_element_tag=EL_DEMOGRAPHICS)

    def parse(self, descriptor_dir: Path) -> DemographicsStatement:
        model = self.validate_attributes(DemographicsModel)
        directory = Path(model.directory)
        if not directory.is_absolute():
            # Resolve relative demographic directories against the descriptor to keep XML portable.
            directory = (descriptor_dir / directory).resolve()
        model.directory = str(directory)
        return DemographicsStatement(model)
