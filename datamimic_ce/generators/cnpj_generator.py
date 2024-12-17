# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.generators.data_faker_generator import DataFakerGenerator
from datamimic_ce.generators.generator import Generator


class CNPJGenerator(Generator):
    """
    Generates Brazilian CNPJ numbers.
    """

    def __init__(self):
        self._gen = DataFakerGenerator(method="cnpj", locale="pt_BR")

    def generate(self) -> str:
        return self._gen.generate()
