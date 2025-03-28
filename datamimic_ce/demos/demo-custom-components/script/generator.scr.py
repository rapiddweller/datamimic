from datamimic_ce.domain_core.base_literal_generator import BaseLiteralGenerator


class RandomHexColorGenerator(BaseLiteralGenerator):
    def generate(self) -> str:
        import random

        return f"#{random.randint(0, 0xFFFFFF):06x}"


class RandomIPAddressGenerator(BaseLiteralGenerator):
    def generate(self) -> str:
        import random

        return ".".join(map(str, (random.randint(0, 255) for _ in range(4))))


class RandomUUIDGenerator(BaseLiteralGenerator):
    def generate(self) -> str:
        import uuid

        return str(uuid.uuid4())


class RandomMACAddressGenerator(BaseLiteralGenerator):
    def generate(self) -> str:
        import random

        return ":".join([f"{random.randint(0, 255):02x}" for _ in range(6)])


class RandomISBNGenerator(BaseLiteralGenerator):
    def generate(self) -> str:
        import random

        prefix = "978"
        group = random.randint(0, 1)
        publisher = random.randint(100, 999)
        title = random.randint(100000, 999999)
        isbn = f"{prefix}-{group}-{publisher}-{title}"
        check_digit = sum(int(x) if i % 2 == 0 else int(x) * 3 for i, x in enumerate(isbn.replace("-", ""))) % 10
        check_digit = (10 - check_digit) % 10
        return f"{isbn}-{check_digit}"


class RandomCoordinatesGenerator(BaseLiteralGenerator):
    def generate(self) -> str:
        import random

        latitude = random.uniform(-90, 90)
        longitude = random.uniform(-180, 180)
        return f"{latitude},{longitude}"


class RandomLicensePlateGenerator(BaseLiteralGenerator):
    def generate(self) -> str:
        import random
        import string

        letters = "".join(random.choices(string.ascii_uppercase, k=3))
        numbers = "".join(random.choices(string.digits, k=4))
        return f"{letters}-{numbers}"


class RandomPasswordGenerator(BaseLiteralGenerator):
    def __init__(self, length: int = 12):
        self.length = length

    def generate(self) -> str:
        import random
        import string

        characters = string.ascii_letters + string.digits + string.punctuation
        return "".join(random.choices(characters, k=self.length))


class RandomMovieTitleGenerator(BaseLiteralGenerator):
    def __init__(self):
        from faker import Faker

        self.fake = Faker()

    def generate(self) -> str:
        return self.fake.catch_phrase()


class RandomUserAgentGenerator(BaseLiteralGenerator):
    def __init__(self):
        from faker import Faker

        self.fake = Faker()

    def generate(self) -> str:
        return self.fake.user_agent()


class RandomNameGenerator(BaseLiteralGenerator):
    def __init__(self):
        from faker import Faker

        self.fake = Faker()

    def generate(self) -> str:
        return self.fake.name()


class RandomEmailGenerator(BaseLiteralGenerator):
    def __init__(self):
        from faker import Faker

        self.fake = Faker()

    def generate(self) -> str:
        return self.fake.email()


class RandomFloatGenerator(BaseLiteralGenerator):
    def __init__(self, min: float, max: float):
        self.min = min
        self.max = max

    def generate(self) -> float:
        import random

        return random.uniform(self.min, self.max)


class RandomTransactionTypeGenerator(BaseLiteralGenerator):
    def generate(self) -> str:
        import random

        transaction_types = ["purchase", "refund", "transfer", "withdrawal"]
        return random.choice(transaction_types)
