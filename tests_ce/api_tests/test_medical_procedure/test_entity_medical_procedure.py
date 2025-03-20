import random
import string
import pytest

from datamimic_ce.domains.healthcare.models.medical_procedure import MedicalProcedure
from datamimic_ce.domains.healthcare.services.medical_procedure_service import MedicalProcedureService


class TestEntityMedicalProcedure:
    _supported_datasets = ["US", "DE"]
    def _test_single_medical_procedure(self, medical_procedure: MedicalProcedure):
        assert isinstance(medical_procedure, MedicalProcedure)
        assert isinstance(medical_procedure.procedure_id, str)
        assert isinstance(medical_procedure.description, str)
        assert isinstance(medical_procedure.specialty, str)
        assert isinstance(medical_procedure.duration_minutes, int)
        assert isinstance(medical_procedure.cost, float)
        assert isinstance(medical_procedure.requires_anesthesia, bool)
        assert isinstance(medical_procedure.is_surgical, bool)
        assert isinstance(medical_procedure.is_diagnostic, bool)
        assert isinstance(medical_procedure.is_preventive, bool)    
        assert isinstance(medical_procedure.recovery_time_days, int)            
        assert isinstance(medical_procedure.cpt_code, str)
        assert isinstance(medical_procedure.name, str)
        assert isinstance(medical_procedure.procedure_code, str)
        assert isinstance(medical_procedure.recovery_time_days, int)
        assert isinstance(medical_procedure.category, str)
        
        assert medical_procedure.procedure_id is not None
        assert medical_procedure.description is not None
        assert medical_procedure.specialty is not None
        assert medical_procedure.duration_minutes is not None
        assert medical_procedure.cost is not None
        assert medical_procedure.requires_anesthesia is not None
        assert medical_procedure.is_surgical is not None
        assert medical_procedure.is_diagnostic is not None
        assert medical_procedure.is_preventive is not None
        assert medical_procedure.recovery_time_days is not None
        assert medical_procedure.cpt_code is not None
        assert medical_procedure.name is not None
        assert medical_procedure.procedure_code is not None
        assert medical_procedure.category is not None
        assert medical_procedure.recovery_time_days is not None

        assert medical_procedure.procedure_id != ""
        assert medical_procedure.description != ""
        assert medical_procedure.specialty != ""
        assert medical_procedure.duration_minutes != 0
        assert medical_procedure.cost != 0.0
        assert medical_procedure.category != ""
        assert medical_procedure.cpt_code != ""
        assert medical_procedure.name != ""
        assert medical_procedure.procedure_code != ""   

    def test_generate_single_medical_procedure(self):   
        medical_procedure_service = MedicalProcedureService()
        medical_procedure = medical_procedure_service.generate()
        self._test_single_medical_procedure(medical_procedure)

    def test_generate_multiple_medical_procedures(self):
        medical_procedure_service = MedicalProcedureService()
        medical_procedures = medical_procedure_service.generate_batch(10)
        assert len(medical_procedures) == 10
        for medical_procedure in medical_procedures:
            self._test_single_medical_procedure(medical_procedure)

    def test_hospital_property_cache(self): 
        medical_procedure_service = MedicalProcedureService()
        medical_procedure = medical_procedure_service.generate()
        assert medical_procedure.procedure_id == medical_procedure.procedure_id
        assert medical_procedure.description == medical_procedure.description
        assert medical_procedure.specialty == medical_procedure.specialty
        assert medical_procedure.duration_minutes == medical_procedure.duration_minutes
        assert medical_procedure.cost == medical_procedure.cost
        assert medical_procedure.requires_anesthesia == medical_procedure.requires_anesthesia
        assert medical_procedure.is_surgical == medical_procedure.is_surgical
        assert medical_procedure.is_diagnostic == medical_procedure.is_diagnostic
        assert medical_procedure.is_preventive == medical_procedure.is_preventive
        assert medical_procedure.recovery_time_days == medical_procedure.recovery_time_days
        assert medical_procedure.cpt_code == medical_procedure.cpt_code
        assert medical_procedure.name == medical_procedure.name
        assert medical_procedure.procedure_code == medical_procedure.procedure_code
        assert medical_procedure.recovery_time_days == medical_procedure.recovery_time_days

    @pytest.mark.flaky(reruns=10)
    def test_two_different_entities(self):
        medical_procedure_service = MedicalProcedureService()    
        medical_procedure1 = medical_procedure_service.generate()
        medical_procedure2 = medical_procedure_service.generate()
        assert medical_procedure1.procedure_id != medical_procedure2.procedure_id
        assert medical_procedure1.description != medical_procedure2.description
        assert medical_procedure1.specialty != medical_procedure2.specialty
        assert medical_procedure1.duration_minutes != medical_procedure2.duration_minutes
        assert medical_procedure1.cost != medical_procedure2.cost
        assert medical_procedure1.recovery_time_days != medical_procedure2.recovery_time_days
        assert medical_procedure1.cpt_code != medical_procedure2.cpt_code
        assert medical_procedure1.name != medical_procedure2.name
        assert medical_procedure1.procedure_code != medical_procedure2.procedure_code
        assert medical_procedure1.recovery_time_days != medical_procedure2.recovery_time_days

    @pytest.mark.parametrize("dataset", _supported_datasets)
    def test_supported_datasets(self, dataset):
        medical_procedure_service = MedicalProcedureService(dataset=dataset)
        medical_procedure = medical_procedure_service.generate()
        self._test_single_medical_procedure(medical_procedure)

    def test_not_supported_dataset(self):
        random_dataset = "".join(random.choices(string.ascii_uppercase, k=2))
        while random_dataset in self._supported_datasets:
            random_dataset = "".join(random.choices(string.ascii_uppercase, k=2))
        # Raise ValueError because Street name data not found for unsupported dataset
        medical_procedure_service = MedicalProcedureService(dataset=random_dataset)
        medical_procedure = medical_procedure_service.generate()
        with pytest.raises(FileNotFoundError):
            medical_procedure.to_dict()