# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
import random
from pathlib import Path

from datamimic_ce.domains.domain_core.base_domain_generator import DatasetAwareDomainGenerator
from datamimic_ce.domains.utils.dataset_loader import pick_one_weighted_no_repeat
from datamimic_ce.domains.utils.dataset_path import dataset_path
from datamimic_ce.utils.file_util import FileUtil


class BankGenerator(DatasetAwareDomainGenerator):
    def __init__(
        self,
        dataset: str | None = None,
        rng: random.Random | None = None,
    ):
        super().__init__(dataset=dataset, rng=rng)
        # Track last pick to avoid immediate repetition in single process
        self._last_bank_name: str | None = None

    def generate_bank_data(self) -> dict:
        #  centralized dataset path
        file_path = dataset_path("finance", "bank", f"banks_{self._dataset}.csv", start=Path(__file__))
        header_dict, loaded_data = FileUtil.read_csv_to_dict_of_tuples_with_header(file_path, delimiter=",")

        name_idx = header_dict["name"]
        wgt_idx = header_dict["weight"]
        names = [row[name_idx] for row in loaded_data]
        weights = [float(row[wgt_idx]) for row in loaded_data]
        # pick_one_weighted_no_repeat guarantees non-repetition when ≥2 distinct values
        chosen_name = pick_one_weighted_no_repeat(self._rng, names, weights, last=self._last_bank_name)
        bank_data = loaded_data[names.index(chosen_name)]
        self._last_bank_name = chosen_name

        return {
            "name": bank_data[header_dict["name"]],
            "swift_code": bank_data[header_dict["swift_code"]],
            "routing_number": bank_data[header_dict["routing_number"]] if "routing_number" in header_dict else "",
        }
