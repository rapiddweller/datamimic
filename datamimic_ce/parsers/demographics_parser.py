"""Parser for <demographics> elements."""

from __future__ import annotations

from pathlib import Path
from xml.etree.ElementTree import Element

from datamimic_ce.constants.element_constants import EL_DEMOGRAPHICS
from datamimic_ce.model.demographics_model import DemographicsModel
from datamimic_ce.parsers.statement_parser import StatementParser
from datamimic_ce.statements.demographics_statement import DemographicsStatement


class DemographicsParser(StatementParser):
    def __init__(self, element: Element, properties: dict | None):
        super().__init__(element, properties, valid_element_tag=EL_DEMOGRAPHICS)

    def parse(self, descriptor_dir: Path) -> DemographicsStatement:
        model = self.validate_attributes(DemographicsModel)
        directory = Path(model.directory)
        if not directory.is_absolute():
            # Resolve relative demographic directories against the descriptor to keep XML portable.
            directory = (descriptor_dir / directory).resolve()
        model.directory = str(directory)
        return DemographicsStatement(model)
