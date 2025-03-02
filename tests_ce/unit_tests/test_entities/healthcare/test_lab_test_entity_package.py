# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


from datamimic_ce.entities.healthcare.lab_test_entity import LabTestEntity


def test_lab_test_entity_initialization():
    """Test that the LabTestEntity can be initialized."""
    entity = LabTestEntity()
    assert entity is not None


def test_lab_test_entity_properties():
    """Test that the LabTestEntity properties can be accessed."""
    entity = LabTestEntity()
    assert entity.test_id is not None
    assert entity.patient_id is not None
    assert entity.doctor_id is not None
    assert entity.test_type is not None
    assert entity.test_name is not None
    assert entity.test_date is not None
    assert entity.result_date is not None
    assert entity.status is not None
    assert entity.specimen_type is not None
    assert entity.specimen_collection_date is not None
    assert entity.results is not None
    assert entity.performing_lab is not None
    assert entity.lab_address is not None
    assert entity.ordering_provider is not None
    assert entity.notes is not None


def test_lab_test_entity_to_dict():
    """Test that the LabTestEntity can be converted to a dictionary."""
    entity = LabTestEntity()
    entity_dict = entity.to_dict()
    assert isinstance(entity_dict, dict)
    assert "test_id" in entity_dict
    assert "patient_id" in entity_dict
    assert "doctor_id" in entity_dict
    assert "test_type" in entity_dict
    assert "test_name" in entity_dict
    assert "test_date" in entity_dict
    assert "result_date" in entity_dict
    assert "status" in entity_dict
    assert "specimen_type" in entity_dict
    assert "specimen_collection_date" in entity_dict
    assert "results" in entity_dict
    assert "abnormal_flags" in entity_dict
    assert "performing_lab" in entity_dict
    assert "lab_address" in entity_dict
    assert "ordering_provider" in entity_dict
    assert "notes" in entity_dict


def test_lab_test_entity_reset():
    """Test that the LabTestEntity can be reset."""
    entity = LabTestEntity()
    test_id_1 = entity.test_id
    entity.reset()
    test_id_2 = entity.test_id
    assert test_id_1 != test_id_2


def test_lab_test_entity_generate_batch():
    """Test that the LabTestEntity can generate a batch of entities."""
    entity = LabTestEntity()
    batch = entity.generate_batch(count=5)
    assert isinstance(batch, list)
    assert len(batch) == 5
    assert all(isinstance(item, dict) for item in batch)


def test_lab_test_entity_with_dataset():
    """Test that the LabTestEntity can be initialized with a dataset."""
    entity = LabTestEntity(dataset="DE")
    assert entity._dataset == "DE"
    assert entity.test_type is not None
    assert entity.status is not None
    assert entity.specimen_type is not None


def test_lab_test_entity_with_optional_parameters():
    """Test that the LabTestEntity can be initialized with optional parameters."""
    entity = LabTestEntity(
        test_type="Blood Test",
        status="Completed",
        specimen_type="Blood"
    )
    assert entity.test_type == "Blood Test"
    assert entity.status == "Completed"
    assert entity.specimen_type == "Blood" 