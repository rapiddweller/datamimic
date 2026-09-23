# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import hmac
from base64 import b64encode
from typing import Any

from datamimic_ce.domains.converters.converter import Converter
from datamimic_ce.engine.dsl.api import SupportHash, SupportOutputFormat


class HashConverter(Converter):
    """Pseudonymize a string into a keyed hash (HMAC): the same value gives the same token within a run,
    and nobody without the key can recompute it. The run supplies the key: <setup rngSeed> is the key,
    so tokens replay across runs; without a seed every run gets a new random key. ``salt`` is optional
    extra key material."""

    def __init__(self, hash_type: str, output_format: str, salt: str | None = None, *, key: bytes):
        support_hashes = set(support_hash.value for support_hash in SupportHash)
        support_output_format = set(support_output.value for support_output in SupportOutputFormat)
        if hash_type.lower() not in support_hashes:
            raise TypeError(f"HashConverter can only support hash type of {support_hashes} but received {hash_type}")
        if output_format.lower() not in support_output_format:
            raise TypeError(
                f"HashConverter can only support output format of {support_output_format} but received {output_format}"
            )
        self._hash_type = hash_type.lower()
        self._output_format = SupportOutputFormat(output_format.lower())
        self._key = key if salt is None else key + salt.encode("utf-8")

    def convert(self, value: Any) -> str:
        if not isinstance(value, str):
            raise ValueError(
                f"HashConverter expects data type 'string', but got value {value} "
                f"with an invalid datatype {type(value)}"
            )
        digest = hmac.new(self._key, value.encode("utf-8"), self._hash_type).digest()
        if self._output_format is SupportOutputFormat.Hex:
            return digest.hex()
        return b64encode(digest).decode()
