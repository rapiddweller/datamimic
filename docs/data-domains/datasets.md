Domain Dataset Loading Standard

Scope
- Applies to all generators/services under `datamimic_ce/domains/*` that load CSV/JSON from `datamimic_ce/domains/domain_data`.

Non‑negotiable rules
- File naming: every localized file uses suffix `_CC.csv` (`CC` = ISO 3166‑1 alpha‑2, upper-case). No unsuffixed fallbacks in code.
- Fallback: when a dataset-suffixed file is missing and strict mode is OFF, fall back to `_US` once per dataset code with a single warning log. When strict mode is ON, raise a `FileNotFoundError`.
- Strict mode: controlled by env `DATAMIMIC_STRICT_DATASET`. Any truthy value other than `0/false/False` enables strict mode.
- Paths: construct all dataset paths via `dataset_path(...)` from `datamimic_ce.utils.dataset_path`. Do not reimplement `Path(__file__).parents[...]`.
- Weights: for wgt-like CSVs without headers, last column is treated as the weight (non-numeric weights default to `1.0`). For headered CSVs, the weight column must be named `weight`.
- Determinism: pass an injected `random.Random` where practical; do not use module-level RNGs in shared code. There is no global seed environment variable; reproducibility is achieved by passing a seeded `random.Random` into generators (and services that accept `rng`).

Unified helpers (use these)
- `dataset_path(*relative, start=Path(__file__))` – builds the path under `domain_data`, with env overrides and fallback behavior.
- `load_weighted_values_try_dataset(*relative, dataset, start)` – loads `value, weight` pairs from suffixed files using `dataset_path`. Honors strict mode and fallback.
- `pick_one_weighted(rng, values, weights)` and `sample_weighted_no_replacement(rng, values, weights, k)` – consistent weighted selection.
- `compute_supported_datasets(patterns, start)` – returns intersection of dataset codes for which ALL pattern files exist. Patterns are relative to `domain_data` and must contain `{CC}`, e.g. `"public_sector/administration/office_types_{CC}.csv"`.

Per‑category and type‑specialized files
- When datasets are specialized by a logical key (category/type), encode that key in the filename, not in directories. Examples:
  - E‑commerce nouns: `ecommerce/product_nouns_{category}_{CC}.csv` (e.g., `product_nouns_electronics_US.csv`)
  - Hospital departments/services by type: `healthcare/hospital/departments_{slug}_{CC}.csv` with a `departments_general_{CC}.csv` fallback
- Callers must pass the base filename with the key but without dataset code to the loader, e.g. `load_weighted_values_try_dataset("ecommerce", f"product_nouns_{category}.csv", dataset=..., start=...)`.

Headered vs headerless CSVs
- Headerless, 2+ columns: the last column is the weight; the preceding columns form the joined value.
- Headered CSVs: include a `weight` column; the value is typically the first column or an explicitly named field when using dict readers.

Cross‑domain reuse (SPOT)
- Reuse shared datasets across domains when appropriate rather than duplicating files. Examples:
  - Finance symbol lookup uses `ecommerce/currencies_{CC}.csv`.
  - Location generation uses `common/city/city_{CC}.csv`.

Generator conventions
- Normalize dataset once: `self._dataset = (dataset or "US").upper()` in `__init__` and use that consistently.
- Do not hardcode example lists in code. If a list is required (e.g., maintenance results), add a dataset CSV in the appropriate folder.
- Type-specialization files: when a generator supports specialized variants (e.g., `departments_{type}_{CC}.csv`), catch `FileNotFoundError` and fall back to a `*_general_{CC}.csv` dataset.
- Keep orchestration (counts, branching) minimal and explicit; keep business data exclusively in CSV/JSON files.

Error handling and logging
- Public APIs/services must not leak raw exceptions; map them to user-friendly messages. Internals can raise explicit exceptions (`FileNotFoundError`, `ValueError`).
- Fallback warnings must log once per dataset code. The centralized logger in `dataset_path` already ensures this.

Supported datasets discovery (recommendation)
- When a service needs to declare supported datasets, compute the intersection of required dataset file sets using `datamimic_ce.utils.supported_datasets.compute_supported_datasets(...)` instead of ad-hoc scans.

Examples
- Country list: `dataset_path("common", f"country_{self._dataset}.csv", start=Path(__file__))`
- Webmail domains: `dataset_path("common", "net", f"webmailDomain_{self._dataset}.csv", start=Path(__file__))`
- Hospital services by type: `load_weighted_values_try_dataset("healthcare", "hospital", f"services_{slug}.csv", dataset=self._dataset, start=Path(__file__))`
- Supported datasets (administration):
  ```python
  from datamimic_ce.domains.utils.supported_datasets import compute_supported_datasets
  codes = compute_supported_datasets([
      "public_sector/administration/office_types_{CC}.csv",
      "public_sector/administration/jurisdictions_{CC}.csv",
  ], start=Path(__file__))
  ```

Rationale (SOC/DRY/KISS)
- SOC: business rules stay in datasets; generators orchestrate selection only.
- DRY: path resolution, weighted selection, and fallback live in one place.
- KISS: uniform filename patterns and a single loader minimize branching and edge cases.
