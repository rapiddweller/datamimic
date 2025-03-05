# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import datetime
import hashlib
import random
import uuid
from typing import Any

from datamimic_ce.entities.entity import Entity
from datamimic_ce.entities.entity_util import EntityUtil


class UserAccountEntity(Entity):
    """Generate user account data.

    This class generates realistic user account data including user IDs,
    usernames, emails, password hashes, registration dates, login timestamps,
    account statuses, roles, and preferences.
    """

    # Account statuses
    ACCOUNT_STATUSES = [
        "ACTIVE",
        "INACTIVE",
        "SUSPENDED",
        "PENDING",
        "LOCKED",
        "DELETED",
        "BANNED",
        "UNVERIFIED",
    ]

    # User roles
    USER_ROLES = [
        "USER",
        "ADMIN",
        "MODERATOR",
        "EDITOR",
        "VIEWER",
        "MANAGER",
        "DEVELOPER",
        "TESTER",
        "ANALYST",
        "GUEST",
    ]

    # Preference themes
    THEMES = ["LIGHT", "DARK", "SYSTEM", "HIGH_CONTRAST", "CUSTOM"]

    # Notification preferences
    NOTIFICATION_PREFERENCES = ["ALL", "IMPORTANT", "NONE", "CUSTOM"]

    def __init__(
        self,
        class_factory_util,
        locale: str = "en",
        dataset: str | None = None,
    ):
        """Initialize the UserAccountEntity.

        Args:
            class_factory_util: The class factory utility.
            locale: The locale to use for generating data.
            dataset: The dataset to use for generating data.
        """
        super().__init__(locale, dataset)
        self._class_factory_util = class_factory_util
        self._data_generation_util = class_factory_util.get_data_generation_util()

        # Initialize field generators
        self._field_generators = EntityUtil.create_field_generator_dict(
            {
                "user_id": self._generate_user_id,
                "username": self._generate_username,
                "email": self._generate_email,
                "password_hash": self._generate_password_hash,
                "registration_date": self._generate_registration_date,
                "last_login": self._generate_last_login,
                "account_status": self._generate_account_status,
                "role": self._generate_role,
                "preferences": self._generate_preferences,
            }
        )

    def _generate_user_id(self) -> str:
        """Generate a unique user ID."""
        return f"user_{uuid.uuid4().hex[:12]}"

    def _generate_username(self) -> str:
        """Generate a username."""
        adjectives = ["happy", "clever", "brave", "swift", "calm", "bright", "bold", "wise"]
        nouns = ["tiger", "eagle", "wolf", "fox", "panda", "lion", "hawk", "bear"]
        numbers = random.randint(1, 9999)

        return f"{random.choice(adjectives)}_{random.choice(nouns)}_{numbers}"

    def _generate_email(self) -> str:
        """Generate an email address."""
        domains = ["example.com", "test.org", "mail.net", "domain.io", "service.co"]
        username = self.username.lower().replace("_", ".")
        return f"{username}@{random.choice(domains)}"

    def _generate_password_hash(self) -> str:
        """Generate a password hash."""
        # Generate a random password
        chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+"
        password = "".join(random.choice(chars) for _ in range(12))

        # Hash the password
        return hashlib.sha256(password.encode()).hexdigest()

    def _generate_registration_date(self) -> str:
        """Generate a registration date."""
        # Generate a date between 5 years ago and today
        days_ago = random.randint(0, 5 * 365)
        registration_date = datetime.datetime.now() - datetime.timedelta(days=days_ago)
        return registration_date.strftime("%Y-%m-%d")

    def _generate_last_login(self) -> str:
        """Generate a last login timestamp."""
        # Generate a timestamp between registration date and now
        registration_date = datetime.datetime.strptime(self.registration_date, "%Y-%m-%d")
        now = datetime.datetime.now()

        # If registration date is today, last login is now
        if registration_date.date() == now.date():
            return now.strftime("%Y-%m-%d %H:%M:%S")

        # Otherwise, generate a random timestamp between registration and now
        seconds_diff = int((now - registration_date).total_seconds())
        random_seconds = random.randint(0, seconds_diff)
        last_login = registration_date + datetime.timedelta(seconds=random_seconds)

        return last_login.strftime("%Y-%m-%d %H:%M:%S")

    def _generate_account_status(self) -> str:
        """Generate an account status."""
        # 80% chance of being active
        if random.random() < 0.8:
            return "ACTIVE"
        return random.choice(self.ACCOUNT_STATUSES)

    def _generate_role(self) -> str:
        """Generate a user role."""
        # 70% chance of being a regular user
        if random.random() < 0.7:
            return "USER"
        return random.choice(self.USER_ROLES)

    def _generate_preferences(self) -> dict:
        """Generate user preferences."""
        return {
            "theme": random.choice(self.THEMES),
            "notifications": random.choice(self.NOTIFICATION_PREFERENCES),
            "language": self._locale.upper() if self._locale else "EN",
            "timezone": random.choice(["UTC", "GMT", "EST", "PST", "CET", "JST"]),
            "two_factor_auth": random.choice([True, False]),
            "marketing_emails": random.choice([True, False]),
        }

    def reset(self) -> None:
        """Reset all field generators."""
        for generator in self._field_generators.values():
            generator.reset()

    @property
    def user_id(self) -> str:
        """Get the user ID."""
        value = self._field_generators["user_id"].get()
        assert value is not None, "user_id should not be None"
        return value

    @property
    def username(self) -> str:
        """Get the username."""
        value = self._field_generators["username"].get()
        assert value is not None, "username should not be None"
        return value

    @property
    def email(self) -> str:
        """Get the email address."""
        value = self._field_generators["email"].get()
        assert value is not None, "email should not be None"
        return value

    @property
    def password_hash(self) -> str:
        """Get the password hash."""
        value = self._field_generators["password_hash"].get()
        assert value is not None, "password_hash should not be None"
        return value

    @property
    def registration_date(self) -> str:
        """Get the registration date."""
        value = self._field_generators["registration_date"].get()
        assert value is not None, "registration_date should not be None"
        return value

    @property
    def last_login(self) -> str:
        """Get the last login timestamp."""
        value = self._field_generators["last_login"].get()
        assert value is not None, "last_login should not be None"
        return value

    @property
    def account_status(self) -> str:
        """Get the account status."""
        value = self._field_generators["account_status"].get()
        assert value is not None, "account_status should not be None"
        return value

    @property
    def role(self) -> str:
        """Get the user role."""
        value = self._field_generators["role"].get()
        assert value is not None, "role should not be None"
        return value

    @property
    def preferences(self) -> dict[str, Any]:
        """Get the user preferences."""
        value = self._field_generators["preferences"].get()
        assert value is not None, "preferences should not be None"
        return value

    def to_dict(self) -> dict[str, Any]:
        """Convert the entity to a dictionary.

        Returns:
            A dictionary containing all entity properties.
        """
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "password_hash": self.password_hash,
            "registration_date": self.registration_date,
            "last_login": self.last_login,
            "account_status": self.account_status,
            "role": self.role,
            "preferences": self.preferences,
        }

    def generate_batch(self, count: int = 100) -> list[dict[str, Any]]:
        """Generate a batch of user account data.

        Args:
            count: The number of records to generate.

        Returns:
            A list of dictionaries containing generated user account data.
        """
        field_names = [
            "user_id",
            "username",
            "email",
            "password_hash",
            "registration_date",
            "last_login",
            "account_status",
            "role",
            "preferences",
        ]

        return EntityUtil.batch_generate_fields(self._field_generators, field_names, count)
