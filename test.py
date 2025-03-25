import unittest
from datamimic_ce.domains.finance.services import BankAccountService, TransactionService
from my_application.transaction_processor import TransactionProcessor

class TestTransactionProcessor(unittest.TestCase):
    def setUp(self):
        # Create services
        self.account_service = BankAccountService()
        self.transaction_service = TransactionService()
        
        # Generate test data
        self.test_account = self.account_service.generate()
        self.test_transactions = self.transaction_service.generate_batch(
            count=10,
            account_id=self.test_account.account_id
        )
        
        # Initialize system under test
        self.processor = TransactionProcessor()
        
    def test_transaction_processing(self):
        # Use generated data in test
        result = self.processor.process_transactions(
            self.test_account, 
            self.test_transactions
        )
        
        # Assertions
        self.assertEqual(len(result.processed), 10)
        self.assertEqual(result.error_count, 0)