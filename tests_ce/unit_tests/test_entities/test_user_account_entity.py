# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import unittest

from datamimic_ce.entities.user_account_entity import UserAccountEntity
from datamimic_ce.utils.class_factory_ce_util import ClassFactoryCEUtil


class TestUserAccountEntity(unittest.TestCase):
    """Test cases for the UserAccountEntity class."""

    def setUp(self):
        """Set up test fixtures."""
        self.class_factory_util = ClassFactoryCEUtil()
        self.user_account_entity = UserAccountEntity(self.class_factory_util)

    def test_init(self):
        """Test initialization of UserAccountEntity."""
        self.assertEqual(self.user_account_entity._locale, "en")
        self.assertIsNone(self.user_account_entity._dataset)

    def test_init_with_params(self):
        """Test initialization with custom parameters."""
        user_account_entity = UserAccountEntity(
            self.class_factory_util,
            locale="de",
            dataset="test_dataset"
        )
        self.assertEqual(user_account_entity._locale, "de")
        self.assertEqual(user_account_entity._dataset, "test_dataset")

    def test_user_id_generation(self):
        """Test user_id generation."""
        user_id = self.user_account_entity.user_id
        self.assertIsInstance(user_id, str)
        self.assertTrue(len(user_id) > 0)

    def test_username_generation(self):
        """Test username generation."""
        username = self.user_account_entity.username
        self.assertIsInstance(username, str)
        self.assertTrue(len(username) > 0)

    def test_email_generation(self):
        """Test email generation."""
        email = self.user_account_entity.email
        self.assertIsInstance(email, str)
        self.assertIn("@", email)
        self.assertIn(".", email)

    def test_password_hash_generation(self):
        """Test password_hash generation."""
        password_hash = self.user_account_entity.password_hash
        self.assertIsInstance(password_hash, str)
        self.assertTrue(len(password_hash) > 0)

    def test_registration_date_generation(self):
        """Test registration_date generation."""
        registration_date = self.user_account_entity.registration_date
        self.assertIsInstance(registration_date, str)
        # Check if it's a valid date string (YYYY-MM-DD)
        self.assertRegex(registration_date, r"\d{4}-\d{2}-\d{2}")

    def test_last_login_generation(self):
        """Test last_login generation."""
        last_login = self.user_account_entity.last_login
        self.assertIsInstance(last_login, str)
        # Check if it's a valid datetime string (YYYY-MM-DD HH:MM:SS)
        self.assertRegex(last_login, r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")

    def test_account_status_generation(self):
        """Test account_status generation."""
        account_status = self.user_account_entity.account_status
        self.assertIsInstance(account_status, str)
        self.assertIn(account_status, UserAccountEntity.ACCOUNT_STATUSES)

    def test_role_generation(self):
        """Test role generation."""
        role = self.user_account_entity.role
        self.assertIsInstance(role, str)
        self.assertIn(role, UserAccountEntity.USER_ROLES)

    def test_preferences_generation(self):
        """Test preferences generation."""
        preferences = self.user_account_entity.preferences
        self.assertIsInstance(preferences, dict)
        self.assertTrue(len(preferences) > 0)

    def test_to_dict(self):
        """Test to_dict method."""
        user_dict = self.user_account_entity.to_dict()
        self.assertIsInstance(user_dict, dict)
        self.assertIn("user_id", user_dict)
        self.assertIn("username", user_dict)
        self.assertIn("email", user_dict)
        self.assertIn("password_hash", user_dict)
        self.assertIn("registration_date", user_dict)
        self.assertIn("last_login", user_dict)
        self.assertIn("account_status", user_dict)
        self.assertIn("role", user_dict)
        self.assertIn("preferences", user_dict)

    def test_generate_batch(self):
        """Test generate_batch method."""
        batch_size = 5
        batch = self.user_account_entity.generate_batch(batch_size)
        self.assertIsInstance(batch, list)
        self.assertEqual(len(batch), batch_size)
        for item in batch:
            self.assertIsInstance(item, dict)
            self.assertIn("user_id", item)
            self.assertIn("username", item)
            self.assertIn("email", item)
            self.assertIn("password_hash", item)
            self.assertIn("registration_date", item)
            self.assertIn("last_login", item)
            self.assertIn("account_status", item)
            self.assertIn("role", item)
            self.assertIn("preferences", item)

    def test_reset(self):
        """Test reset method."""
        # Get initial values
        initial_user_id = self.user_account_entity.user_id
        initial_username = self.user_account_entity.username
        
        # Reset the entity
        self.user_account_entity.reset()
        
        # Get new values
        new_user_id = self.user_account_entity.user_id
        new_username = self.user_account_entity.username
        
        # Values should be different after reset
        self.assertNotEqual(initial_user_id, new_user_id)
        self.assertNotEqual(initial_username, new_username) 