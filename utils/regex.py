import re


def is_int(value: str) -> bool:
    return bool(re.fullmatch(r"-?\d+", value))


def is_float(value: str) -> bool:
    return bool(re.fullmatch(r"-?\d+\.\d+", value))


def is_number(value: str) -> bool:
    return is_float(value) or is_int(value)
