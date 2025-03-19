import datetime
import random
import string
import pytest

from datamimic_ce.domains.healthcare.models.medical_device import MedicalDevice
from datamimic_ce.domains.healthcare.services.medical_device_service import MedicalDeviceService


class TestEntityMedicalDevice:
    _supported_datasets = ["US", "DE"]
    def _test_single_medical_device(self, medical_device: MedicalDevice):
        assert isinstance(medical_device, MedicalDevice)
        assert isinstance(medical_device.device_id, str)
        assert isinstance(medical_device.device_type, str)
        assert isinstance(medical_device.manufacturer, str) 
        assert isinstance(medical_device.model_number, str)
        assert isinstance(medical_device.serial_number, str)
        assert isinstance(medical_device.manufacture_date, str)
        assert isinstance(medical_device.expiration_date, str)
        assert isinstance(medical_device.last_maintenance_date, str)
        assert isinstance(medical_device.next_maintenance_date, str)
        assert isinstance(medical_device.status, str)           
        assert isinstance(medical_device.location, str)
        assert isinstance(medical_device.assigned_to, str)
        assert isinstance(medical_device.specifications, dict)
        assert isinstance(medical_device.usage_logs, list)
        assert isinstance(medical_device.maintenance_history, list)

        assert medical_device.device_id is not None and medical_device.device_id != ""
        assert medical_device.manufacturer is not None and medical_device.manufacturer != ""
        assert medical_device.model_number is not None and medical_device.model_number != ""
        assert medical_device.serial_number is not None and medical_device.serial_number != ""
        assert medical_device.manufacture_date is not None and medical_device.manufacture_date != ""
        assert medical_device.expiration_date is not None and medical_device.expiration_date != ""
        assert medical_device.last_maintenance_date is not None and medical_device.last_maintenance_date != ""
        assert medical_device.next_maintenance_date is not None and medical_device.next_maintenance_date != ""
        assert medical_device.status is not None and medical_device.status != ""
        assert medical_device.location is not None and medical_device.location != ""
        assert medical_device.assigned_to is not None and medical_device.assigned_to != ""
        assert medical_device.specifications is not None and medical_device.specifications != {}
        assert medical_device.usage_logs is not None and medical_device.usage_logs != []
        assert medical_device.maintenance_history is not None and medical_device.maintenance_history != []      

    def test_generate_single_medical_device(self):
        medical_device_service = MedicalDeviceService()
        medical_device = medical_device_service.generate()
        self._test_single_medical_device(medical_device)

    def test_generate_multiple_medical_devices(self):
        medical_device_service = MedicalDeviceService()
        medical_devices = medical_device_service.generate_batch(10)
        assert len(medical_devices) == 10
        for medical_device in medical_devices:
            self._test_single_medical_device(medical_device)

    def test_hospital_property_cache(self): 
        medical_device_service = MedicalDeviceService()
        medical_device = medical_device_service.generate()
        assert medical_device.device_id == medical_device.device_id
        assert medical_device.manufacturer == medical_device.manufacturer
        assert medical_device.model_number == medical_device.model_number
        assert medical_device.serial_number == medical_device.serial_number
        assert medical_device.manufacture_date == medical_device.manufacture_date
        assert medical_device.expiration_date == medical_device.expiration_date
        assert medical_device.last_maintenance_date == medical_device.last_maintenance_date
        assert medical_device.next_maintenance_date == medical_device.next_maintenance_date
        assert medical_device.status == medical_device.status
        assert medical_device.location == medical_device.location
        assert medical_device.assigned_to == medical_device.assigned_to
        assert medical_device.specifications == medical_device.specifications
        assert medical_device.usage_logs == medical_device.usage_logs
        assert medical_device.maintenance_history == medical_device.maintenance_history

    def test_two_different_entities(self):
        medical_device_service = MedicalDeviceService()    
        medical_device1 = medical_device_service.generate()
        medical_device2 = medical_device_service.generate()
        assert medical_device1.device_id != medical_device2.device_id
        assert medical_device1.manufacturer != medical_device2.manufacturer
        assert medical_device1.model_number != medical_device2.model_number
        assert medical_device1.serial_number != medical_device2.serial_number
        assert medical_device1.manufacture_date != medical_device2.manufacture_date
        assert medical_device1.expiration_date != medical_device2.expiration_date
        assert medical_device1.last_maintenance_date != medical_device2.last_maintenance_date
        assert medical_device1.next_maintenance_date != medical_device2.next_maintenance_date
        assert medical_device1.status != medical_device2.status
        assert medical_device1.location != medical_device2.location
        assert medical_device1.assigned_to != medical_device2.assigned_to
        assert medical_device1.specifications != medical_device2.specifications
        assert medical_device1.usage_logs != medical_device2.usage_logs
        assert medical_device1.maintenance_history != medical_device2.maintenance_history

    @pytest.mark.parametrize("dataset", _supported_datasets)
    def test_supported_datasets(self, dataset):
        medical_device_service = MedicalDeviceService(dataset=dataset)
        medical_device = medical_device_service.generate()
        self._test_single_medical_device(medical_device)

    def test_not_supported_dataset(self):
        random_dataset = "".join(random.choices(string.ascii_uppercase, k=2))
        while random_dataset in self._supported_datasets:
            random_dataset = "".join(random.choices(string.ascii_uppercase, k=2))
        # Raise ValueError because Street name data not found for unsupported dataset
        with pytest.raises(ValueError):
            medical_device_service = MedicalDeviceService(dataset=random_dataset)
