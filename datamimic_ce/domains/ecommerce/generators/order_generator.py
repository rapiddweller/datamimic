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
        self._address_generator = AddressGenerator(dataset=dataset)

    @property
    def dataset(self) -> str:
        return self._dataset

    @property
    def product_generator(self) -> ProductGenerator:
        return self._product_generator

    def get_order_statuses(self) -> str:
        file_path = Path(__file__).parent.parent.parent / "data" / f"order_statuses_{self._dataset}.csv"
        loaded_status, weights = FileContentStorage.load_file_with_custom_func(file_path, lambda: FileUtil.read_weight_csv(file_path, ","))
        return random.choices(loaded_status, weights=weights, k=1)[0]
    
    def get_payment_methods(self) -> str:
        file_path = Path(__file__).parent.parent.parent / "data" / f"payment_methods_{self._dataset}.csv"
        loaded_methods, weights = FileContentStorage.load_file_with_custom_func(file_path, lambda: FileUtil.read_weight_csv(file_path, ","))
        return random.choices(loaded_methods, weights=weights, k=1)[0]
    
    def get_shipping_methods(self) -> str:
        file_path = Path(__file__).parent.parent.parent / "data" / f"shipping_methods_{self._dataset}.csv"
        loaded_methods, weights = FileContentStorage.load_file_with_custom_func(file_path, lambda: FileUtil.read_weight_csv(file_path, ","))
        return random.choices(loaded_methods, weights=weights, k=1)[0]
    
    def get_currencies(self) -> str:
        file_path = Path(__file__).parent.parent.parent / "data" / f"currencies_{self._dataset}.csv"
        loaded_currencies, weights = FileContentStorage.load_file_with_custom_func(file_path, lambda: FileUtil.read_weight_csv(file_path, ","))
        return random.choices(loaded_currencies, weights=weights, k=1)[0]
    