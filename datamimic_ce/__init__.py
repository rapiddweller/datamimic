# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# Licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License (CC BY-NC-SA 4.0).
# For commercial use, please contact Rapiddweller at info@rapiddweller.com to obtain a commercial license.
# Full license text available at: http://creativecommons.org/licenses/by-nc-sa/4.0/

import os

from dotenv import load_dotenv

load_dotenv()
required_env_vars = []
missing_vars = [var for var in required_env_vars if var not in os.environ]

if missing_vars:
    raise OSError(f"Missing required environment variables: {', '.join(missing_vars)}")
