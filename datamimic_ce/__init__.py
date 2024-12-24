# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import os

from dotenv import load_dotenv

load_dotenv()
required_env_vars: list[str] = []
missing_vars: list[str] = [var for var in required_env_vars if var not in os.environ]

if missing_vars:
    raise OSError(f"Missing required environment variables: {', '.join(missing_vars)}")
