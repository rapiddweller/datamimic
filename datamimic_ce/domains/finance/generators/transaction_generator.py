# DATAMIMIC
# Copyright (c) 2023-2025 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

"""
Transaction Generator.

This module provides functionality to generate transaction data for financial accounts.
"""

import random
from pathlib import Path

from datamimic_ce.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.common.literal_generators.data_faker_generator import DataFakerGenerator
from datamimic_ce.utils.data_generation_ce_util import DataGenerationCEUtil
from datamimic_ce.utils.file_content_storage import FileContentStorage
from datamimic_ce.utils.file_util import FileUtil


class TransactionGenerator(BaseDomainGenerator):
    """Generator for financial transaction data."""

    def __init__(self, dataset: str | None = None):
        """Initialize the transaction generator.

        Args:
            dataset: The dataset code to use (e.g., 'US', 'DE'). Defaults to 'US'.
        """
        self._dataset = dataset or "US"
        self._reference_generator = DataFakerGenerator("uuid4")
        self._transaction_data: dict[str, tuple[dict[str, int], list[tuple]]] = {}
        self._currency_data: dict[str, tuple[dict[str, int], list[tuple]]] = {}
        self._amount_data: dict[str, tuple[dict[str, int], list[tuple]]] = {}

    @property
    def dataset(self) -> str:
        """Get the current dataset code.

        Returns:
            The dataset code.
        """
        return self._dataset

    def _get_base_path(self, subdirectory: str) -> Path:
        """Get base path for domain data files.

        Args:
            subdirectory: The subdirectory to append to the base path.

        Returns:
            The full path to the specified directory.
        """
        base_path = Path(__file__).parent.parent.parent.parent / "domain_data"

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

    def _load_data_file(self, file_name: str, subdirectory: str = "transaction") -> tuple[dict, list]:
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

    def _weighted_choice(self, data: list, header_dict: dict, weight_key: str = "weight") -> tuple:
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
            weights = [float(row[wgt_idx]) for row in data]
            return random.choices(data, weights=weights)[0]
        else:
            # If no weight key exists, use equal weights
            return random.choice(data)

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

        transaction_type = type_data[header_dict["transaction_type"]]
        direction = type_data[header_dict["direction"]].strip()

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
        return category_data[header_dict["category"]]

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
                return merchant_data[header_dict["merchant_name"]]
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
        except Exception:
            # Fallback if any error occurs
            self._merchant_recursion_count = 0  # Reset recursion counter
            return f"Generic {category} Merchant"

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
        return status_data[header_dict["status"]]

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
        return channel_data[header_dict["channel"]]

    def get_location(self) -> str:
        """Generate a random location.

        Returns:
            A random city name.
        """
        try:
            if "cities" not in self._transaction_data:
                header_dict, loaded_data = self._load_data_file(f"city_{self._dataset}.csv", "common/city")
                self._transaction_data["cities"] = (header_dict, loaded_data)

            header_dict, loaded_data = self._transaction_data["cities"]

            # Select a city at random - no weights for city data
            city_data = random.choice(loaded_data)

            # Parse the city name from the combined string
            # The format appears to be "state.id;name;county;postalCode;areaCode"
            if len(city_data) > 0 and ";" in city_data[0]:
                parts = city_data[0].split(";")
                if len(parts) > 1:
                    return parts[1]  # Return the city name

            # Fall back to the first field if parsing fails
            return city_data[0]
        except Exception:
            # Fallback if city data fails to load or parse
            default_cities = {
                "US": ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"],
                "DE": ["Berlin", "Hamburg", "Munich", "Cologne", "Frankfurt"],
            }
            return random.choice(default_cities.get(self._dataset, default_cities["US"]))

    def get_reference_number(self) -> str:
        """Generate a random transaction reference number.

        Returns:
            A random alphanumeric reference number.
        """
        return DataGenerationCEUtil.rnd_str_from_regex("[A-Z0-9]{10,12}")

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
            currencies_path = (
                Path(__file__).parent.parent.parent.parent / "domain_data" / "ecommerce" / "currencies.csv"
            )
            # Convert the weighted data into the expected format (header_dict, data)
            header_dict = {"code": 0, "name": 1, "weight": 2, "symbol": 3}  # Define the header structure
            with currencies_path.open("r", newline="", encoding="utf-8") as csvfile:
                import csv

                csvreader = csv.reader(csvfile, delimiter=",")
                next(csvreader)  # Skip header row
                data = [tuple(row) for row in csvreader]  # Keep all columns to maintain structure

            self._currency_data["currencies"] = (header_dict, data)

        # Get currency mapping for the current dataset
        mapping_header, mapping_data = self._currency_data["currency_mapping"]

        # Select a currency code based on weights
        selected_mapping = self._weighted_choice(mapping_data, mapping_header)
        currency_code = selected_mapping[mapping_header["currency_code"]]

        # Get additional currency details
        currency_header, currency_data = self._currency_data["currencies"]
        code_idx = currency_header["code"]
        filtered_currency = [row for row in currency_data if row[code_idx] == currency_code]

        if filtered_currency:
            currency_info = filtered_currency[0]
            return {
                "code": currency_code,
                "name": currency_info[currency_header["name"]],
                "symbol": currency_info[currency_header["symbol"]],
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
            return template_data[header_dict["template"]]
        else:
            # Try to find generic template
            generic_data = [row for row in loaded_data if row[header_dict["transaction_type"]] == "Generic"]
            if generic_data:
                template_data = self._weighted_choice(generic_data, header_dict)
                return template_data[header_dict["template"]]
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
            min_amount = float(category_data[header_dict["min_amount"]])
            max_amount = float(category_data[header_dict["max_amount"]])
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
            and row[type_idx].strip()
            and not row[type_idx].strip().startswith("#")
            and row[type_idx] == transaction_type
        ]

        if filtered_data:
            # Use first matching transaction type (should be only one)
            type_data = filtered_data[0]
            return float(type_data[header_dict["modifier"]])
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
        amount = min_amount + (max_amount - min_amount) * random.random() ** 1.5
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
