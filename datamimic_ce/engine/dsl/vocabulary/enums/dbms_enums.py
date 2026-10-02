# DATAMIMIC
# Copyright (c) 2023-2026 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce._compat import StrEnum


class Dbms(StrEnum):
    """Relational database system of a <database> connection (``dbms=``).

    Parsed once by the database model, so clients and SQL handling dispatch on the enum
    instead of raw strings, and an unsupported value fails when the model is read.
    """

    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    MSSQL = "mssql"
    ORACLE = "oracle"
