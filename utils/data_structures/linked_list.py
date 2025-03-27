from typing import Any, Optional

from collections.abc import Iterable


from utils.data_structures import Node


class LinkedList:

    def __init__(self, iterable: Optional[Iterable[Any]] = None) -> None:

        self.first = None

        self.last = None

        self.size = 0

        if iterable:

            for item in iterable:

                self.append(item)

    def append(self, value: Any) -> None:

        new_node = Node(value)

        self.size += 1

        if self.first is None:

            self.first = new_node

            self.last = self.first

            return

        self.last.next = new_node

        new_node.prev = self.last

        self.last = new_node

    def find(self, value: Any) -> bool:

        node = self.first

        while not node is None:

            if node.value == value:

                return True

            node = node.next

        return False

    def pop(self) -> Any:

        if self.last is None:

            raise "LinkedList is empty"

        self.size -= 1

        node = self.last

        if node == self.first:

            self.first = None

            self.last = None

            return node.value

        self.last = self.last.prev

        self.last.next = None

        return node.value

    def insert(self, value: Any, index: int) -> None:

        if index > len(self) - 1:

            raise IndexError(f"Invalid index: {index}")

        new_node = Node(value)

        if index == 0:

            new_node.next = self.first

            self.first.prev = new_node

            self.first = new_node

            self.size += 1

            return

        node = self.first

        while index != 0:

            node = node.next

            index -= 1

        new_node.prev = node.prev

        new_node.next = node

        node.prev.next = new_node

        self.size += 1

    def remove(self, value: Any) -> None:

        if len(self) == 0:

            return

        node = self.first

        if self.first.value == value:

            self.size -= 1

            self.first = self.first.next

            if self.first:

                self.first.prev = None

            else:

                self.last = self.first

            return

        while not node is None:

            if node.value == value:

                self.size -= 1

                node.prev.next = node.next

                if node.next:

                    node.next.prev = node.prev

                return

            node = node.next

    def __getitem__(self, index: int) -> Any:

        if index > len(self) - 1:

            raise IndexError(f"Invalid index: {index}")

        node = self.first

        while index != 0:

            node = node.next

            index -= 1

        return node.value

    def __len__(self) -> int:

        return self.size

    def __list__(self) -> list[Any]:

        result = []

        node = self.first

        while not node is None:

            result.append(node.value)

            node = node.next

        return result

    def __repr__(self) -> str:

        return f"LinkedList()"
