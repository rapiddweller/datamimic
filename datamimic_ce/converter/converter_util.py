# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import importlib
from base64 import b64encode

from datamimic_ce.enums.converter_enums import SupportHash, SupportOutputFormat


class ConverterUtil:
    @staticmethod
    def get_hash_value(hash_type: str, output_format: str, value: str, salt: str | None = None) -> str:
        hash_module_name = hash_type
        try:
            hash_module = importlib.import_module("hashlib").__getattribute__(hash_module_name)
        except AttributeError:
            raise ValueError(
                f"""
                HashConverter can only support hash type of {[h.value for h in SupportHash]} 
                but received {hash_type}
                """
            ) from None

        if salt is not None:
            value += salt

        hash_instance = hash_module(value.encode("UTF-8"))

        if output_format.lower() == SupportOutputFormat.Hex.value:
            return hash_instance.hexdigest()
        elif output_format.lower() == SupportOutputFormat.Base64.value:
            hash_bytes = hash_instance.digest()
            return b64encode(hash_bytes).decode()
        else:
            raise ValueError(
                f"""
                HashConverter can only support output format "['hex','base64']" but recieved {output_format}
                """
            )
