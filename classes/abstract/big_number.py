from abc import ABC, abstractmethod
from typing import Union
import copy


class BigNumber(ABC):
    BigNumbers = Union[str, int, float, "Float", "Int", "BigNumber"]

    @property
    @abstractmethod
    def value(self) -> str:
        pass

    @value.setter
    @abstractmethod
    def value(self, value: BigNumbers) -> None:
        pass

    @abstractmethod
    def __add__(self, other: BigNumbers) -> BigNumbers:
        pass

    @abstractmethod
    def __sub__(self, other: BigNumbers) -> BigNumbers:
        pass

    @abstractmethod
    def __mul__(self, other: BigNumbers) -> BigNumbers:
        pass

    @abstractmethod
    def __divmod__(self, other: BigNumbers) -> BigNumbers:
        pass

    @abstractmethod
    def __truediv__(self, other: BigNumbers) -> BigNumbers:
        pass

    @abstractmethod
    def __floordiv__(self, other: BigNumbers) -> BigNumbers:
        pass

    @abstractmethod
    def __pow__(
        self, power: int | float, modulo: int | float | None = None
    ) -> BigNumbers:
        pass

    def __copy__(self) -> BigNumbers:
        return copy.copy(self)

    def __deepcopy__(self, memodict={}) -> BigNumbers:
        return copy.deepcopy(self)

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.__str__()!r})"
