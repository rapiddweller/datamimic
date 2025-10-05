# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Transaction Generator.

This module provides functionality to generate transaction data for financial accounts.
"""

from __future__ import annotations

import datetime as dt
import random
from pathlib import Path

from datamimic_ce.domains.common.literal_generators.data_faker_generator import DataFakerGenerator
from datamimic_ce.domains.common.literal_generators.string_generator import StringGenerator
from datamimic_ce.domains.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.utils.dataset_path import dataset_path
from datamimic_ce.utils.file_content_storage import FileContentStorage
from datamimic_ce.utils.file_util import FileUtil


class TransactionGenerator(BaseDomainGenerator):
    """Generator for financial transaction data."""

    def __init__(self, dataset: str | None = None, rng: random.Random | None = None):
        """Initialize the transaction generator.

        Args:
            dataset: The dataset code to use (e.g., 'US', 'DE'). Defaults to 'US'.
        """
        self._dataset = (dataset or "US").upper()  #  normalize once for consistent dataset file suffixes
        self._rng: random.Random = rng or random.Random()
        # Keep reference IDs deterministic when rngSeed is supplied via descriptors.
        self._reference_generator = DataFakerGenerator(
            "uuid4",
            rng=self._derive_rng() if rng is not None else None,
        )
        # Cache structures: map key -> (header_dict, rows)
        self._transaction_data: dict[str, tuple[dict[str, int], list[tuple[object, ...]]]] = {}
        self._currency_data: dict[str, tuple[dict[str, int], list[tuple[object, ...]]]] = {}
        self._amount_data: dict[str, tuple[dict[str, int], list[tuple[object, ...]]]] = {}

    @property
    def dataset(self) -> str:
        """Get the current dataset code.

        Returns:
            The dataset code.
        """
        return self._dataset

    @property
    def rng(self) -> random.Random:
        return self._rng

    def _derive_rng(self) -> random.Random:
        # Spawn deterministic child RNGs so seeded transaction batches replay without cross-coupling randomness.
        return random.Random(self._rng.randrange(2**63)) if isinstance(self._rng, random.Random) else random.Random()

    #  Centralize date sampling to keep model pure and determinism consistent
    def generate_transaction_date(self) -> dt.datetime:
        from datamimic_ce.domains.common.literal_generators.datetime_generator import DateTimeGenerator

        now = dt.datetime.now()
        min_dt = (now - dt.timedelta(days=365)).strftime("%Y-%m-%d %H:%M:%S")
        max_dt = now.strftime("%Y-%m-%d %H:%M:%S")
        gen = DateTimeGenerator(min=min_dt, max=max_dt, random=True, rng=self._derive_rng()).generate()
        assert isinstance(gen, dt.datetime)
        return gen

    def _get_base_path(self, subdirectory: str) -> Path:
        """Get base path for domain data files.

        Args:
            subdirectory: The subdirectory to append to the base path.

        Returns:
            The full path to the specified directory.
        """
        #  remove hardcoded repo traversal
        base_path = dataset_path(start=Path(__file__))

        # Handle different directory structures based on subdirectory
        if subdirectory.startswith("../"):
            # Handle relative paths that start with "../"
            parts = subdirectory.split("/")
            return base_path.joinpath(*parts[1:])
        elif "/" in subdirectory:
            # Handle paths with subdirectories like "common/city"
            parts = subdirectory.split("/")
            return base_path.joinpath(*parts)
        else:
            # Standard case for finance/subdirectory
            return base_path / "finance" / subdirectory

    def _load_data_file(
        self, file_name: str, subdirectory: str = "transaction"
    ) -> tuple[dict[str, int], list[tuple[object, ...]]]:
        """Load data from a CSV file.

        Args:
            file_name: Name of the file to load.
            subdirectory: The subdirectory where the file is located.

        Returns:
            Tuple containing the header dictionary and loaded data.
        """
        file_path = self._get_base_path(subdirectory) / file_name

        return FileContentStorage.load_file_with_custom_func(
            cache_key=str(file_path),
            read_func=lambda: FileUtil.read_csv_to_dict_of_tuples_with_header(file_path, delimiter=","),
        )

    def _weighted_choice(
        self, data: list[tuple[object, ...]], header_dict: dict[str, int], weight_key: str = "weight"
    ) -> tuple[object, ...]:
        """Select a random item based on weights.

        Args:
            data: List of data rows.
            header_dict: Dictionary mapping column names to indices.
            weight_key: Key for the weight column.

        Returns:
            The selected data row.
        """
        # Check if weight key exists in the header, otherwise use equal weights
        if weight_key in header_dict:
            wgt_idx = header_dict[weight_key]
            weights = [float(str(row[wgt_idx])) for row in data]
            return self._rng.choices(data, weights=weights)[0]
        else:
            # If no weight key exists, use equal weights
            return self._rng.choice(data)

    def get_transaction_type(self) -> dict:
        """Generate a random transaction type.

        Returns:
            A dictionary containing the transaction type and direction.
        """
        if "transaction_types" not in self._transaction_data:
            header_dict, loaded_data = self._load_data_file(f"transaction_types_{self._dataset}.csv", "transaction")
            self._transaction_data["transaction_types"] = (header_dict, loaded_data)

        header_dict, loaded_data = self._transaction_data["transaction_types"]
        type_data = self._weighted_choice(loaded_data, header_dict)

        transaction_type = str(type_data[header_dict["transaction_type"]])
        direction = str(type_data[header_dict["direction"]]).strip()

        return {"type": transaction_type, "direction": direction}

    def get_merchant_category(self) -> str:
        """Generate a random merchant category.

        Returns:
            A random merchant category.
        """
        if "categories" not in self._transaction_data:
            header_dict, loaded_data = self._load_data_file(f"categories_{self._dataset}.csv", "transaction")
            self._transaction_data["categories"] = (header_dict, loaded_data)

        header_dict, loaded_data = self._transaction_data["categories"]
        category_data = self._weighted_choice(loaded_data, header_dict)
        return str(category_data[header_dict["category"]])

    def get_merchant_name(self, category: str | None = None) -> str:
        """Generate a random merchant name.

        Args:
            category: Optional category to select merchant from.

        Returns:
            A random merchant name.
        """
        if category is None:
            category = self.get_merchant_category()

        # Prevent infinite recursion with a fallback
        recursion_guard = getattr(self, "_merchant_recursion_count", 0)
        if recursion_guard > 3:
            # If we've recursed too many times, return a generic merchant name
            return f"{category} Shop"

        # Set recursion guard
        self._merchant_recursion_count = recursion_guard + 1

        try:
            if "merchants" not in self._transaction_data:
                header_dict, loaded_data = self._load_data_file(f"merchants_{self._dataset}.csv", "transaction")
                self._transaction_data["merchants"] = (header_dict, loaded_data)

            header_dict, loaded_data = self._transaction_data["merchants"]

            # Filter merchants by category
            filtered_data = [row for row in loaded_data if row[header_dict["category"]] == category]

            if filtered_data:
                merchant_data = self._weighted_choice(filtered_data, header_dict)
                self._merchant_recursion_count = 0  # Reset recursion counter
                return str(merchant_data[header_dict["merchant_name"]])
            else:
                # If no merchants found for the category, try with a new random category
                # But don't recurse infinitely if no merchants exist at all
                if recursion_guard < 3:
                    new_category = self.get_merchant_category()
                    # Avoid recursion with the same category
                    if new_category != category:
                        return self.get_merchant_name(new_category)

                # Fallback if recursion limit reached or same category
                self._merchant_recursion_count = 0  # Reset recursion counter
                return f"{category} Merchant"
        except (FileNotFoundError, KeyError, IndexError, ValueError):
            # Narrow exception scope; do not mask unrelated errors
            self._merchant_recursion_count = 0
            return f"{category} Merchant"

    def get_status(self) -> str:
        """Generate a random transaction status.

        Returns:
            A transaction status.
        """
        if "status" not in self._transaction_data:
            header_dict, loaded_data = self._load_data_file(f"status_{self._dataset}.csv", "transaction")
            self._transaction_data["status"] = (header_dict, loaded_data)

        header_dict, loaded_data = self._transaction_data["status"]
        status_data = self._weighted_choice(loaded_data, header_dict)
        return str(status_data[header_dict["status"]])

    def get_channel(self) -> str:
        """Generate a random transaction channel.

        Returns:
            A transaction channel.
        """
        if "channels" not in self._transaction_data:
            header_dict, loaded_data = self._load_data_file(f"channels_{self._dataset}.csv", "transaction")
            self._transaction_data["channels"] = (header_dict, loaded_data)

        header_dict, loaded_data = self._transaction_data["channels"]
        channel_data = self._weighted_choice(loaded_data, header_dict)
        return str(channel_data[header_dict["channel"]])

    def get_location(self) -> str:
        """Generate a random location.

        Returns:
            A random city name.
        """
        try:
            if "cities" not in self._transaction_data:
                # Use existing datasets under common/city with semicolon delimiter
                from datamimic_ce.domains.utils.dataset_path import dataset_path
                from datamimic_ce.utils.file_util import FileUtil

                file_path = dataset_path("common", "city", f"city_{self._dataset}.csv", start=Path(__file__))
                rows = FileUtil.read_csv_to_list_of_tuples_without_header(file_path, delimiter=";")
                # Drop header if present
                if rows and rows[0] and rows[0][0] == "state.id":
                    rows = rows[1:]
                self._transaction_data["cities"] = ({}, rows)

            _, loaded_data = self._transaction_data["cities"]

            # Select a city at random - no weights for city data
            city_data = self._rng.choice(loaded_data)

            # city_data tuple format: (state.id, name, county, postalCode, areaCode)
            if len(city_data) > 1:
                return str(city_data[1])

            # Fall back to first field if parsing fails
            return str(city_data[0])
        except (FileNotFoundError, IndexError, KeyError, ValueError) as e:
            raise ValueError(f"Unable to load or parse cities for dataset {self._dataset}") from e

    def get_reference_number(self) -> str:
        """Generate a random transaction reference number.

        Returns:
            A random alphanumeric reference number.
        """
        return StringGenerator.rnd_str_from_regex("[A-Z0-9]{10,12}")

    def get_currency(self) -> dict:
        """Get currency information based on the current dataset.

        Returns:
            A dictionary containing currency code and symbol.
        """
        # Load country-specific currency mapping
        if "currency_mapping" not in self._currency_data:
            header_dict, loaded_data = self._load_data_file(f"currency_mapping_{self._dataset}.csv", "transaction")
            self._currency_data["currency_mapping"] = (header_dict, loaded_data)

        # Load all currencies for details (symbol, name)
        if "currencies" not in self._currency_data:
            currencies_path = dataset_path("ecommerce", f"currencies_{self.dataset}.csv", start=Path(__file__))
            # Convert the weighted data into the expected format (header_dict, data)
            header_dict = {"code": 0, "name": 1, "weight": 2, "symbol": 3}  # Define the header structure
            from typing import cast

            with currencies_path.open("r", newline="", encoding="utf-8") as csvfile:
                import csv

                csvreader = csv.reader(csvfile, delimiter=",")
                next(csvreader)  # Skip header row
                data = [tuple(row) for row in csvreader]  # Keep all columns to maintain structure
            data_typed = cast(list[tuple[object, ...]], data)
            self._currency_data["currencies"] = (header_dict, data_typed)

        # Get currency mapping for the current dataset
        mapping_header, mapping_data = self._currency_data["currency_mapping"]

        # Select a currency code based on weights
        selected_mapping = self._weighted_choice(mapping_data, mapping_header)
        currency_code = str(selected_mapping[mapping_header["currency_code"]])

        # Get additional currency details
        currency_header, currency_data = self._currency_data["currencies"]
        code_idx = currency_header["code"]
        filtered_currency = [row for row in currency_data if row[code_idx] == currency_code]

        if filtered_currency:
            currency_info = filtered_currency[0]
            return {
                "code": currency_code,
                "name": str(currency_info[currency_header["name"]]),
                "symbol": str(currency_info[currency_header["symbol"]]),
            }
        else:
            # Fallback if currency details not found
            return {"code": currency_code, "name": f"{currency_code} Currency", "symbol": currency_code}

    def get_description_template(self, transaction_type: str) -> str:
        """Get description template for transaction type.

        Args:
            transaction_type: The type of transaction.

        Returns:
            A description template string.
        """
        if "description_templates" not in self._transaction_data:
            header_dict, loaded_data = self._load_data_file(f"description_templates_{self._dataset}.csv", "transaction")
            self._transaction_data["description_templates"] = (header_dict, loaded_data)

        header_dict, loaded_data = self._transaction_data["description_templates"]

        # Filter templates by transaction type
        filtered_data = [row for row in loaded_data if row[header_dict["transaction_type"]] == transaction_type]

        if filtered_data:
            template_data = self._weighted_choice(filtered_data, header_dict)
            return str(template_data[header_dict["template"]])
        else:
            # Try to find generic template
            generic_data = [row for row in loaded_data if row[header_dict["transaction_type"]] == "Generic"]
            if generic_data:
                template_data = self._weighted_choice(generic_data, header_dict)
                return str(template_data[header_dict["template"]])
            else:
                # Last resort - use transaction type with merchant
                return f"{transaction_type} - {{}}"

    def generate_description(self, transaction_type: str, merchant_name: str) -> str:
        """Generate a transaction description based on type and merchant.

        Args:
            transaction_type: The type of transaction.
            merchant_name: The merchant name.

        Returns:
            A descriptive string for the transaction.
        """
        template = self.get_description_template(transaction_type)
        return template.format(merchant_name)

    def get_category_amount_range(self, category: str) -> tuple:
        """Get amount range for a specific merchant category.

        Args:
            category: The merchant category.

        Returns:
            A tuple containing minimum and maximum amount.
        """
        if "amount_ranges" not in self._amount_data:
            header_dict, loaded_data = self._load_data_file(f"amount_ranges_{self._dataset}.csv", "transaction")
            self._amount_data["amount_ranges"] = (header_dict, loaded_data)

        header_dict, loaded_data = self._amount_data["amount_ranges"]

        # Filter by category
        category_idx = header_dict["category"]
        filtered_data = [row for row in loaded_data if row[category_idx] == category]

        if filtered_data:
            # Use first matching category (should be only one)
            category_data = filtered_data[0]
            min_amount = float(str(category_data[header_dict["min_amount"]]))
            max_amount = float(str(category_data[header_dict["max_amount"]]))
            return min_amount, max_amount
        else:
            # Default range if category not found
            return 10.0, 200.0

    def get_transaction_type_modifier(self, transaction_type: str) -> float:
        """Get amount modifier for a specific transaction type.

        Args:
            transaction_type: The transaction type.

        Returns:
            A modifier value to apply to the transaction amount.
        """
        if "type_modifiers" not in self._amount_data:
            header_dict, loaded_data = self._load_data_file(
                f"transaction_type_modifiers_{self._dataset}.csv", "transaction"
            )
            self._amount_data["type_modifiers"] = (header_dict, loaded_data)

        header_dict, loaded_data = self._amount_data["type_modifiers"]

        # Filter out comment lines and filter by transaction type
        type_idx = header_dict["transaction_type"]
        filtered_data = [
            row
            for row in loaded_data
            if len(row) > 0
            and str(row[type_idx]).strip()
            and not str(row[type_idx]).strip().startswith("#")
            and row[type_idx] == transaction_type
        ]

        if filtered_data:
            # Use first matching transaction type (should be only one)
            type_data = filtered_data[0]
            return float(str(type_data[header_dict["modifier"]]))
        else:
            # Default modifier if type not found
            return 1.0

    def generate_amount(self, category: str, transaction_type: str) -> float:
        """Generate a random transaction amount based on category and type.

        Args:
            category: The merchant category.
            transaction_type: The type of transaction.

        Returns:
            A random amount suitable for the category and transaction type.
        """
        # Get range for the category
        min_amount, max_amount = self.get_category_amount_range(category)

        # Get modifier for transaction type
        modifier = self.get_transaction_type_modifier(transaction_type)

        # Generate amount with some randomness
        # Use log distribution to have more smaller transactions than larger ones
        amount = min_amount + (max_amount - min_amount) * self._rng.random() ** 1.5
        amount = amount * modifier

        # Round to 2 decimal places
        return round(amount, 2)

    def generate_transaction_data(self, bank_account=None) -> dict:
        """Generate complete transaction data.

        Args:
            bank_account: Optional bank account to associate with the transaction.
                          If provided, will use its currency.

        Returns:
            A dictionary containing transaction data.
        """
        transaction_info = self.get_transaction_type()
        transaction_type = transaction_info["type"]
        direction = transaction_info["direction"]

        category = self.get_merchant_category()
        merchant_name = self.get_merchant_name(category)

        # Get amount based on category and type
        amount = self.generate_amount(category, transaction_type)

        # Get currency (either from account or generate new)
        if bank_account and hasattr(bank_account, "currency"):
            currency = {
                "code": bank_account.currency,
                # Ideally we would also get name and symbol, but we'll keep it simple
                "symbol": "$"
                if bank_account.currency == "USD"
                else "€"
                if bank_account.currency == "EUR"
                else bank_account.currency,
            }
        else:
            currency = self.get_currency()

        return {
            "type": transaction_type,
            "direction": direction,
            "merchant": merchant_name,
            "merchant_category": category,
            "amount": amount,
            "currency_code": currency["code"],
            "currency_symbol": currency["symbol"],
            "status": self.get_status(),
            "channel": self.get_channel(),
            "location": self.get_location(),
            "reference_number": self.get_reference_number(),
            "description": self.generate_description(transaction_type, merchant_name),
        }
