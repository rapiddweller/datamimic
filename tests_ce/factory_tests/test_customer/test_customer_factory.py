from pathlib import Path

from tests_ce.factory_tests.test_customer.customer_factory import CustomerFactory



class TestCustomerFactory:
    _test_dir = Path(__file__).resolve().parent
    _customer_factory = CustomerFactory(_test_dir / "datamimic.xml", "customer")

    def test_customer_factory(self):
        customer = self._customer_factory.create()
        assert "id" in customer

    def test_customer_factory_batch(self):
        customers = self._customer_factory.create_batch(10)
        assert len(customers) == 10
        assert all("id" in customer for customer in customers)

    def test_customer_factory_create_with_custom_data(self):
        customer = self._customer_factory.create({"status": "active"})
        assert customer["status"] == "active"
        assert customer["id"] is not None

    def test_customer_factory_create_batch_with_custom_data(self):
        customers = self._customer_factory.create_batch(10, {"status": "active"})
        assert len(customers) == 10
        assert all(customer["status"] == "active" for customer in customers)
        assert all(customer["id"] is not None for customer in customers)
