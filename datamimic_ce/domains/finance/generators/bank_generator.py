# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import random
from pathlib import Path

from datamimic_ce.domains.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.utils.dataset_path import dataset_path
from datamimic_ce.utils.file_util import FileUtil


class BankGenerator(BaseDomainGenerator):
    def __init__(self, dataset: str | None = None, rng: random.Random | None = None):
        self._dataset = (dataset or "US").upper()  #  bank datasets live in suffixed CSV files
        self._rng: random.Random = rng or random.Random()
        # Track last pick to avoid immediate repetition in single process
        self._last_bank_name: str | None = None

    @property
    def dataset(self) -> str:
        #  expose dataset so downstream models (e.g., Bank) can format data consistently
        return self._dataset

    def generate_bank_data(self) -> dict:
        #  centralized dataset path
        file_path = dataset_path("finance", "bank", f"banks_{self._dataset}.csv", start=Path(__file__))
        header_dict, loaded_data = FileUtil.read_csv_to_dict_of_tuples_with_header(file_path, delimiter=",")

        wgt_idx = header_dict["weight"]
        weights = [float(row[wgt_idx]) for row in loaded_data]
        # Avoid immediate repetition of the same bank
        if self._last_bank_name is not None and len(loaded_data) > 1:
            # Create a filtered pool excluding the last bank
            name_idx = header_dict["name"]
            pool = [
                (row, wt)
                for row, wt in zip(loaded_data, weights, strict=False)
                if row[name_idx] != self._last_bank_name
            ]
            if pool:
                rows, wgts = zip(*pool, strict=False)
                bank_data = self._rng.choices(list(rows), weights=list(wgts), k=1)[0]
            else:
                bank_data = self._rng.choices(loaded_data, weights=weights, k=1)[0]
        else:
            bank_data = self._rng.choices(loaded_data, weights=weights, k=1)[0]
        # Remember to discourage immediate repetition next time
        self._last_bank_name = bank_data[header_dict["name"]]

        return {
            "name": bank_data[header_dict["name"]],
            "swift_code": bank_data[header_dict["swift_code"]],
            "routing_number": bank_data[header_dict["routing_number"]] if "routing_number" in header_dict else "",
        }
