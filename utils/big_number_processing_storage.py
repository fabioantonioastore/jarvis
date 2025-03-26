from classes.dataclasses import BigNumberProcessingStorage
from utils.regex import is_int, is_float


def big_number_processing_storage_factory(value: str) -> BigNumberProcessingStorage:
    if is_float(value):
        value = value.split(".")
        return BigNumberProcessingStorage(value[0], value[1])
    if is_int(value):
        return BigNumberProcessingStorage(value)
    raise ValueError(f"Invalid value {value}")
