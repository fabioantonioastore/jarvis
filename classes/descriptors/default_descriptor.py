from typing import Any

from ..abstract import Descriptor


class DefaultDescriptor(Descriptor):
    def __set_name__(self, owner, name) -> None:
        self.storage_name = name

    def __get__(self, instance, owner) -> Any:
        return instance.__dict__[self.storage_name]

    def __set__(self, instance, value) -> None:
        instance.__dict__[self.storage_name] = value

    def __delete__(self, instance) -> None:
        del instance.__dict__[self.storage_name]
