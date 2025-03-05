# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import unittest

from datamimic_ce.entities.crm_entity import CRMEntity
from datamimic_ce.utils.class_factory_ce_util import ClassFactoryCEUtil


class TestCRMEntity(unittest.TestCase):
    """Test cases for the CRMEntity class."""

    def setUp(self):
        """Set up test fixtures."""
        self.class_factory_util = ClassFactoryCEUtil()
        self.crm_entity = CRMEntity(self.class_factory_util)

    def test_init(self):
        """Test initialization of CRMEntity."""
        self.assertEqual(self.crm_entity._locale, "en")
        self.assertIsNone(self.crm_entity._dataset)

    def test_init_with_params(self):
        """Test initialization with custom parameters."""
        crm_entity = CRMEntity(
            self.class_factory_util,
            locale="de",
            dataset="test_dataset"
        )
        self.assertEqual(crm_entity._locale, "de")
        self.assertEqual(crm_entity._dataset, "test_dataset")

    def test_customer_id_generation(self):
        """Test customer_id generation."""
        customer_id = self.crm_entity.customer_id
        self.assertIsInstance(customer_id, str)
        self.assertTrue(len(customer_id) > 0)

    def test_first_name_generation(self):
        """Test first_name generation."""
        first_name = self.crm_entity.first_name
        self.assertIsInstance(first_name, str)
        self.assertTrue(len(first_name) > 0)

    def test_last_name_generation(self):
        """Test last_name generation."""
        last_name = self.crm_entity.last_name
        self.assertIsInstance(last_name, str)
        self.assertTrue(len(last_name) > 0)

    def test_email_generation(self):
        """Test email generation."""
        email = self.crm_entity.email
        self.assertIsInstance(email, str)
        self.assertIn("@", email)
        self.assertIn(".", email)

    def test_phone_generation(self):
        """Test phone generation."""
        phone = self.crm_entity.phone
        self.assertIsInstance(phone, str)
        self.assertTrue(len(phone) > 0)

    def test_address_generation(self):
        """Test address generation."""
        address = self.crm_entity.address
        self.assertIsInstance(address, dict)
        self.assertIn("street", address)
        self.assertIn("city", address)
        self.assertIn("state", address)
        self.assertIn("zip_code", address)
        self.assertIn("country", address)

    def test_customer_since_generation(self):
        """Test customer_since generation."""
        customer_since = self.crm_entity.customer_since
        self.assertIsInstance(customer_since, str)
        # Check if it's a valid date string (YYYY-MM-DD)
        self.assertRegex(customer_since, r"\d{4}-\d{2}-\d{2}")

    def test_segment_generation(self):
        """Test segment generation."""
        segment = self.crm_entity.segment
        self.assertIsInstance(segment, str)
        self.assertIn(segment, CRMEntity.CUSTOMER_SEGMENTS)

    def test_lifetime_value_generation(self):
        """Test lifetime_value generation."""
        lifetime_value = self.crm_entity.lifetime_value
        self.assertIsInstance(lifetime_value, float)
        self.assertGreaterEqual(lifetime_value, 0.0)

    def test_interaction_history_generation(self):
        """Test interaction_history generation."""
        interaction_history = self.crm_entity.interaction_history
        self.assertIsInstance(interaction_history, list)
        if interaction_history:  # If not empty
            for interaction in interaction_history:
                self.assertIsInstance(interaction, dict)
                self.assertIn("date", interaction)
                self.assertIn("type", interaction)
                self.assertIn("notes", interaction)

    def test_preferences_generation(self):
        """Test preferences generation."""
        preferences = self.crm_entity.preferences
        self.assertIsInstance(preferences, dict)
        self.assertIn("communication_channel", preferences)
        self.assertIn("frequency", preferences)
        self.assertIn("interests", preferences)

    def test_to_dict(self):
        """Test to_dict method."""
        crm_dict = self.crm_entity.to_dict()
        self.assertIsInstance(crm_dict, dict)
        self.assertIn("customer_id", crm_dict)
        self.assertIn("first_name", crm_dict)
        self.assertIn("last_name", crm_dict)
        self.assertIn("email", crm_dict)
        self.assertIn("phone", crm_dict)
        self.assertIn("address", crm_dict)
        self.assertIn("customer_since", crm_dict)
        self.assertIn("segment", crm_dict)
        self.assertIn("lifetime_value", crm_dict)
        self.assertIn("interaction_history", crm_dict)
        self.assertIn("preferences", crm_dict)

    def test_generate_batch(self):
        """Test generate_batch method."""
        batch_size = 5
        batch = self.crm_entity.generate_batch(batch_size)
        self.assertIsInstance(batch, list)
        self.assertEqual(len(batch), batch_size)
        for item in batch:
            self.assertIsInstance(item, dict)
            self.assertIn("customer_id", item)
            self.assertIn("first_name", item)
            self.assertIn("last_name", item)
            self.assertIn("email", item)
            self.assertIn("phone", item)
            self.assertIn("address", item)
            self.assertIn("customer_since", item)
            self.assertIn("segment", item)
            self.assertIn("lifetime_value", item)
            self.assertIn("interaction_history", item)
            self.assertIn("preferences", item)

    def test_reset(self):
        """Test reset method."""
        # Get initial values
        initial_customer_id = self.crm_entity.customer_id
        initial_first_name = self.crm_entity.first_name
        
        # Reset the entity
        self.crm_entity.reset()
        
        # Get new values
        new_customer_id = self.crm_entity.customer_id
        new_first_name = self.crm_entity.first_name
        
        # Values should be different after reset
        self.assertNotEqual(initial_customer_id, new_customer_id)
        self.assertNotEqual(initial_first_name, new_first_name) 