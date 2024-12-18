#  Copyright (c) 2023 Rapiddweller Asia Co., Ltd.
#  All rights reserved.
#  #
#  This software and related documentation are provided under a license
#  agreement containing restrictions on use and disclosure and are
#  protected by intellectual property laws. Except as expressly permitted
#  in your license agreement or allowed by law, you may not use, copy,
#  reproduce, translate, broadcast, modify, license, transmit, distribute,
#  exhibit, perform, publish, or display any part, in any form, or by any means.
#  #
#  This software is the confidential and proprietary information of
#  Rapiddweller Asia Co., Ltd. ("Confidential Information"). You shall not
#  disclose such Confidential Information and shall use it only in accordance
#  with the terms of the license agreement you entered into with Rapiddweller Asia Co., Ltd.
#


class InMemoryCache:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._dict_cache = {}
        return cls._instance

    def get(self, key):
        """
        Get value from cache
        :param key:
        :return:
        """
        return self._dict_cache.get(key)

    def set(self, key, value):
        """
        Set value to cache
        :param key:
        :param value:
        :return:
        """
        self._dict_cache[key] = value
