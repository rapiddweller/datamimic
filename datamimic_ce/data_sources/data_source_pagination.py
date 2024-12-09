# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/


class DataSourcePagination:
    """
    Store pagination info for creating data source in multiple processing
    """

    def __init__(self, skip: int, limit: int):
        self._skip = skip
        self._limit = limit

    @property
    def skip(self) -> int:
        return self._skip

    @property
    def limit(self) -> int:
        return self._limit
