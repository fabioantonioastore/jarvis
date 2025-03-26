from abc import ABC, abstractmethod
from typing import Any


class Descriptor(ABC):
    @abstractmethod
    def __set_name__(self, owner, name) -> None:
        self.storage_name = name

    @abstractmethod
    def __get__(self, instance, owner) -> Any:
        return instance.__dict__[self.storage_name]

    @abstractmethod
    def __set__(self, instance, value) -> None:
        instance.__dict__[self.storage_name] = value

    @abstractmethod
    def __delete__(self, instance) -> None:
        del self.__dict__[self.storage_name]
