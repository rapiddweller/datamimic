# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.model.include_model import IncludeModel
from datamimic_ce.statements.statement import Statement
from datamimic_ce.utils.file_util import FileUtil


class IncludeStatement(Statement):
    def __init__(self, model: IncludeModel):
        self._uri = model.uri

    @property
    def uri(self):
        return self._uri

    def early_execute(self, descriptor_dir):
        # Case 1: Check if uri is a properties file
        if self._uri.endswith(".properties"):
            # Import properties into context
            return FileUtil.parse_properties(descriptor_dir / self._uri)
        # Case 2: Check if uri is a descriptor file
        else:
            return {}
