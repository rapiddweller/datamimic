from pathlib import Path

from datamimic_ce.interfaces.python.factory import DataMimicTestFactory


class CustomerFactory(DataMimicTestFactory):
    def __init__(self, xml_path: Path | str, entity_name: str):
        super().__init__(xml_path, entity_name)
