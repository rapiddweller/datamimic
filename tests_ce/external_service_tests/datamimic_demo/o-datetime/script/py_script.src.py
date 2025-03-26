# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from datetime import datetime, timedelta


def add_days(current_date: datetime, days: int):
    return current_date + timedelta(days=days)
