from dataclasses import dataclass


@dataclass
class BigNumberProcessingStorage:
    before_dot: str
    after_dot: str = "0"

    def __repr__(self) -> str:
        return f"BigNumberProcessing({self.before_dot!r}, {self.after_dot!r})"
