# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from enum import Enum


class ConverterEnum(Enum):
    UpperCase = "UpperCase"
    LowerCase = "LowerCase"
    DateFormat = "DateFormat"
    Mask = "Mask"
    MiddleMask = "MiddleMask"
    CutLength = "CutLength"
    Append = "Append"
    Hash = "Hash"
    Timestamp2Date = "Timestamp2Date"
    JavaHash = "JavaHash"
    Date2Timestamp = "Date2Timestamp"
    RemoveNoneOrEmptyElement = "RemoveNoneOrEmptyElement"


class SupportHash(Enum):
    SHA256Hash = "sha256"
    SHA512Hash = "sha512"
    SHA3_512Hash = "sha3_512"
    SHA1Hash = "sha1"
    MD5Hash = "md5"


class SupportOutputFormat(Enum):
    Hex = "hex"
    Base64 = "base64"
