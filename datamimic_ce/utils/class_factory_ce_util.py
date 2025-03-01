# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com
from datamimic_ce.config import settings
from datamimic_ce.exporters.exporter_util import ExporterUtil
from datamimic_ce.generators.datetime_generator import DateTimeGenerator
from datamimic_ce.generators.integer_generator import IntegerGenerator
from datamimic_ce.generators.string_generator import StringGenerator
from datamimic_ce.logger import setup_logger
from datamimic_ce.parsers.parser_util import ParserUtil
from datamimic_ce.utils.base_class_factory_util import BaseClassFactoryUtil
from datamimic_ce.utils.data_generation_ce_util import DataGenerationCEUtil


class ClassFactoryCEUtil(BaseClassFactoryUtil):
    # Singleton instance of DataGenerationCEUtil
    _data_generation_util_instance = None

    def __init__(self):
        pass

    @staticmethod
    def get_task_util_cls():
        from datamimic_ce.tasks.task_util import TaskUtil

        return TaskUtil

    @staticmethod
    def get_city_entity(country_code):
        """
        Create and return a CityEntity instance for the given country_code.

        Args:
            country_code: The country code to use as dataset.

        Returns:
            A CityEntity instance configured with the specified country_code.
        """
        from datamimic_ce.entities.city_entity import CityEntity

        return CityEntity(ClassFactoryCEUtil(), dataset=country_code)

    @staticmethod
    def get_name_entity(locale):
        """
        Create and return a simple mock NameEntity.

        Args:
            locale: The locale to use (not used in this mock implementation).

        Returns:
            A simple mock object with the necessary methods.
        """

        # Create a simple mock object with the required methods
        class MockNameEntity:
            def reset(self):
                pass  # No-op reset method

        return MockNameEntity()

    @staticmethod
    def get_transaction_entity(locale="en", min_amount=0.01, max_amount=10000.00, **kwargs):
        """
        Create and return a TransactionEntity instance.

        Args:
            locale: The locale to use for localization
            min_amount: Minimum transaction amount
            max_amount: Maximum transaction amount
            **kwargs: Additional parameters to pass to the TransactionEntity constructor

        Returns:
            A TransactionEntity instance
        """
        from datamimic_ce.entities.transaction_entity import TransactionEntity

        return TransactionEntity(
            ClassFactoryCEUtil(), locale=locale, min_amount=min_amount, max_amount=max_amount, **kwargs
        )

    @staticmethod
    def get_payment_entity(locale="en", min_amount=0.01, max_amount=10000.00, **kwargs):
        """
        Create and return a PaymentEntity instance.

        Args:
            locale: The locale to use for localization
            min_amount: Minimum payment amount
            max_amount: Maximum payment amount
            **kwargs: Additional parameters to pass to the PaymentEntity constructor

        Returns:
            A PaymentEntity instance
        """
        from datamimic_ce.entities.payment_entity import PaymentEntity

        return PaymentEntity(
            ClassFactoryCEUtil(), locale=locale, min_amount=min_amount, max_amount=max_amount, **kwargs
        )

    @staticmethod
    def get_digital_wallet_entity(locale="en", dataset=None, **kwargs):
        """
        Create and return a DigitalWalletEntity instance.

        Args:
            locale: The locale to use for localization
            dataset: Optional dataset name
            **kwargs: Additional parameters to pass to the DigitalWalletEntity constructor

        Returns:
            A DigitalWalletEntity instance
        """
        from datamimic_ce.entities.digital_wallet_entity import DigitalWalletEntity

        return DigitalWalletEntity(ClassFactoryCEUtil(), locale=locale, dataset=dataset, **kwargs)

    @staticmethod
    def get_user_account_entity(locale="en", dataset=None, **kwargs):
        """
        Create and return a UserAccountEntity instance.

        Args:
            locale: The locale to use for localization
            dataset: Optional dataset name
            **kwargs: Additional parameters to pass to the UserAccountEntity constructor

        Returns:
            A UserAccountEntity instance
        """
        from datamimic_ce.entities.user_account_entity import UserAccountEntity

        return UserAccountEntity(ClassFactoryCEUtil(), locale=locale, dataset=dataset, **kwargs)

    @staticmethod
    def get_crm_entity(locale="en", dataset=None, **kwargs):
        """
        Create and return a CRMEntity instance.

        Args:
            locale: The locale to use for localization
            dataset: Optional dataset name
            **kwargs: Additional parameters to pass to the CRMEntity constructor

        Returns:
            A CRMEntity instance
        """
        from datamimic_ce.entities.crm_entity import CRMEntity

        return CRMEntity(ClassFactoryCEUtil(), locale=locale, dataset=dataset, **kwargs)

    @staticmethod
    def get_invoice_entity(locale="en", min_amount=10.00, max_amount=10000.00, dataset=None, **kwargs):
        """
        Create and return an InvoiceEntity instance.

        Args:
            locale: The locale to use for localization
            min_amount: Minimum invoice amount
            max_amount: Maximum invoice amount
            dataset: Optional dataset name
            **kwargs: Additional parameters to pass to the InvoiceEntity constructor

        Returns:
            An InvoiceEntity instance
        """
        from datamimic_ce.entities.invoice_entity import InvoiceEntity

        return InvoiceEntity(
            ClassFactoryCEUtil(), locale=locale, min_amount=min_amount, max_amount=max_amount, dataset=dataset, **kwargs
        )

    @staticmethod
    def get_order_entity(locale="en", dataset=None, **kwargs):
        """
        Create and return an OrderEntity instance.

        Args:
            locale: The locale to use for localization
            dataset: Optional dataset name
            **kwargs: Additional parameters to pass to the OrderEntity constructor

        Returns:
            An OrderEntity instance
        """
        from datamimic_ce.entities.order_entity import OrderEntity

        return OrderEntity(ClassFactoryCEUtil(), locale=locale, dataset=dataset, **kwargs)

    @staticmethod
    def get_product_entity(locale="en", min_price=0.99, max_price=9999.99, dataset=None, **kwargs):
        """
        Create and return a ProductEntity instance.

        Args:
            locale: The locale to use for localization
            min_price: Minimum product price
            max_price: Maximum product price
            dataset: Optional dataset name
            **kwargs: Additional parameters to pass to the ProductEntity constructor

        Returns:
            A ProductEntity instance
        """
        from datamimic_ce.entities.product_entity import ProductEntity

        return ProductEntity(
            ClassFactoryCEUtil(), locale=locale, min_price=min_price, max_price=max_price, dataset=dataset, **kwargs
        )

    @staticmethod
    def get_patient_entity(locale="en", dataset=None, **kwargs):
        """Get a PatientEntity instance.

        Args:
            locale: The locale to use for generating data.
            dataset: The dataset to use for generating data.
            **kwargs: Additional keyword arguments to pass to the PatientEntity constructor.

        Returns:
            A PatientEntity instance.
        """
        from datamimic_ce.entities.patient_entity import PatientEntity

        return PatientEntity(ClassFactoryCEUtil(), locale=locale, dataset=dataset, **kwargs)

    @staticmethod
    def get_doctor_entity(locale="en", dataset=None, **kwargs):
        """
        Create and return a DoctorEntity instance.

        Args:
            locale: The locale to use for localization
            dataset: Optional dataset name
            **kwargs: Additional parameters to pass to the DoctorEntity constructor

        Returns:
            A DoctorEntity instance
        """
        from datamimic_ce.entities.doctor_entity import DoctorEntity

        return DoctorEntity(ClassFactoryCEUtil(), locale=locale, dataset=dataset, **kwargs)

    @staticmethod
    def get_medical_record_entity(locale="en", dataset=None, **kwargs):
        """
        Create and return a MedicalRecordEntity instance.

        Args:
            locale: The locale to use for localization
            dataset: Optional dataset name
            **kwargs: Additional parameters to pass to the MedicalRecordEntity constructor

        Returns:
            A MedicalRecordEntity instance
        """
        from datamimic_ce.entities.healthcare.medical_record_entity import MedicalRecordEntity

        return MedicalRecordEntity(ClassFactoryCEUtil(), locale=locale, dataset=dataset, **kwargs)

    @staticmethod
    def get_medical_device_entity(locale="en", dataset=None, **kwargs):
        """
        Create and return a MedicalDeviceEntity instance.

        Args:
            locale: The locale to use for localization
            dataset: Optional dataset name
            **kwargs: Additional parameters to pass to the MedicalDeviceEntity constructor

        Returns:
            A MedicalDeviceEntity instance
        """
        from datamimic_ce.entities.healthcare.medical_device_entity import MedicalDeviceEntity

        return MedicalDeviceEntity(ClassFactoryCEUtil(), locale=locale, dataset=dataset, **kwargs)

    @staticmethod
    def get_lab_test_entity(locale="en", dataset=None, **kwargs):
        """
        Create and return a LabTestEntity instance.

        Args:
            locale: The locale to use for localization
            dataset: Optional dataset name
            **kwargs: Additional parameters to pass to the LabTestEntity constructor

        Returns:
            A LabTestEntity instance
        """
        from datamimic_ce.entities.lab_entity import LabEntity

        return LabEntity(ClassFactoryCEUtil(), locale=locale, dataset=dataset, **kwargs)

    @staticmethod
    def get_clinical_trial_entity(locale="en", dataset=None, **kwargs):
        """
        Create and return a ClinicalTrialEntity instance.

        Args:
            locale: The locale to use for localization
            dataset: Optional dataset name
            **kwargs: Additional parameters to pass to the ClinicalTrialEntity constructor

        Returns:
            A ClinicalTrialEntity instance
        """
        from datamimic_ce.entities.healthcare.clinical_trial_entity import ClinicalTrialEntity

        return ClinicalTrialEntity(ClassFactoryCEUtil(), locale=locale, dataset=dataset, **kwargs)

    @staticmethod
    def get_data_generation_util():
        """
        Get an instance of the data generation utility.

        Returns:
            An instance of DataGenerationCEUtil.
        """
        # Use the singleton pattern to ensure we only create one instance
        if ClassFactoryCEUtil._data_generation_util_instance is None:
            ClassFactoryCEUtil._data_generation_util_instance = DataGenerationCEUtil()
        return ClassFactoryCEUtil._data_generation_util_instance

    @staticmethod
    def get_datetime_generator():
        return DateTimeGenerator

    @staticmethod
    def get_integer_generator():
        return IntegerGenerator

    @staticmethod
    def get_string_generator():
        return StringGenerator

    @staticmethod
    def get_exporter_util():
        return ExporterUtil

    @staticmethod
    def get_parser_util_cls():
        return ParserUtil

    @staticmethod
    def get_datasource_registry():
        from datamimic_ce.data_sources.data_source_registry import DataSourceRegistry

        return DataSourceRegistry()

    @staticmethod
    def get_setup_logger_func():
        """
        Returns:
            The setup logger function.
        """
        return setup_logger

    @staticmethod
    def get_app_settings():
        """
        Abstract method to get the app settings.

        Returns:
            The app settings.
        """
        return settings
