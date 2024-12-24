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


class MultiprocessingPageInfo:
    """
    Utility class to manage multiprocessing page info.
    """

    def __init__(self, mp_idx: int | None, mp_chunk_size: int | None, page_idx: int, page_size: int):
        """
        Initializes the multiprocessing page info.

        Parameters:
            mp_idx (int): The multiprocessing index.
            mp_chunk_size (int): The multiprocessing chunk size.
            page_idx (int): The page index.
            page_size (int): The page size.
        """
        self._mp_idx = mp_idx
        self._mp_chunk_size = mp_chunk_size
        self._page_idx = page_idx
        self._page_size = page_size

    @property
    def mp_idx(self) -> int | None:
        """
        Get the multiprocessing index.

        Returns:
            int: The multiprocessing index.
        """
        return self._mp_idx

    @property
    def mp_chunk_size(self) -> int | None:
        """
        Get the multiprocessing chunk size.

        Returns:
            int: The multiprocessing chunk size.
        """
        return self._mp_chunk_size

    @property
    def page_idx(self) -> int:
        """
        Get the page index.

        Returns:
            int: The page index.
        """
        return self._page_idx

    @property
    def page_size(self) -> int:
        """
        Get the page size.

        Returns:
            int: The page size.
        """
        return self._page_size
