import random
import string
import uuid

from faker import Faker

from datamimic_ce.domain_core.base_literal_generator import BaseLiteralGenerator


class GlobRandomHexColorGenerator(BaseLiteralGenerator):
    def generate(self) -> str:
        return f"#{random.randint(0, 0xFFFFFF):06x}"


class GlobRandomIPAddressGenerator(BaseLiteralGenerator):
    def generate(self) -> str:
        return ".".join(map(str, (random.randint(0, 255) for _ in range(4))))


class GlobRandomUUIDGenerator(BaseLiteralGenerator):
    def generate(self) -> str:
        return str(uuid.uuid4())


class GlobRandomMACAddressGenerator(BaseLiteralGenerator):
    def generate(self) -> str:
        return ":".join([f"{random.randint(0, 255):02x}" for _ in range(6)])


class GlobRandomISBNGenerator(BaseLiteralGenerator):
    def generate(self) -> str:
        prefix = "978"
        group = random.randint(0, 1)
        publisher = random.randint(100, 999)
        title = random.randint(100000, 999999)
        isbn = f"{prefix}-{group}-{publisher}-{title}"
        check_digit = sum(int(x) if i % 2 == 0 else int(x) * 3 for i, x in enumerate(isbn.replace("-", ""))) % 10
        check_digit = (10 - check_digit) % 10
        return f"{isbn}-{check_digit}"


class GlobRandomCoordinatesGenerator(BaseLiteralGenerator):
    def generate(self) -> str:
        latitude = random.uniform(-90, 90)
        longitude = random.uniform(-180, 180)
        return f"{latitude},{longitude}"


class GlobRandomLicensePlateGenerator(BaseLiteralGenerator):
    def generate(self) -> str:
        import string

        letters = "".join(random.choices(string.ascii_uppercase, k=3))
        numbers = "".join(random.choices(string.digits, k=4))
        return f"{letters}-{numbers}"


class GlobRandomPasswordGenerator(BaseLiteralGenerator):
    def __init__(self, length: int = 12):
        self.length = length

    def generate(self) -> str:
        characters = string.ascii_letters + string.digits + string.punctuation
        return "".join(random.choices(characters, k=self.length))


class GlobRandomMovieTitleGenerator(BaseLiteralGenerator):
    def __init__(self):
        self.fake = Faker()

    def generate(self) -> str:
        return self.fake.catch_phrase()


class GlobRandomUserAgentGenerator(BaseLiteralGenerator):
    def __init__(self):
        self.fake = Faker()

    def generate(self) -> str:
        return self.fake.user_agent()
