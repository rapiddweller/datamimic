# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com

import datetime
import random
import uuid
from typing import Any

from datamimic_ce.entities.entity import Entity
from datamimic_ce.entities.entity_util import EntityUtil


class CRMEntity(Entity):
    """Generate customer relationship management (CRM) data.

    This class generates realistic CRM data including customer IDs,
    contact information, interaction history, customer segments, and preferences.
    """

    # Customer segments
    CUSTOMER_SEGMENTS = [
        "NEW",
        "ACTIVE",
        "LOYAL",
        "AT_RISK",
        "DORMANT",
        "CHURNED",
        "HIGH_VALUE",
        "MID_VALUE",
        "LOW_VALUE",
        "VIP",
    ]

    # Interaction types
    INTERACTION_TYPES = [
        "EMAIL",
        "CALL",
        "MEETING",
        "SUPPORT_TICKET",
        "PURCHASE",
        "COMPLAINT",
        "FEEDBACK",
        "SOCIAL_MEDIA",
        "WEBSITE_VISIT",
        "EVENT",
    ]

    # Communication channels
    COMMUNICATION_CHANNELS = [
        "EMAIL",
        "PHONE",
        "SMS",
        "MAIL",
        "SOCIAL_MEDIA",
        "IN_APP",
        "PUSH_NOTIFICATION",
        "NONE",
    ]

    # Communication frequencies
    COMMUNICATION_FREQUENCIES = [
        "DAILY",
        "WEEKLY",
        "BIWEEKLY",
        "MONTHLY",
        "QUARTERLY",
        "ANNUALLY",
        "NEVER",
    ]

    # Customer interests
    CUSTOMER_INTERESTS = [
        "TECHNOLOGY",
        "FASHION",
        "SPORTS",
        "HEALTH",
        "FINANCE",
        "TRAVEL",
        "FOOD",
        "ENTERTAINMENT",
        "EDUCATION",
        "HOME",
    ]

    def __init__(
        self,
        class_factory_util,
        locale: str = "en",
        dataset: str | None = None,
    ):
        """Initialize the CRMEntity.

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
                "customer_id": self._generate_customer_id,
                "first_name": self._generate_first_name,
                "last_name": self._generate_last_name,
                "email": self._generate_email,
                "phone": self._generate_phone,
                "address": self._generate_address,
                "customer_since": self._generate_customer_since,
                "segment": self._generate_segment,
                "lifetime_value": self._generate_lifetime_value,
                "interaction_history": self._generate_interaction_history,
                "preferences": self._generate_preferences,
            }
        )

    def _generate_customer_id(self) -> str:
        """Generate a unique customer ID."""
        return f"cust_{uuid.uuid4().hex[:12]}"

    def _generate_first_name(self) -> str:
        """Generate a first name."""
        # Simple list of first names for demonstration
        first_names = [
            "James",
            "Mary",
            "John",
            "Patricia",
            "Robert",
            "Jennifer",
            "Michael",
            "Linda",
            "William",
            "Elizabeth",
            "David",
            "Barbara",
            "Richard",
            "Susan",
            "Joseph",
            "Jessica",
            "Thomas",
            "Sarah",
            "Charles",
            "Karen",
            "Christopher",
            "Nancy",
            "Daniel",
            "Lisa",
            "Matthew",
            "Margaret",
            "Anthony",
            "Betty",
            "Mark",
            "Sandra",
            "Donald",
            "Ashley",
            "Steven",
            "Kimberly",
            "Paul",
            "Emily",
            "Andrew",
            "Donna",
            "Joshua",
            "Michelle",
            "Kenneth",
            "Dorothy",
            "Kevin",
            "Carol",
            "Brian",
            "Amanda",
            "George",
            "Melissa",
            "Edward",
            "Deborah",
            "Ronald",
            "Stephanie",
            "Timothy",
            "Rebecca",
            "Jason",
            "Sharon",
            "Jeffrey",
            "Laura",
            "Ryan",
            "Cynthia",
            "Jacob",
            "Kathleen",
            "Gary",
            "Amy",
            "Nicholas",
            "Shirley",
            "Eric",
            "Angela",
            "Jonathan",
            "Helen",
            "Stephen",
            "Anna",
            "Larry",
            "Brenda",
            "Justin",
            "Pamela",
            "Scott",
            "Nicole",
            "Brandon",
            "Emma",
            "Benjamin",
            "Samantha",
            "Samuel",
            "Katherine",
            "Gregory",
            "Christine",
            "Frank",
            "Debra",
            "Alexander",
            "Rachel",
            "Raymond",
            "Catherine",
            "Patrick",
            "Carolyn",
            "Jack",
            "Janet",
            "Dennis",
            "Ruth",
            "Jerry",
            "Maria",
            "Tyler",
            "Heather",
            "Aaron",
            "Diane",
            "Jose",
            "Virginia",
            "Adam",
            "Julie",
            "Nathan",
            "Joyce",
            "Henry",
            "Victoria",
            "Douglas",
            "Olivia",
            "Zachary",
            "Kelly",
            "Peter",
            "Christina",
            "Kyle",
            "Lauren",
            "Walter",
            "Joan",
            "Ethan",
            "Evelyn",
            "Jeremy",
            "Judith",
            "Harold",
            "Megan",
            "Keith",
            "Cheryl",
            "Christian",
            "Andrea",
            "Roger",
            "Hannah",
            "Noah",
            "Martha",
        ]
        return random.choice(first_names)

    def _generate_last_name(self) -> str:
        """Generate a last name."""
        # Simple list of last names for demonstration
        last_names = [
            "Smith",
            "Johnson",
            "Williams",
            "Brown",
            "Jones",
            "Garcia",
            "Miller",
            "Davis",
            "Rodriguez",
            "Martinez",
            "Hernandez",
            "Lopez",
            "Gonzalez",
            "Wilson",
            "Anderson",
            "Thomas",
            "Taylor",
            "Moore",
            "Jackson",
            "Martin",
            "Lee",
            "Perez",
            "Thompson",
            "White",
            "Harris",
            "Sanchez",
            "Clark",
            "Ramirez",
            "Lewis",
            "Robinson",
            "Walker",
            "Young",
            "Allen",
            "King",
            "Wright",
            "Scott",
            "Torres",
            "Nguyen",
            "Hill",
            "Flores",
            "Green",
            "Adams",
            "Nelson",
            "Baker",
            "Hall",
            "Rivera",
            "Campbell",
            "Mitchell",
            "Carter",
            "Roberts",
            "Gomez",
            "Phillips",
            "Evans",
            "Turner",
            "Diaz",
            "Parker",
            "Cruz",
            "Edwards",
            "Collins",
            "Reyes",
            "Stewart",
            "Morris",
            "Morales",
            "Murphy",
            "Cook",
            "Rogers",
            "Gutierrez",
            "Ortiz",
            "Morgan",
            "Cooper",
            "Peterson",
            "Bailey",
            "Reed",
            "Kelly",
            "Howard",
            "Ramos",
            "Kim",
            "Cox",
            "Ward",
            "Richardson",
            "Watson",
            "Brooks",
            "Chavez",
            "Wood",
            "James",
            "Bennett",
            "Gray",
            "Mendoza",
            "Ruiz",
            "Hughes",
            "Price",
            "Alvarez",
            "Castillo",
            "Sanders",
            "Patel",
            "Myers",
            "Long",
            "Ross",
            "Foster",
            "Jimenez",
            "Powell",
            "Jenkins",
            "Perry",
            "Russell",
            "Sullivan",
            "Bell",
            "Coleman",
            "Butler",
            "Henderson",
            "Barnes",
            "Gonzales",
            "Fisher",
            "Vasquez",
            "Simmons",
            "Romero",
            "Jordan",
            "Patterson",
            "Alexander",
            "Hamilton",
            "Graham",
            "Reynolds",
            "Griffin",
            "Wallace",
            "Moreno",
            "West",
            "Cole",
            "Hayes",
            "Bryant",
            "Herrera",
            "Gibson",
            "Ellis",
            "Tran",
            "Medina",
            "Aguilar",
            "Stevens",
            "Murray",
            "Ford",
            "Castro",
            "Marshall",
            "Owens",
            "Harrison",
            "Fernandez",
            "Mcdonald",
            "Woods",
            "Washington",
            "Kennedy",
            "Wells",
            "Chen",
            "Hoffman",
            "Meyer",
            "Saunders",
            "Guzman",
            "Payne",
            "Maldonado",
            "Keller",
            "Sanford",
            "Guerrero",
            "Stanley",
            "Bates",
            "Alvarado",
        ]
        return random.choice(last_names)

    def _generate_email(self) -> str:
        """Generate an email address."""
        domains = ["example.com", "test.org", "mail.net", "domain.io", "service.co"]
        first_name = self.first_name.lower()
        last_name = self.last_name.lower()
        return f"{first_name}.{last_name}@{random.choice(domains)}"

    def _generate_phone(self) -> str:
        """Generate a phone number."""
        # Generate a random phone number in the format (XXX) XXX-XXXX
        area_code = random.randint(100, 999)
        prefix = random.randint(100, 999)
        line = random.randint(1000, 9999)
        return f"({area_code}) {prefix}-{line}"

    def _generate_address(self) -> dict:
        """Generate an address."""
        # Simple list of street names, cities, states, and countries for demonstration
        street_names = [
            "Main",
            "Oak",
            "Pine",
            "Maple",
            "Cedar",
            "Elm",
            "Washington",
            "Park",
            "Lake",
            "Hill",
            "River",
            "View",
            "Church",
            "High",
            "Mill",
            "Forest",
        ]
        street_types = ["St", "Ave", "Blvd", "Dr", "Ln", "Rd", "Way", "Pl", "Ct"]
        cities = [
            "Springfield",
            "Franklin",
            "Greenville",
            "Bristol",
            "Clinton",
            "Kingston",
            "Marion",
            "Salem",
            "Georgetown",
            "Oxford",
            "Madison",
            "Arlington",
            "Fairview",
        ]
        states = [
            "AL",
            "AK",
            "AZ",
            "AR",
            "CA",
            "CO",
            "CT",
            "DE",
            "FL",
            "GA",
            "HI",
            "ID",
            "IL",
            "IN",
            "IA",
            "KS",
            "KY",
            "LA",
            "ME",
            "MD",
            "MA",
            "MI",
            "MN",
            "MS",
            "MO",
            "MT",
            "NE",
            "NV",
            "NH",
            "NJ",
            "NM",
            "NY",
            "NC",
            "ND",
            "OH",
            "OK",
            "OR",
            "PA",
            "RI",
            "SC",
            "SD",
            "TN",
            "TX",
            "UT",
            "VT",
            "VA",
            "WA",
            "WV",
            "WI",
            "WY",
        ]
        countries = ["United States", "Canada", "United Kingdom", "Australia", "Germany", "France"]

        # Generate a random address
        street_number = random.randint(1, 9999)
        street_name = random.choice(street_names)
        street_type = random.choice(street_types)
        city = random.choice(cities)
        state = random.choice(states)
        zip_code = f"{random.randint(10000, 99999)}"
        country = random.choice(countries)

        return {
            "street": f"{street_number} {street_name} {street_type}",
            "city": city,
            "state": state,
            "zip_code": zip_code,
            "country": country,
        }

    def _generate_customer_since(self) -> str:
        """Generate a customer since date."""
        # Generate a date between 10 years ago and today
        days_ago = random.randint(0, 10 * 365)
        customer_since = datetime.datetime.now() - datetime.timedelta(days=days_ago)
        return customer_since.strftime("%Y-%m-%d")

    def _generate_segment(self) -> str:
        """Generate a customer segment."""
        # Weighted distribution of segments
        weights = {
            "NEW": 0.1,
            "ACTIVE": 0.3,
            "LOYAL": 0.2,
            "AT_RISK": 0.1,
            "DORMANT": 0.1,
            "CHURNED": 0.05,
            "HIGH_VALUE": 0.05,
            "MID_VALUE": 0.05,
            "LOW_VALUE": 0.03,
            "VIP": 0.02,
        }

        # Generate a random segment based on weights
        segments = list(weights.keys())
        weights_list = list(weights.values())
        return random.choices(segments, weights=weights_list, k=1)[0]

    def _generate_lifetime_value(self) -> float:
        """Generate a customer lifetime value."""
        # Generate a random lifetime value between 0 and 10000
        # with higher probability for lower values
        base_value = random.expovariate(0.0005)  # Exponential distribution
        return min(round(base_value, 2), 10000.0)  # Cap at 10000

    def _generate_interaction_history(self) -> list:
        """Generate a customer interaction history."""
        # Generate a random number of interactions (0-10)
        num_interactions = random.randint(0, 10)

        # Generate a list of interactions
        interactions = []
        customer_since = datetime.datetime.strptime(self.customer_since, "%Y-%m-%d")
        now = datetime.datetime.now()

        for _ in range(num_interactions):
            # Generate a random date between customer_since and now
            seconds_diff = int((now - customer_since).total_seconds())
            if seconds_diff <= 0:
                # If customer_since is today, use now as the interaction date
                interaction_date = now
            else:
                random_seconds = random.randint(0, seconds_diff)
                interaction_date = customer_since + datetime.timedelta(seconds=random_seconds)

            # Generate a random interaction type
            interaction_type = random.choice(self.INTERACTION_TYPES)

            # Generate random notes
            notes_templates = [
                "Customer inquired about {product}.",
                "Customer requested information on {service}.",
                "Customer complained about {issue}.",
                "Customer provided feedback on {topic}.",
                "Customer purchased {product}.",
                "Customer attended {event}.",
                "Customer requested support for {problem}.",
                "Customer upgraded their plan to {plan}.",
                "Customer downgraded their plan from {plan}.",
                "Customer canceled their subscription.",
            ]

            placeholders = {
                "{product}": ["Product A", "Product B", "Product C", "Product D"],
                "{service}": ["Service X", "Service Y", "Service Z"],
                "{issue}": ["billing", "delivery", "quality", "customer service"],
                "{topic}": ["user experience", "product quality", "customer service", "pricing"],
                "{problem}": ["login issues", "technical problems", "billing questions", "usage concerns"],
                "{plan}": ["Basic", "Premium", "Pro", "Enterprise"],
                "{event}": ["webinar", "conference", "workshop", "product launch"],
            }

            notes_template = random.choice(notes_templates)
            notes = notes_template

            # Replace placeholders with random values
            for placeholder, values in placeholders.items():
                if placeholder in notes:
                    notes = notes.replace(placeholder, random.choice(values))

            # Add the interaction to the list
            interactions.append(
                {
                    "date": interaction_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "type": interaction_type,
                    "notes": notes,
                }
            )

        # Sort interactions by date (newest first)
        interactions.sort(key=lambda x: x["date"], reverse=True)

        return interactions

    def _generate_preferences(self) -> dict:
        """Generate customer preferences."""
        # Generate random preferences
        communication_channel = random.choice(self.COMMUNICATION_CHANNELS)
        frequency = random.choice(self.COMMUNICATION_FREQUENCIES)

        # Generate 1-3 random interests
        num_interests = random.randint(1, 3)
        interests = random.sample(self.CUSTOMER_INTERESTS, num_interests)

        return {
            "communication_channel": communication_channel,
            "frequency": frequency,
            "interests": interests,
            "opt_in_marketing": random.choice([True, False]),
            "opt_in_surveys": random.choice([True, False]),
            "language": self._locale.upper() if self._locale else "EN",
        }

    def reset(self) -> None:
        """Reset all field generators."""
        for generator in self._field_generators.values():
            generator.reset()

    @property
    def customer_id(self) -> str:
        """Get the customer ID."""
        value = self._field_generators["customer_id"].get()
        assert value is not None, "customer_id should not be None"
        return value

    @property
    def first_name(self) -> str:
        """Get the customer's first name."""
        value = self._field_generators["first_name"].get()
        assert value is not None, "first_name should not be None"
        return value

    @property
    def last_name(self) -> str:
        """Get the customer's last name."""
        value = self._field_generators["last_name"].get()
        assert value is not None, "last_name should not be None"
        return value

    @property
    def email(self) -> str:
        """Get the customer's email address."""
        value = self._field_generators["email"].get()
        assert value is not None, "email should not be None"
        return value

    @property
    def phone(self) -> str:
        """Get the customer's phone number."""
        value = self._field_generators["phone"].get()
        assert value is not None, "phone should not be None"
        return value

    @property
    def address(self) -> dict[str, str]:
        """Get the customer's address."""
        value = self._field_generators["address"].get()
        assert value is not None, "address should not be None"
        return value

    @property
    def customer_since(self) -> str:
        """Get the customer's start date."""
        value = self._field_generators["customer_since"].get()
        assert value is not None, "customer_since should not be None"
        return value

    @property
    def segment(self) -> str:
        """Get the customer segment."""
        value = self._field_generators["segment"].get()
        assert value is not None, "segment should not be None"
        return value

    @property
    def lifetime_value(self) -> float:
        """Get the customer lifetime value."""
        value = self._field_generators["lifetime_value"].get()
        assert value is not None, "lifetime_value should not be None"
        return value

    @property
    def interaction_history(self) -> list[dict[str, Any]]:
        """Get the customer interaction history."""
        value = self._field_generators["interaction_history"].get()
        assert value is not None, "interaction_history should not be None"
        return value

    @property
    def preferences(self) -> dict[str, Any]:
        """Get the customer preferences."""
        value = self._field_generators["preferences"].get()
        assert value is not None, "preferences should not be None"
        return value

    def to_dict(self) -> dict[str, Any]:
        """Convert the entity to a dictionary.

        Returns:
            A dictionary containing all entity properties.
        """
        return {
            "customer_id": self.customer_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "customer_since": self.customer_since,
            "segment": self.segment,
            "lifetime_value": self.lifetime_value,
            "interaction_history": self.interaction_history,
            "preferences": self.preferences,
        }

    def generate_batch(self, count: int = 100) -> list[dict[str, Any]]:
        """Generate a batch of CRM data.

        Args:
            count: The number of records to generate.

        Returns:
            A list of dictionaries containing generated CRM data.
        """
        field_names = [
            "customer_id",
            "first_name",
            "last_name",
            "email",
            "phone",
            "address",
            "customer_since",
            "segment",
            "lifetime_value",
            "interaction_history",
            "preferences",
        ]

        return EntityUtil.batch_generate_fields(self._field_generators, field_names, count)
