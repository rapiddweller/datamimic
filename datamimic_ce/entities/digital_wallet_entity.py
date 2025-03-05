"""Digital Wallet Entity for generating synthetic digital wallet data."""

import random
import uuid
from datetime import datetime, timedelta
from typing import Any

# Remove the import that's causing issues
# from datamimic_ce.utils.factory_util import FactoryUtil


class DigitalWalletEntity:
    """Entity for generating synthetic digital wallet data."""

    # Class constants for generating realistic data
    WALLET_TYPES = ["Mobile", "Online", "Crypto", "Bank", "Card"]
    CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CAD", "AUD", "BTC", "ETH", "LTC"]
    STATUSES = ["Active", "Inactive", "Suspended", "Pending", "Closed"]
    PAYMENT_METHOD_TYPES = ["Credit Card", "Debit Card", "Bank Account", "PayPal", "Apple Pay", "Google Pay"]
    TRANSACTION_TYPES = ["Deposit", "Withdrawal", "Transfer", "Payment", "Refund", "Fee"]

    def __init__(self, class_factory_util=None, locale: str = "en", dataset: str | None = None, **kwargs):
        """Initialize the DigitalWalletEntity.

        Args:
            class_factory_util: The class factory utility (not used but kept for compatibility)
            locale: The locale to use for generating data.
            dataset: The dataset to use (not used but kept for compatibility)
            **kwargs: Additional parameters for customizing the entity.
                wallet_type: Type of digital wallet.
                balance_min: Minimum balance amount.
                balance_max: Maximum balance amount.
                currency: Currency code.
                status: Wallet status.
        """
        self.locale = locale
        self._dataset = dataset
        # self.factory_util = FactoryUtil()  # Remove this line

        # Store custom parameters
        self._wallet_type = kwargs.get("wallet_type")
        self._currency = kwargs.get("currency")
        self._status = kwargs.get("status")
        self._balance_min = kwargs.get("balance_min", 0)
        self._balance_max = kwargs.get("balance_max", 10000)

        # Initialize field generators
        self._wallet_id = None
        self._owner_id = None
        self._balance = None
        self._created_date = None
        self._last_transaction_date = None
        self._payment_methods = None
        self._transaction_history = None
        self._settings = None

        # Generate initial data
        self.reset()

    def reset(self):
        """Reset all generated fields."""
        self._wallet_id = self._generate_wallet_id()
        self._owner_id = self._generate_owner_id()
        self._balance = self._generate_balance()
        self._created_date = self._generate_created_date()
        self._last_transaction_date = self._generate_last_transaction_date()
        self._payment_methods = self._generate_payment_methods()
        self._transaction_history = self._generate_transaction_history()
        self._settings = self._generate_settings()

    def _generate_wallet_id(self) -> str:
        """Generate a unique wallet ID.

        Returns:
            A string representing the wallet ID.
        """
        return f"WALLET-{random.randint(10000, 99999)}"

    def _generate_owner_id(self) -> str:
        """Generate an owner ID.

        Returns:
            A string representing the owner ID.
        """
        return f"USER-{random.randint(10000, 99999)}"

    def _generate_balance(self) -> float:
        """Generate a random balance within the specified range.

        Returns:
            A float representing the wallet balance.
        """
        return round(random.uniform(self._balance_min, self._balance_max), 2)

    def _generate_created_date(self) -> str:
        """Generate a random creation date within the last 5 years.

        Returns:
            A string representing the creation date in YYYY-MM-DD format.
        """
        days_ago = random.randint(1, 5 * 365)  # Within the last 5 years
        created_date = datetime.now() - timedelta(days=days_ago)
        return created_date.strftime("%Y-%m-%d")

    def _generate_last_transaction_date(self) -> str:
        """Generate a random last transaction date after the creation date.

        Returns:
            A string representing the last transaction date in YYYY-MM-DD format.
        """
        if not self._created_date:
            return datetime.now().strftime("%Y-%m-%d")

        created_date = datetime.strptime(self._created_date, "%Y-%m-%d")
        days_since_creation = (datetime.now() - created_date).days
        days_after_creation = random.randint(0, max(0, days_since_creation))
        last_transaction_date = created_date + timedelta(days=days_after_creation)
        return last_transaction_date.strftime("%Y-%m-%d")

    def _generate_payment_methods(self) -> list[dict[str, Any]]:
        """Generate a list of payment methods.

        Returns:
            A list of dictionaries representing payment methods.
        """
        num_methods = random.randint(1, 3)
        methods = []

        for i in range(num_methods):
            method_type = random.choice(self.PAYMENT_METHOD_TYPES)

            # Generate appropriate details based on method type
            if method_type in ["Credit Card", "Debit Card"]:
                details = {
                    "card_number": f"**** **** **** {random.randint(1000, 9999)}",
                    "expiry": f"{random.randint(1, 12)}/{datetime.now().year + random.randint(1, 5)}",
                    "name": f"{self._generate_random_name()} {self._generate_random_name()}",
                }
            elif method_type == "Bank Account":
                details = {
                    "account_number": f"****{random.randint(1000, 9999)}",
                    "routing_number": f"****{random.randint(1000, 9999)}",
                    "bank_name": random.choice(["Chase", "Bank of America", "Wells Fargo", "Citibank"]),
                }
            else:
                details = {
                    "linked_email": (
                        f"{self._generate_random_name().lower()}.{self._generate_random_name().lower()}@example.com"
                    )
                }

            methods.append(
                {
                    "type": method_type,
                    "details": details,
                    "is_default": i == 0,  # First method is default
                }
            )

        return methods

    def _generate_random_name(self) -> str:
        """Generate a random name.

        Returns:
            A random name string.
        """
        first_names = [
            "James",
            "Mary",
            "John",
            "Patricia",
            "Robert",
            "Jennifer",
            "Michael",
            "Linda",
            "William",
            "Elizabeth",
            "David",
            "Barbara",
            "Richard",
            "Susan",
            "Joseph",
            "Jessica",
        ]
        return random.choice(first_names)

    def _generate_transaction_history(self) -> list[dict[str, Any]]:
        """Generate a transaction history.

        Returns:
            A list of dictionaries representing transactions.
        """
        num_transactions = random.randint(3, 10)
        transactions: list[dict[str, Any]] = []

        if not self._created_date or not self._last_transaction_date:
            return transactions

        created_date = datetime.strptime(self._created_date, "%Y-%m-%d")
        last_transaction_date = datetime.strptime(self._last_transaction_date, "%Y-%m-%d")

        for _ in range(num_transactions):
            # Generate a random date between created_date and last_transaction_date
            days_range = (last_transaction_date - created_date).days
            if days_range > 0:
                random_days = random.randint(0, days_range)
                transaction_date = created_date + timedelta(days=random_days)
            else:
                transaction_date = created_date

            transaction_type = random.choice(self.TRANSACTION_TYPES)

            # Determine amount based on transaction type
            if transaction_type in ["Deposit", "Refund"]:
                amount = round(random.uniform(10, 1000), 2)
            elif transaction_type in ["Withdrawal", "Payment"]:
                amount = -round(random.uniform(10, 500), 2)
            elif transaction_type == "Fee":
                amount = -round(random.uniform(1, 25), 2)
            else:  # Transfer
                amount = round(random.uniform(-500, 500), 2)

            # Generate description based on transaction type
            if transaction_type == "Deposit":
                if self._payment_methods and len(self._payment_methods) > 0:
                    payment_method = random.choice(self._payment_methods)
                    description = f"Deposit from {payment_method['type']}"
                else:
                    description = "Deposit"
            elif transaction_type == "Withdrawal":
                if self._payment_methods and len(self._payment_methods) > 0:
                    payment_method = random.choice(self._payment_methods)
                    description = f"Withdrawal to {payment_method['type']}"
                else:
                    description = "Withdrawal"
            elif transaction_type == "Transfer":
                description = f"Transfer {'to' if amount < 0 else 'from'} wallet {uuid.uuid4().hex[:8]}"
            elif transaction_type == "Payment":
                merchants = ["Amazon", "Walmart", "Target", "Starbucks", "Netflix", "Uber", "DoorDash"]
                description = f"Payment to {random.choice(merchants)}"
            elif transaction_type == "Refund":
                merchants = ["Amazon", "Walmart", "Target", "Starbucks", "Netflix", "Uber", "DoorDash"]
                description = f"Refund from {random.choice(merchants)}"
            else:  # Fee
                description = "Service fee"

            transactions.append(
                {
                    "transaction_id": f"TXN-{uuid.uuid4().hex[:8]}",
                    "date": transaction_date.strftime("%Y-%m-%d"),
                    "type": transaction_type,
                    "amount": amount,
                    "description": description,
                }
            )

        # Sort transactions by date
        transactions.sort(key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d"))

        return transactions

    def _generate_settings(self) -> dict[str, Any]:
        """Generate wallet settings.

        Returns:
            A dictionary representing wallet settings.
        """
        return {
            "notifications_enabled": random.choice([True, False]),
            "two_factor_auth": random.choice([True, False]),
            "auto_reload": random.choice([True, False]),
            "daily_limit": float(random.choice([500, 1000, 2000, 5000])),
        }

    @property
    def wallet_id(self) -> str:
        """Get the wallet ID.

        Returns:
            A string representing the wallet ID.
        """
        assert self._wallet_id is not None, "wallet_id should not be None"
        return self._wallet_id

    @property
    def owner_id(self) -> str:
        """Get the owner ID.

        Returns:
            A string representing the owner ID.
        """
        assert self._owner_id is not None, "owner_id should not be None"
        return self._owner_id

    @property
    def wallet_type(self) -> str:
        """Get the wallet type.

        Returns:
            A string representing the wallet type.
        """
        if self._wallet_type:
            return self._wallet_type
        return random.choice(self.WALLET_TYPES)

    @property
    def balance(self) -> float:
        """Get the wallet balance.

        Returns:
            A float representing the wallet balance.
        """
        assert self._balance is not None, "balance should not be None"
        return self._balance

    @property
    def currency(self) -> str:
        """Get the wallet currency.

        Returns:
            A string representing the currency code.
        """
        if self._currency:
            return self._currency
        return random.choice(self.CURRENCIES)

    @property
    def created_date(self) -> str:
        """Get the wallet creation date.

        Returns:
            A string representing the creation date in YYYY-MM-DD format.
        """
        assert self._created_date is not None, "created_date should not be None"
        return self._created_date

    @property
    def last_transaction_date(self) -> str:
        """Get the last transaction date.

        Returns:
            A string representing the last transaction date in YYYY-MM-DD format.
        """
        assert self._last_transaction_date is not None, "last_transaction_date should not be None"
        return self._last_transaction_date

    @property
    def status(self) -> str:
        """Get the wallet status.

        Returns:
            A string representing the wallet status.
        """
        if self._status:
            return self._status
        return random.choice(self.STATUSES)

    @property
    def payment_methods(self) -> list[dict[str, Any]]:
        """Get the payment methods.

        Returns:
            A list of dictionaries representing payment methods.
        """
        assert self._payment_methods is not None, "payment_methods should not be None"
        return self._payment_methods

    @property
    def transaction_history(self) -> list[dict[str, Any]]:
        """Get the transaction history.

        Returns:
            A list of dictionaries representing transactions.
        """
        assert self._transaction_history is not None, "transaction_history should not be None"
        return self._transaction_history

    @property
    def settings(self) -> dict[str, Any]:
        """Get the wallet settings.

        Returns:
            A dictionary representing wallet settings.
        """
        assert self._settings is not None, "settings should not be None"
        return self._settings

    def to_dict(self) -> dict[str, Any]:
        """Convert the entity to a dictionary.

        Returns:
            A dictionary representation of the entity.
        """
        return {
            "wallet_id": self.wallet_id,
            "owner_id": self.owner_id,
            "wallet_type": self.wallet_type,
            "balance": self.balance,
            "currency": self.currency,
            "created_date": self.created_date,
            "last_transaction_date": self.last_transaction_date,
            "status": self.status,
            "payment_methods": self.payment_methods,
            "transaction_history": self.transaction_history,
            "settings": self.settings,
        }

    def generate_batch(self, count: int = 100) -> list[dict[str, Any]]:
        """Generate a batch of digital wallet records.

        Args:
            count: The number of records to generate.

        Returns:
            A list of dictionaries, each representing a digital wallet.
        """
        wallets = []
        for _ in range(count):
            self.reset()
            wallets.append(self.to_dict())
        return wallets
