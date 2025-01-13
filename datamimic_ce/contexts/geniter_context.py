# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce.contexts.context import Context
from datamimic_ce.contexts.setup_context import SetupContext
from datamimic_ce.utils.dict_util import dict_nested_update


class GenIterContext(Context):
    """
    Context of GenerateTask, mainly used for saving current product and variable as hierarchical structure.
    Must be sub-context of SetupContext or another GenerateContext.
    """

    def __init__(self, parent: Context, current_name: str):
        super().__init__(parent.root)
        self._parent = parent
        self._current_name = current_name
        self._current_product: dict = {}
        self._current_variables: dict = {}
        # self._namespace: dict = {}
        self._worker_id = None

    @property
    def current_name(self) -> str:
        return self._current_name

    @property
    def current_product(self) -> dict:
        return self._current_product

    @current_product.setter
    def current_product(self, value: dict) -> None:
        self._current_product = value

    @property
    def current_variables(self) -> dict:
        return self._current_variables

    @property
    def parent(self) -> Context:
        return self._parent

    @property
    def worker_id(self) -> int:
        if self._worker_id is not None:
            return self._worker_id

        if isinstance(self._parent, GenIterContext):
            return self._parent.worker_id

        raise ValueError("Worker ID not found in context hierarchy.")

    @worker_id.setter
    def worker_id(self, value: int) -> None:
        self._worker_id = value

    def add_current_product_field(self, key_path, value):
        """
        Add field to current product using string key path (i.e. "data.people.name")
        :param key_path:
        :param value:
        :return:
        """
        dict_nested_update(self.current_product, key_path, value)
