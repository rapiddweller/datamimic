from pathlib import Path

from tests_ce.factory_test.test_customer.customer_factory import CustomerFactory


class TestCustomerFactory:
    _test_dir = Path(__file__).resolve().parent

    def test_customer_factory(self):
        customer_factory = CustomerFactory(self._test_dir / "datamimic.xml", "customer")
        # Basic customer creation using XML defaults
        customer = customer_factory.create()
        assert "id" in customer

    def test_customer_factory_batch(self):
        customer_factory = CustomerFactory(self._test_dir / "datamimic.xml", "customer")
        customers = customer_factory.create_batch(10)
        assert len(customers) == 10
        assert all("id" in customer for customer in customers)
