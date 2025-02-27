"""Unit tests for the DigitalWalletEntity class."""
import re
import unittest
from datetime import datetime

from datamimic_ce.entities.digital_wallet_entity import DigitalWalletEntity
from datamimic_ce.utils.class_factory_ce_util import ClassFactoryCEUtil


class TestDigitalWalletEntity(unittest.TestCase):
    """Test cases for the DigitalWalletEntity class."""

    def setUp(self):
        """Set up test fixtures."""
        # Use a fixed status to ensure consistency across tests
        self.digital_wallet = DigitalWalletEntity(status="Active")

    def test_init(self):
        """Test initialization of DigitalWalletEntity."""
        # Test default initialization
        self.assertEqual(self.digital_wallet.locale, "en")
        
        # Test with custom locale
        digital_wallet = DigitalWalletEntity(locale="fr")
        self.assertEqual(digital_wallet.locale, "fr")
        
        # Test with custom parameters
        digital_wallet = DigitalWalletEntity(
            wallet_type="Crypto",
            balance_min=1000,
            balance_max=5000
        )
        self.assertEqual(digital_wallet._wallet_type, "Crypto")
        self.assertEqual(digital_wallet._balance_min, 1000)
        self.assertEqual(digital_wallet._balance_max, 5000)

    def test_wallet_id_generation(self):
        """Test wallet_id generation."""
        wallet_id = self.digital_wallet.wallet_id
        
        # Check format (e.g., "WALLET-12345")
        self.assertTrue(re.match(r"WALLET-\d+", wallet_id))
        
        # Check that it's consistent
        self.assertEqual(wallet_id, self.digital_wallet.wallet_id)
        
        # Check that it changes after reset
        self.digital_wallet.reset()
        self.assertNotEqual(wallet_id, self.digital_wallet.wallet_id)

    def test_owner_id_generation(self):
        """Test owner_id generation."""
        owner_id = self.digital_wallet.owner_id
        
        # Check that it's a string
        self.assertIsInstance(owner_id, str)
        
        # Check that it's not empty
        self.assertTrue(len(owner_id) > 0)
        
        # Check that it's consistent
        self.assertEqual(owner_id, self.digital_wallet.owner_id)

    def test_wallet_type_generation(self):
        """Test wallet_type generation."""
        wallet_type = self.digital_wallet.wallet_type
        
        # Check that it's one of the expected types
        self.assertIn(wallet_type, DigitalWalletEntity.WALLET_TYPES)
        
        # Test with custom wallet type
        digital_wallet = DigitalWalletEntity(wallet_type="Crypto")
        self.assertEqual(digital_wallet.wallet_type, "Crypto")

    def test_balance_generation(self):
        """Test balance generation."""
        balance = self.digital_wallet.balance
        
        # Check that it's a float
        self.assertIsInstance(balance, float)
        
        # Check that it's within default range
        self.assertTrue(0 <= balance <= 10000)
        
        # Test with custom balance range
        digital_wallet = DigitalWalletEntity(balance_min=1000, balance_max=2000)
        self.assertTrue(1000 <= digital_wallet.balance <= 2000)

    def test_currency_generation(self):
        """Test currency generation."""
        currency = self.digital_wallet.currency
        
        # Check that it's a string
        self.assertIsInstance(currency, str)
        
        # Check that it's one of the expected currencies
        self.assertIn(currency, DigitalWalletEntity.CURRENCIES)
        
        # Test with custom currency
        digital_wallet = DigitalWalletEntity(currency="BTC")
        self.assertEqual(digital_wallet.currency, "BTC")

    def test_created_date_generation(self):
        """Test created_date generation."""
        created_date = self.digital_wallet.created_date
        
        # Check that it's a string
        self.assertIsInstance(created_date, str)
        
        # Check that it's a valid date format (YYYY-MM-DD)
        try:
            datetime.strptime(created_date, "%Y-%m-%d")
        except ValueError:
            self.fail("created_date is not in the expected format YYYY-MM-DD")

    def test_last_transaction_date_generation(self):
        """Test last_transaction_date generation."""
        last_transaction_date = self.digital_wallet.last_transaction_date
        
        # Check that it's a string
        self.assertIsInstance(last_transaction_date, str)
        
        # Check that it's a valid date format (YYYY-MM-DD)
        try:
            datetime.strptime(last_transaction_date, "%Y-%m-%d")
        except ValueError:
            self.fail("last_transaction_date is not in the expected format YYYY-MM-DD")
        
        # Check that last_transaction_date is not before created_date
        self.assertGreaterEqual(
            datetime.strptime(last_transaction_date, "%Y-%m-%d"),
            datetime.strptime(self.digital_wallet.created_date, "%Y-%m-%d")
        )

    def test_status_generation(self):
        """Test status generation."""
        status = self.digital_wallet.status
        
        # Check that it's a string
        self.assertIsInstance(status, str)
        
        # Check that it's one of the expected statuses
        self.assertIn(status, DigitalWalletEntity.STATUSES)
        
        # Test with custom status
        digital_wallet = DigitalWalletEntity(status="Suspended")
        self.assertEqual(digital_wallet.status, "Suspended")

    def test_payment_methods_generation(self):
        """Test payment_methods generation."""
        payment_methods = self.digital_wallet.payment_methods
        
        # Check that it's a list
        self.assertIsInstance(payment_methods, list)
        
        # Check that each item has the expected structure
        for method in payment_methods:
            self.assertIn("type", method)
            self.assertIn("details", method)
            self.assertIn("is_default", method)
            self.assertIsInstance(method["is_default"], bool)

    def test_transaction_history_generation(self):
        """Test transaction_history generation."""
        transaction_history = self.digital_wallet.transaction_history
        
        # Check that it's a list
        self.assertIsInstance(transaction_history, list)
        
        # Check that each item has the expected structure
        for transaction in transaction_history:
            self.assertIn("transaction_id", transaction)
            self.assertIn("date", transaction)
            self.assertIn("type", transaction)
            self.assertIn("amount", transaction)
            self.assertIn("description", transaction)
            self.assertIsInstance(transaction["amount"], float)

    def test_settings_generation(self):
        """Test settings generation."""
        settings = self.digital_wallet.settings
        
        # Check that it's a dictionary
        self.assertIsInstance(settings, dict)
        
        # Check that it has the expected keys
        self.assertIn("notifications_enabled", settings)
        self.assertIn("two_factor_auth", settings)
        self.assertIn("auto_reload", settings)
        self.assertIn("daily_limit", settings)
        self.assertIsInstance(settings["notifications_enabled"], bool)
        self.assertIsInstance(settings["two_factor_auth"], bool)
        self.assertIsInstance(settings["auto_reload"], bool)
        self.assertIsInstance(settings["daily_limit"], float)

    def test_to_dict(self):
        """Test to_dict method."""
        wallet_dict = self.digital_wallet.to_dict()
        
        # Check that it's a dictionary
        self.assertIsInstance(wallet_dict, dict)
        
        # Check that it has all the expected keys
        expected_keys = [
            "wallet_id", "owner_id", "wallet_type", "balance", "currency",
            "created_date", "last_transaction_date", "status",
            "payment_methods", "transaction_history", "settings"
        ]
        for key in expected_keys:
            self.assertIn(key, wallet_dict)
        
        # Check that the values match the properties
        self.assertEqual(wallet_dict["wallet_id"], self.digital_wallet.wallet_id)
        self.assertEqual(wallet_dict["balance"], self.digital_wallet.balance)
        self.assertEqual(wallet_dict["status"], self.digital_wallet.status)

    def test_generate_batch(self):
        """Test generate_batch method."""
        batch_size = 5
        wallets = self.digital_wallet.generate_batch(count=batch_size)
        
        # Check that it returns a list of the correct size
        self.assertIsInstance(wallets, list)
        self.assertEqual(len(wallets), batch_size)
        
        # Check that each item is a dictionary with the expected keys
        for wallet in wallets:
            self.assertIsInstance(wallet, dict)
            self.assertIn("wallet_id", wallet)
            self.assertIn("balance", wallet)
            self.assertIn("wallet_type", wallet)
            
        # Check that the wallets are unique
        wallet_ids = [wallet["wallet_id"] for wallet in wallets]
        self.assertEqual(len(wallet_ids), len(set(wallet_ids)))

    def test_reset(self):
        """Test reset method."""
        # Get initial values
        initial_wallet_id = self.digital_wallet.wallet_id
        initial_balance = self.digital_wallet.balance
        
        # Reset the entity
        self.digital_wallet.reset()
        
        # Check that values have changed
        self.assertNotEqual(initial_wallet_id, self.digital_wallet.wallet_id)
        self.assertNotEqual(initial_balance, self.digital_wallet.balance)

    def test_class_factory_integration(self):
        """Test integration with ClassFactoryCEUtil."""
        # Use a direct call to the factory method instead of patching
        wallet = ClassFactoryCEUtil.get_digital_wallet_entity(locale="en_US", wallet_type="Mobile")
        
        # Verify the wallet was created with the correct parameters
        self.assertEqual(wallet.locale, "en_US")
        self.assertEqual(wallet.wallet_type, "Mobile")


if __name__ == '__main__':
    unittest.main() 