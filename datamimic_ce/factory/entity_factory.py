# # DATAMIMIC
# # Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# # This software is licensed under the MIT License.
# # See LICENSE file for the full text of the license.
# # For questions and support, contact: info@rapiddweller.com

# import random


# class EntityFactory:
#     @staticmethod
#     def get_city_entity(country_code):
#         """
#         Create and return a City entity instance for the given country_code.

#         Args:
#             country_code: The country code to use as dataset.

#         Returns:
#             A City entity instance from the domain model.
#         """
#         from datamimic_ce.domains.common.models.city import City
#         return City(dataset=country_code)

#     @staticmethod
#     def get_name_entity(locale):
#         """
#         Create and return a simple mock NameEntity.

#         Args:
#             locale: The locale to use (not used in this mock implementation).

#         Returns:
#             A simple mock object with the necessary methods.
#         """

#         # Create a simple mock object with the required methods
#         class MockNameEntity:
#             def reset(self):
#                 pass  # No-op reset method

#         return MockNameEntity()

#     @staticmethod
#     def get_transaction_entity(locale="en", min_amount=0.01, max_amount=10000.00, **kwargs):
#         """
#         Create and return a TransactionEntity instance.

#         Args:
#             locale: The locale to use for localization
#             min_amount: Minimum transaction amount
#             max_amount: Maximum transaction amount
#             **kwargs: Additional parameters to pass to the TransactionEntity constructor

#         Returns:
#             A TransactionEntity instance
#         """
#         from datamimic_ce.entities.transaction_entity import TransactionEntity

#         return TransactionEntity(
#             ClassFactoryCEUtil(), locale=locale, min_amount=min_amount, max_amount=max_amount, **kwargs
#         )

#     @staticmethod
#     def get_payment_entity(locale="en", min_amount=0.01, max_amount=10000.00, **kwargs):
#         """
#         Create and return a PaymentEntity instance.

#         Args:
#             locale: The locale to use for localization
#             min_amount: Minimum payment amount
#             max_amount: Maximum payment amount
#             **kwargs: Additional parameters to pass to the PaymentEntity constructor

#         Returns:
#             A PaymentEntity instance
#         """
#         from datamimic_ce.entities.payment_entity import PaymentEntity

#         return PaymentEntity(
#             ClassFactoryCEUtil(), locale=locale, min_amount=min_amount, max_amount=max_amount, **kwargs
#         )

#     @staticmethod
#     def get_digital_wallet_entity(locale="en", dataset=None, **kwargs):
#         """
#         Create and return a DigitalWalletEntity instance.

#         Args:
#             locale: The locale to use for localization
#             dataset: Optional dataset name
#             **kwargs: Additional parameters to pass to the DigitalWalletEntity constructor

#         Returns:
#             A DigitalWalletEntity instance
#         """
#         from datamimic_ce.entities.digital_wallet_entity import DigitalWalletEntity

#         return DigitalWalletEntity(ClassFactoryCEUtil(), locale=locale, dataset=dataset, **kwargs)

#     @staticmethod
#     def get_user_account_entity(locale="en", dataset=None, **kwargs):
#         """
#         Create and return a UserAccountEntity instance.

#         Args:
#             locale: The locale to use for localization
#             dataset: Optional dataset name
#             **kwargs: Additional parameters to pass to the UserAccountEntity constructor

#         Returns:
#             A UserAccountEntity instance
#         """
#         from datamimic_ce.entities.user_account_entity import UserAccountEntity

#         return UserAccountEntity(ClassFactoryCEUtil(), locale=locale, dataset=dataset, **kwargs)

#     @staticmethod
#     def get_crm_entity(locale="en", dataset=None, **kwargs):
#         """
#         Create and return a CRMEntity instance.

#         Args:
#             locale: The locale to use for localization
#             dataset: Optional dataset name
#             **kwargs: Additional parameters to pass to the CRMEntity constructor

#         Returns:
#             A CRMEntity instance
#         """
#         from datamimic_ce.entities.crm_entity import CRMEntity

#         return CRMEntity(ClassFactoryCEUtil(), locale=locale, dataset=dataset, **kwargs)

#     @staticmethod
#     def get_invoice_entity(locale="en", min_amount=10.00, max_amount=10000.00, dataset=None, **kwargs):
#         """
#         Create and return an InvoiceEntity instance.

#         Args:
#             locale: The locale to use for localization
#             min_amount: Minimum invoice amount
#             max_amount: Maximum invoice amount
#             dataset: Optional dataset name
#             **kwargs: Additional parameters to pass to the InvoiceEntity constructor

#         Returns:
#             An InvoiceEntity instance
#         """
#         from datamimic_ce.entities.invoice_entity import InvoiceEntity

#         return InvoiceEntity(
#             ClassFactoryCEUtil(), locale=locale, min_amount=min_amount, max_amount=max_amount, dataset=dataset, **kwargs
#         )

#     @staticmethod
#     def get_order_entity(locale="en", dataset=None, **kwargs):
#         """
#         Create and return an Order entity instance.

#         Args:
#             locale: The locale to use for localization
#             dataset: Optional dataset name
#             **kwargs: Additional parameters to pass to the Order constructor

#         Returns:
#             An Order entity instance from the domain model.
#         """
#         from datamimic_ce.domains.ecommerce.models.order import Order
#         return Order(locale=locale, dataset=dataset, **kwargs)

