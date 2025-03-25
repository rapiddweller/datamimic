from datamimic_ce.factory.datamimic_test_factory import DataMimicTestFactory

customer_factory = DataMimicTestFactory("test.xml", "customer")
customer = customer_factory.create()

print(customer["id"])  # 1
print(customer["first_name"])  # Jose
print(customer["last_name"])  # Ayers
