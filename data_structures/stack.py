from typing import Any
from collections.abc import Iterable

from classes.descriptors import DefaultDescriptor
from data_structures import Node


class Stack:
    pointer = DefaultDescriptor()

    def __init__(self) -> None:
        self.pointer = None
        self.size = 0

    def add(self, value: Any) -> None:
        node = Node(value)
        self.size += 1
        if self.pointer is None:
            self.pointer = node
            return
        self.pointer.prev = node
        node.next = self.pointer
        self.pointer = node

    def pop(self) -> Any:
        if self.pointer is None:
            raise OverflowError("Stack is empty")
        node = self.pointer
        self.pointer = self.pointer.next
        if self.pointer:
            self.pointer.prev = None
        self.size -= 1
        return node.value

    def find(self, value: Any) -> bool:
        node = self.pointer
        while not node is None:
            if node.value == value:
                return True
            node = node.next
        return False

    def __list__(self) -> list[Any]:
        result = []
        node = self.pointer
        while not node is None:
            result.append(node.value)
            node = node.next
        return result

    def __len__(self) -> int:
        return self.size

    def __repr__(self) -> str:
        return f"Stack()"
