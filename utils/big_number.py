from classes.abstract import BigNumber
from classes.dataclasses import RemainProcessing
from utils.regex import is_int, is_float
from utils.big_number_processing_storage import big_number_processing_storage_factory
from data_structures import Stack

# 30 - 39
ASCII = {
    ord("0"): "0",
    ord("1"): "1",
    ord("2"): "2",
    ord("3"): "3",
    ord("4"): "4",
    ord("5"): "5",
    ord("6"): "6",
    ord("7"): "7",
    ord("8"): "8",
    ord("9"): "9",
}


def number_to_char(number: int) -> str:
    return ASCII[number + 48]


def make_sum_remain_part(first_amount: str, second_amount: str) -> RemainProcessing:
    first_stack = Stack()
    for v in first_amount:
        first_stack.add(v)
    second_stack = Stack()
    for v in second_amount:
        second_stack.add(v)
    result_amount = Stack()
    accumulated = 0
    first_len = len(first_amount)
    second_len = len(second_amount)

    min_lenght = min(first_len, second_len)
    remain_lenght = max(first_len, second_len) - min_lenght
    for _ in range(min_lenght):
        result = (
            accumulated
            + ord(first_stack.pop())
            + ord(second_stack.pop())
            - (ord("0") * 2)
        )
        accumulated = result // 10
        result %= 10
        result_amount.add(result)

    if first_len != second_len:
        for _ in range(remain_lenght):
            if first_len > second_len:
                result = accumulated + ord(first_stack.pop()) - ord("0")
                accumulated = result // 10
                result %= 10
                result_amount.add(result)
            else:
                result = accumulated + ord(second_stack.pop()) - ord("0")
                accumulated = result // 10
                result %= 10
                result_amount.add(result)

    string_result = ""
    for _ in range(len(result_amount)):
        string_result += number_to_char(result_amount.pop())
    while string_result[0] == "0" and len(string_result) > 1:
        string_result = string_result[1::]

    return RemainProcessing(result=string_result, accumulated=accumulated)


def make_sum_integer_part(
    first_amount: str, second_amount: str, accumulated: int = 0
) -> str:
    first_stack = Stack()
    for v in first_amount:
        first_stack.add(v)
    second_stack = Stack()
    for v in second_amount:
        second_stack.add(v)
    result_amount = Stack()
    first_len = len(first_amount)
    second_len = len(second_amount)

    min_lenght = min(first_len, second_len)
    remain_lenght = max(first_len, second_len) - min_lenght
    for _ in range(min_lenght):
        result = (
            accumulated
            + ord(first_stack.pop())
            + ord(second_stack.pop())
            - (ord("0") * 2)
        )
        accumulated = result // 10
        result %= 10
        result_amount.add(result)

    if first_len != second_len:
        for _ in range(remain_lenght):
            if first_len > second_len:
                result = accumulated + ord(first_stack.pop()) - ord("0")
                accumulated = result // 10
                result %= 10
                result_amount.add(result)
            else:
                result = accumulated + ord(second_stack.pop()) - ord("0")
                accumulated = result // 10
                result %= 10
                result_amount.add(result)
    if accumulated > 0:
        result_amount.add(accumulated)

    string_result = ""
    for _ in range(len(result_amount)):
        string_result += number_to_char(result_amount.pop())

    while string_result[0] == "0" and len(string_result) > 1:
        string_result = string_result[1::]

    return string_result


def join_big_number_parts(integer_part: str, remain_part: str) -> str:
    return integer_part + "." + remain_part


def big_number_sum(
    first_cls: BigNumber.BigNumbers, second_cls: BigNumber.BigNumbers
) -> str:
    first_number_proc = big_number_processing_storage_factory(first_cls.value)
    second_number_proc = big_number_processing_storage_factory(second_cls.value)

    remain_result = make_sum_remain_part(
        first_number_proc.after_dot, second_number_proc.after_dot
    )
    integer_result = make_sum_integer_part(
        first_number_proc.before_dot,
        second_number_proc.before_dot,
        remain_result.accumulated,
    )

    if remain_result.result == "0":
        return integer_result
    return join_big_number_parts(integer_result, remain_result.result)


def big_number_sub(
    first_cls: BigNumber.BigNumbers, second_cls: BigNumber.BigNumbers
) -> BigNumber.BigNumbers:
    pass


def string_value_to_int(value_str: str) -> str:
    if is_float(value_str):
        return string_float_to_int_converter(value_str)
    if is_int(value_str):
        return value_str
    raise ValueError(f"Invalid value {value_str}")


def string_value_to_float(value_str: str) -> str:
    if is_int(value_str):
        return string_int_to_float_converter(value_str)
    if is_float(value_str):
        return value_str
    raise ValueError(f"Invalid value {value_str}")


def string_float_to_int_converter(string: str) -> str:
    return string.split(".")[0]


def string_int_to_float_converter(string: str) -> str:
    return string + ".0"
