# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com



class RandomHexColorGenerator(Generator):
    def generate(self) -> str:
        import random
        return f"#{random.randint(0, 0xFFFFFF):06x}"


class RandomIPAddressGenerator(Generator):
    def generate(self) -> str:
        import random
        return ".".join(map(str, (random.randint(0, 255) for _ in range(4))))


class RandomUUIDGenerator(Generator):
    def generate(self) -> str:
        import uuid
        return str(uuid.uuid4())


class RandomMACAddressGenerator(Generator):
    def generate(self) -> str:
        import random
        return ":".join([f"{random.randint(0, 255):02x}" for _ in range(6)])


class RandomISBNGenerator(Generator):
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


class RandomCoordinatesGenerator(Generator):
    def generate(self) -> str:
        import random
        latitude = random.uniform(-90, 90)
        longitude = random.uniform(-180, 180)
        return f"{latitude},{longitude}"


class RandomLicensePlateGenerator(Generator):
    def generate(self) -> str:
        import random
        import string
        letters = "".join(random.choices(string.ascii_uppercase, k=3))
        numbers = "".join(random.choices(string.digits, k=4))
        return f"{letters}-{numbers}"


class RandomPasswordGenerator(Generator):
    def __init__(self, length: int = 12):
        self.length = length

    def generate(self) -> str:
        import random
        import string
        characters = string.ascii_letters + string.digits + string.punctuation
        return "".join(random.choices(characters, k=self.length))


class RandomMovieTitleGenerator(Generator):
    def __init__(self):
        from faker import Faker
        self.fake = Faker()

    def generate(self) -> str:
        return self.fake.catch_phrase()


class RandomUserAgentGenerator(Generator):
    def __init__(self):
        from faker import Faker
        self.fake = Faker()

    def generate(self) -> str:
        return self.fake.user_agent()
