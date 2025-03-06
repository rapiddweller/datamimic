from typing import TypeVar, Generic, Type
from datamimic_ce.domain_core.base_entity import BaseEntity
from datamimic_ce.domain_core.base_data_loader import BaseDataLoader
from datamimic_ce.generators.generator import Generator

T = TypeVar("T", bound=BaseEntity)
class DomainGenerator(Generator, Generic[T]):
    """
    Base class for all domain generators.
    """

    def __init__(self, data_loader: BaseDataLoader, model_cls: Type[T]):
        self._data_loader = data_loader
        self._model_cls = model_cls

    def generate(self) -> T:
        """
        Generate a single instance of the domain object.
        :return:
        """
        return self._model_cls(self._data_loader)

    def generate_batch(self, count: int = 10) -> list[T]:
        """
        Generate a batch of data
        :param count:
        :return:
        """
        return [self.generate() for _ in range(count)]