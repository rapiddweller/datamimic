from pathlib import Path
import random
from datamimic_ce.domain_core.base_domain_generator import BaseDomainGenerator
from datamimic_ce.domains.common.generators.address_generator import AddressGenerator
from datamimic_ce.domains.ecommerce.generators.product_generator import ProductGenerator
from datamimic_ce.utils.file_content_storage import FileContentStorage
from datamimic_ce.utils.file_util import FileUtil


class OrderGenerator(BaseDomainGenerator):
    def __init__(self, dataset: str = "US"):
        self._dataset = dataset
        self._product_generator = ProductGenerator(dataset=dataset)
        self._address_generator = AddressGenerator(country_code=dataset)

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
        file_path = (Path(__file__).parent.parent.parent
                     .parent / "domain_data/ecommerce" / f"order_statuses_{self._dataset}.csv")
        weights, loaded_status = FileContentStorage.load_file_with_custom_func(
            str(file_path),
            lambda: FileUtil.read_csv_having_weight_column(file_path, "weight", ","))
        return random.choices(loaded_status, weights=weights, k=1)[0]["status"]
    
    def get_payment_method(self) -> str:
        file_path = (Path(__file__).parent.parent.parent
                     .parent / "domain_data/ecommerce" / f"payment_methods_{self._dataset}.csv")
        weights, loaded_methods = FileContentStorage.load_file_with_custom_func(
            str(file_path),
            lambda: FileUtil.read_csv_having_weight_column(file_path, "weight", ","))
        return random.choices(loaded_methods, weights=weights, k=1)[0]["method"]
    
    def get_shipping_method(self) -> str:
        file_path = (Path(__file__).parent.parent.parent
                     .parent / "domain_data/ecommerce" / f"shipping_methods_{self._dataset}.csv")
        weights, loaded_methods = FileContentStorage.load_file_with_custom_func(
            str(file_path),
            lambda: FileUtil.read_csv_having_weight_column(file_path, "weight", ","))
        return random.choices(loaded_methods, weights=weights, k=1)[0]["method"]
    
    def get_currency_code(self) -> str:
        file_path = (Path(__file__).parent.parent.parent
                     .parent / "domain_data/ecommerce" / f"currencies_{self._dataset}.csv")
        weights, loaded_currencies = FileContentStorage.load_file_with_custom_func(str(file_path), lambda: FileUtil.read_csv_having_weight_column(file_path, "weight", ","))
        return random.choices(loaded_currencies, weights=weights, k=1)[0]["code"]

    def get_shipping_amount(self, shipping_method: str) -> float:
        file_path = (Path(__file__).parent.parent.parent
                     .parent / "domain_data/ecommerce" / f"shipping_methods_{self._dataset}.csv")
        header_dict, datas = FileContentStorage.load_file_with_custom_func(
            str(file_path),
            lambda: FileUtil.read_csv_to_dict_of_tuples_with_header(file_path, ","))
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
        except ValueError:
            raise ValueError("Shipping methods have error at cost data, please inform help-center")
        return round(random.uniform(min_cost, max_cost), 2)
