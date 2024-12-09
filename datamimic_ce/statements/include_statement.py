# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/

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
