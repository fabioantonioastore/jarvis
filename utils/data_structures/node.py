from typing import Any, Optional


class Node:
    def __init__(
        self, value: Any, next: Optional["Node"] = None, prev: Optional["Node"] = None
    ) -> None:
        self.value = value
        self.next = next
        self.prev = prev

    def __repr__(self) -> str:
        return f"Node({self.value!r}, {self.next!r}, {self.prev!r})"