#     @staticmethod
#     def get_product_entity(locale="en", min_price=0.99, max_price=9999.99, dataset=None, **kwargs):
#         """
#         Create and return a Product entity instance.

#         Args:
#             locale: The locale to use for localization
#             min_price: Minimum product price
#             max_price: Maximum product price
#             dataset: Optional dataset name
#             **kwargs: Additional parameters to pass to the Product constructor

#         Returns:
#             A Product entity instance from the domain model.
#         """
#         from datamimic_ce.domains.ecommerce.models.product import Product
#         return Product(
#             locale=locale, min_price=min_price, max_price=max_price, dataset=dataset, **kwargs
#         )

#     @staticmethod
#     def get_patient_entity(locale="en", dataset=None, **kwargs):
#         """Get a Patient entity instance.

#         Args:
#             locale: The locale to use for generating data.
#             dataset: The dataset to use for generating data.
#             **kwargs: Additional keyword arguments to pass to the Patient constructor.

#         Returns:
#             A Patient entity instance from the domain model.
#         """
#         from datamimic_ce.domains.healthcare.models.patient import Patient
#         return Patient(locale=locale, dataset=dataset, **kwargs)

#     @staticmethod
#     def get_doctor_entity(locale="en", dataset=None, **kwargs):
#         """
#         Create and return a Doctor entity instance.

#         Args:
#             locale: The locale to use for localization
#             dataset: Optional dataset name
#             **kwargs: Additional parameters to pass to the Doctor constructor

#         Returns:
#             A Doctor entity instance from the domain model.
#         """
#         from datamimic_ce.domains.healthcare.models.doctor import Doctor
#         return Doctor(locale=locale, dataset=dataset, **kwargs)

#     @staticmethod
#     def get_medical_record_entity(locale="en", dataset=None, **kwargs):
#         """
#         Create and return a MedicalRecord entity instance.

#         Args:
#             locale: The locale to use for localization
#             dataset: Optional dataset name
#             **kwargs: Additional parameters to pass to the MedicalRecord constructor

#         Returns:
#             A MedicalRecord entity instance from the domain model.
#         """
#         from datamimic_ce.domains.healthcare.models.medical_record import MedicalRecord
#         return MedicalRecord(locale=locale, dataset=dataset, **kwargs)
            
#     @staticmethod
#     def get_company_entity(locale="en", dataset=None, count=1, **kwargs):
#         """
#         Create and return a Company entity instance.

#         Args:
#             locale: The locale to use for localization
#             dataset: Optional dataset name (country code)
#             count: Number of companies to generate
#             **kwargs: Additional parameters to pass to the Company constructor

#         Returns:
#             A Company entity instance from the domain model.
#         """
#         from datamimic_ce.domains.common.models.company import Company
#         return Company(dataset=dataset, count=count, **kwargs)

#     @staticmethod
#     def get_medical_device_entity(locale="en", dataset=None, **kwargs):
#         """
#         Create and return a MedicalDevice entity instance.

#         Args:
#             locale: The locale to use for localization
#             dataset: Optional dataset name
#             **kwargs: Additional parameters to pass to the MedicalDevice constructor

#         Returns:
#             A MedicalDevice entity instance from the domain model.
#         """
#         from datamimic_ce.domains.healthcare.models.medical_device import MedicalDevice
#         return MedicalDevice(locale=locale, dataset=dataset, **kwargs)

#     @staticmethod
#     def get_lab_test_entity(locale="en", dataset=None, **kwargs):
#         """
#         Create and return a LabTestEntity instance.

#         Args:
#             locale: The locale to use for localization
#             dataset: Optional dataset name
#             **kwargs: Additional parameters to pass to the LabTestEntity constructor

#         Returns:
#             A LabTestEntity instance
#         """
#         from datamimic_ce.entities.lab_entity import LabEntity

#         return LabEntity(ClassFactoryCEUtil(), locale=locale, dataset=dataset, **kwargs)

#     @staticmethod
#     def get_clinical_trial_entity(locale="en", dataset=None, **kwargs):
#         """
#         Create and return a ClinicalTrialEntity instance.

#         Args:
#             locale: The locale to use for localization
#             dataset: Optional dataset name
#             **kwargs: Additional parameters to pass to the ClinicalTrialEntity constructor

#         Returns:
#             A ClinicalTrialEntity instance
#         """
#         from datamimic_ce.entities.healthcare.clinical_trial_entity import ClinicalTrialEntity

#         return ClinicalTrialEntity(ClassFactoryCEUtil(), locale=locale, dataset=dataset, **kwargs)

#     @staticmethod
#     def create_person_entity(locale="en", dataset=None, **kwargs):
#         """
#         Create and return a simple person entity for basic person name generation.

#         Args:
#             locale: The locale to use for localization
#             dataset: Optional dataset name
#             **kwargs: Additional parameters

#         Returns:
#             A simple person entity with first_name and last_name methods
#         """

#         class SimplePersonEntity:
#             def __init__(self):
#                 self.first_names_male = ["James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph"]
#                 self.first_names_female = ["Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Susan", "Jessica"]
#                 self.last_names = ["Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson"]

#             def first_name(self, gender=None):
#                 """Generate a first name based on gender."""
#                 if gender and gender.upper() == "F":
#                     return random.choice(self.first_names_female)
#                 else:
#                     return random.choice(self.first_names_male)

#             def last_name(self):
#                 """Generate a last name."""
#                 return random.choice(self.last_names)

#         return SimplePersonEntity()
