# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from abc import ABC

from datamimic_ce.engine.io.contracts import SqlScriptClient


class Client(ABC):  # noqa: B024
    pass


RegisteredClient = Client | SqlScriptClient
