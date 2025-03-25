import random
from pathlib import Path

from datamimic_ce.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.common.generators.address_generator import AddressGenerator
from datamimic_ce.domains.ecommerce.generators.product_generator import ProductGenerator
from datamimic_ce.utils.file_util import FileUtil


class OrderGenerator(BaseDomainGenerator):
    def __init__(self, dataset: str = "US"):
        self._dataset = dataset
        self._product_generator = ProductGenerator(dataset=dataset)
        self._address_generator = AddressGenerator(dataset=dataset)

    @property
    def dataset(self) -> str:
        return self._dataset

    @property
    def product_generator(self) -> ProductGenerator:
        return self._product_generator

    @property
    def address_generator(self) -> AddressGenerator:
        return self._address_generator

    def get_order_status(self) -> str:
        file_path = (
            Path(__file__).parent.parent.parent.parent / "domain_data/ecommerce" / f"order_statuses_{self._dataset}.csv"
        )
        header_dict, loaded_data = FileUtil.read_csv_to_dict_of_tuples_with_header(file_path, ",")

        wgt_idx = header_dict["weight"]
        status_idx = header_dict["status"]
        return random.choices(loaded_data, weights=[float(row[wgt_idx]) for row in loaded_data])[0][status_idx]

    def get_payment_method(self) -> str:
        file_path = (
            Path(__file__).parent.parent.parent.parent
            / "domain_data/ecommerce"
            / f"payment_methods_{self._dataset}.csv"
        )
        header_dict, loaded_data = FileUtil.read_csv_to_dict_of_tuples_with_header(file_path, ",")

        wgt_idx = header_dict["weight"]
        method_idx = header_dict["method"]
        return random.choices(loaded_data, weights=[float(row[wgt_idx]) for row in loaded_data])[0][method_idx]

    def get_shipping_method(self) -> str:
        file_path = (
            Path(__file__).parent.parent.parent.parent
            / "domain_data/ecommerce"
            / f"shipping_methods_{self._dataset}.csv"
        )
        header_dict, loaded_data = FileUtil.read_csv_to_dict_of_tuples_with_header(file_path, ",")

        wgt_idx = header_dict["weight"]
        method_idx = header_dict["method"]
        return random.choices(loaded_data, weights=[float(row[wgt_idx]) for row in loaded_data])[0][method_idx]

    def get_currency_code(self) -> str:
        file_path = (
            Path(__file__).parent.parent.parent.parent / "domain_data/ecommerce" / f"currencies_{self._dataset}.csv"
        )
        header_dict, loaded_data = FileUtil.read_csv_to_dict_of_tuples_with_header(file_path, ",")

        wgt_idx = header_dict["weight"]
        code_idx = header_dict["code"]
        return random.choices(loaded_data, weights=[float(row[wgt_idx]) for row in loaded_data])[0][code_idx]

    def get_shipping_amount(self, shipping_method: str) -> float:
        file_path = (
            Path(__file__).parent.parent.parent.parent
            / "domain_data/ecommerce"
            / f"shipping_methods_{self._dataset}.csv"
        )
        header_dict, datas = FileUtil.read_csv_to_dict_of_tuples_with_header(file_path, ",")
        method_idx = header_dict["method"]
        min_cost_idx = header_dict["min_cost"]
        max_cost_idx = header_dict["max_cost"]
        min_cost = 0.0
        max_cost = 0.0

        for data in datas:
            if data[method_idx] == shipping_method:
                min_cost = data[min_cost_idx]
                max_cost = data[max_cost_idx]

        try:
            min_cost = float(min_cost)
            max_cost = float(max_cost)
        except ValueError as e:
            raise ValueError("Shipping methods have error at cost data, please inform help-center") from e
        return round(random.uniform(min_cost, max_cost), 2)
