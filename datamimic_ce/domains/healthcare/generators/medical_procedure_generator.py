# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Medical Procedure generator utilities.

Dataset-driven generator for medical procedures: names, descriptions,
categories, specialties. All strings and choices are sourced from
datamimic_ce/domains/domain_data/healthcare/medical/*_{CC}.csv files.
"""

from __future__ import annotations

import random
from pathlib import Path

from datamimic_ce.domains.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.utils.dataset_path import dataset_path
from datamimic_ce.utils.file_util import FileUtil


class MedicalProcedureGenerator(BaseDomainGenerator):
    def __init__(self, dataset: str | None = None, rng: random.Random | None = None):
        #  normalize once so we consistently resolve _{CC}.csv files
        self._dataset = (dataset or "US").upper()
        self._rng: random.Random = rng or random.Random()
        self._last_specialty: str | None = None
        self._last_recovery_time: int | None = None

    def get_procedure_name(self, category: str, specialty: str, is_surgical: bool, is_diagnostic: bool) -> str:
        """Generate a procedure name using dataset patterns and components."""
        patterns, pw = FileUtil.read_wgt_file(
            dataset_path("healthcare", "medical", f"procedure_name_patterns_{self._dataset}.csv", start=Path(__file__))
        )

        if is_surgical:
            action_file = f"procedure_actions_surgical_{self._dataset}.csv"
        elif is_diagnostic:
            action_file = f"procedure_actions_diagnostic_{self._dataset}.csv"
        else:
            action_file = f"procedure_actions_general_{self._dataset}.csv"

        actions, aw = FileUtil.read_wgt_file(dataset_path("healthcare", "medical", action_file, start=Path(__file__)))
        locations, lw = FileUtil.read_wgt_file(
            dataset_path("healthcare", "medical", f"procedure_locations_{self._dataset}.csv", start=Path(__file__))
        )
        structures, sw = FileUtil.read_wgt_file(
            dataset_path("healthcare", "medical", f"procedure_structures_{self._dataset}.csv", start=Path(__file__))
        )

        pattern = self._rng.choices(patterns, weights=pw, k=1)[0]
        action = self._rng.choices(actions, weights=aw, k=1)[0]
        location = self._rng.choices(locations, weights=lw, k=1)[0]
        structure = self._rng.choices(structures, weights=sw, k=1)[0]
        return pattern.format(action=action, location=location, structure=structure)

    def generate_procedure_description(
        self,
        name: str,
        category: str,
        is_surgical: bool,
        is_diagnostic: bool,
        is_preventive: bool,
        requires_anesthesia: bool,
    ) -> str:
        """Generate a dataset-driven procedure description."""
        from datamimic_ce.domains.utils.dataset_loader import load_weighted_values_try_dataset

        if is_surgical:
            t_file = "procedure_description_templates_surgical.csv"
            a_file = "procedure_actions_surgical.csv"
            p_file = "procedure_purposes_surgical.csv"
        elif is_diagnostic:
            t_file = "procedure_description_templates_diagnostic.csv"
            a_file = "procedure_actions_diagnostic.csv"
            p_file = "procedure_purposes_diagnostic.csv"
        elif is_preventive:
            t_file = "procedure_description_templates_preventive.csv"
            a_file = "procedure_actions_preventive.csv"
            p_file = "procedure_purposes_preventive.csv"
        else:
            t_file = "procedure_description_templates_general.csv"
            a_file = "procedure_actions_general.csv"
            p_file = "procedure_purposes_general.csv"

        templates, tw = load_weighted_values_try_dataset(
            "healthcare", "medical", t_file, dataset=self._dataset, start=Path(__file__)
        )
        actions, aw = load_weighted_values_try_dataset(
            "healthcare", "medical", a_file, dataset=self._dataset, start=Path(__file__)
        )
        purposes, pw = load_weighted_values_try_dataset(
            "healthcare", "medical", p_file, dataset=self._dataset, start=Path(__file__)
        )

        words = name.split()
        structure = words[-1] if len(words) > 0 else "structure"

        template = self._rng.choices(templates, weights=tw, k=1)[0]
        action = self._rng.choices(actions, weights=aw, k=1)[0]
        purpose = self._rng.choices(purposes, weights=pw, k=1)[0]

        description = template.format(
            action=action,
            structure=structure,
            category=category.lower(),
            purpose=purpose,
        )

        if requires_anesthesia:
            from datamimic_ce.domains.utils.dataset_loader import load_weighted_values_try_dataset

            a_vals, a_w = load_weighted_values_try_dataset(
                "healthcare", "medical", "procedure_anesthesia_notes.csv", dataset=self._dataset, start=Path(__file__)
            )
            description += self._rng.choices(a_vals, weights=a_w, k=1)[0]

        return description

    def generate_specialty(self) -> str:
        """Generate a medical specialty (dataset-driven)."""
        file_path = dataset_path("healthcare", "medical", f"specialties_{self._dataset}.csv", start=Path(__file__))
        wgt, loaded_data = FileUtil.read_csv_having_weight_column(file_path, "weight")
        # avoid immediate repetition when possible
        if self._last_specialty is not None and len(loaded_data) > 1:
            pool = [
                (row["specialty"], float(w))
                for row, w in zip(loaded_data, wgt, strict=False)
                if row["specialty"] != self._last_specialty
            ]
            values, weights = zip(*pool, strict=False)
            choice = self._rng.choices(list(values), weights=list(weights), k=1)[0]
        else:
            choice = self._rng.choices(loaded_data, weights=wgt, k=1)[0]["specialty"]
        self._last_specialty = choice
        return choice

    def generate_category(self) -> str:
        values, w = FileUtil.read_wgt_file(
            dataset_path("healthcare", "medical", f"procedure_categories_{self._dataset}.csv", start=Path(__file__))
        )
        return self._rng.choices(values, weights=w, k=1)[0]

    # Helper to pick recovery time with anti-repetition
    def pick_recovery_time(self, is_surgical: bool) -> int:
        if is_surgical:
            low, high = 1, 30
        else:
            low, high = 0, 3
        val = self._rng.randint(low, high)
        if self._last_recovery_time is not None and (high - low) >= 1 and val == self._last_recovery_time:
            # pick a different value within bounds using generator RNG
            candidates = [x for x in range(low, high + 1) if x != self._last_recovery_time]
            val = self._rng.choice(candidates)
        self._last_recovery_time = val
        return val

    @property
    def rng(self) -> random.Random:
        return self._rng
