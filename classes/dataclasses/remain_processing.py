from typing import NamedTuple


class RemainProcessing(NamedTuple):
    result: str
    accumulated: int = 0
