# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

from datamimic_ce._compat import StrEnum


class ExportOperation(StrEnum):
    """Client write operation selected by a target suffix (``clientId.<operation>``).

    A plain ``clientId`` target inserts. Parsed once at the target boundary
    (ExporterUtil.create_exporter_list) so everything downstream dispatches on the
    enum instead of raw strings.
    """

    UPDATE = "update"
    UPSERT = "upsert"
    DELETE = "delete"
