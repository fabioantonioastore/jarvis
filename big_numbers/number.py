from classes.abstract import BigNumber
from utils import big_number
from utils.regex import is_int, is_float


class Int(BigNumber):
    def __init__(self, value: BigNumber.BigNumbers) -> None:
        self.value = value

    @property
    def value(self) -> str:
        if not isinstance(self._value, str):
            return str(self._value)
        return self._value

    @value.setter
    def value(self, value: BigNumber.BigNumbers) -> None:
        if isinstance(value, str | float | int):
            if not isinstance(value, str):
                value = str(value)
            self._value = big_number.string_value_to_int(value)
            return
        self._value = big_number.string_value_to_int(value.value)

    def __add__(self, other: BigNumber.BigNumbers) -> BigNumber.BigNumbers:
        result = big_number.big_number_sum(self, other)
        if is_int(result):
            return Int(result)
        if is_float(result):
            return Float(result)

    def __sub__(self, other: BigNumber.BigNumbers) -> BigNumber.BigNumbers:
        return big_number.big_number_sub(self, other)

    def __mul__(self, other: BigNumber.BigNumbers) -> BigNumber.BigNumbers:
        pass

    def __divmod__(self, other: BigNumber.BigNumbers) -> BigNumber.BigNumbers:
        pass

    def __truediv__(self, other: BigNumber.BigNumbers) -> BigNumber.BigNumbers:
        pass

    def __floordiv__(self, other: BigNumber.BigNumbers) -> BigNumber.BigNumbers:
        pass

    def __pow__(
        self, power: int | float, modulo: int | float | None = None
    ) -> BigNumber.BigNumbers:
        pass


class Float(BigNumber):
    def __init__(self, value: BigNumber.BigNumbers) -> None:
        self.value = value

    @property
    def value(self) -> str:
        return self._value

    @value.setter
    def value(self, value: BigNumber.BigNumbers) -> None:
        if isinstance(value, str | float | int):
            if not isinstance(value, str):
                value = str(value)
            self._value = big_number.string_value_to_float(value)
            return
        self._value = big_number.string_value_to_float(value.value)

    def __add__(self, other: BigNumber.BigNumbers) -> BigNumber.BigNumbers:
        result = big_number.big_number_sum(self, other)
        if is_int(result):
            return Int(result)
        if is_float(result):
            return Float(result)

    def __sub__(self, other: BigNumber.BigNumbers) -> BigNumber.BigNumbers:
        pass

    def __mul__(self, other: BigNumber.BigNumbers) -> BigNumber.BigNumbers:
        pass

    def __divmod__(self, other: BigNumber.BigNumbers) -> BigNumber.BigNumbers:
        pass

    def __truediv__(self, other: BigNumber.BigNumbers) -> BigNumber.BigNumbers:
        pass

    def __floordiv__(self, other: BigNumber.BigNumbers) -> BigNumber.BigNumbers:
        pass

    def __pow__(
        self, power: int | float, modulo: int | float | None = None
    ) -> BigNumber.BigNumbers:
        pass
