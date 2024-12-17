# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import random
from pathlib import Path

from datamimic_ce.generators.generator import Generator
from datamimic_ce.logger import logger
from datamimic_ce.utils.file_content_storage import FileContentStorage
from datamimic_ce.utils.file_util import FileUtil


class StreetNameGenerator(Generator):
    """
    Generate random street name
    """

    def __init__(self, dataset: str = "US"):
        self._locale = "en"
        street_code = dataset.upper()[:2]

        # Prepare file path
        prefix_path = Path(__file__).parent
        file_name = f"data/address/street/street_{street_code}.csv"
        file_path = prefix_path.joinpath(file_name)

        # Load file data
        file_content_storage = FileContentStorage()
        try:
            self._values, self._wgt = file_content_storage.load_file_with_custom_func(
                str(file_path), lambda: FileUtil.read_wgt_file(file_path)
            )
        except FileNotFoundError:
            logger.warning(f"No such file or directory: 'street_{street_code}.csv'. Change to street_US datas")
            file_path = prefix_path.joinpath("data/address/street/street_US.csv")
            self._values, self._wgt = file_content_storage.load_file_with_custom_func(
                str(file_path), lambda: FileUtil.read_wgt_file(file_path)
            )

    def generate(self) -> str | None:
        """
        Generate random street name
        Returns:
            Optional[str]: Returns a string if successful, otherwise returns None.
        """
        # return rust.rnd_locale_faker("StreetName", self._locale)
        return random.choices(self._values, self._wgt, k=1)[0]
