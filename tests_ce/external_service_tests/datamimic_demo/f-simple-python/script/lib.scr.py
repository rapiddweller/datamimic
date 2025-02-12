# DATAMIMIC
# Copyright (c) 2023-2024 Rapiddweller Asia Co., Ltd.
# This software is licensed under the MIT License.
# See LICENSE file for the full text of the license.
# For questions and support, contact: info@rapiddweller.com


def multiply(number1, number2):
    return number1 * number2


def divide(number1, number2):
    return number1 / number2


def create_random_json():
    import json
    import random
    import string

    import numpy as np
    import pandas as pd

    # Generate a random DataFrame
    num_rows = random.randint(5, 10)
    num_columns = random.randint(3, 5)
    data = np.random.rand(num_rows, num_columns)
    columns = [
        "".join(random.choices(string.ascii_uppercase + string.ascii_lowercase, k=5)) for _ in range(num_columns)
    ]
    df = pd.DataFrame(data, columns=columns)

    # Convert the DataFrame to a JSON string
    json_str = df.to_json(orient="records")

    # Convert the JSON string to a Python dictionary
    data = json.loads(json_str)

    return data


class CustomStringGenerator(Generator):
    def __init__(self, prefix: str = ""):
        self.prefix = prefix
        self.counter = 0

    def generate(self) -> str:
        self.counter += 1
        return f"{self.prefix}{self.counter}"


class CustomConverter(Converter):
    def convert(self, value):
        return f"Converted: {value}"
