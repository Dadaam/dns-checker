from abc import ABC, abstractmethod
from typing import List, Generator, Tuple
from src.models.graph import Node, Edge

class Strategy(ABC):
    @abstractmethod
    def execute(self, node: Node) -> Generator[Tuple[Node, Edge], None, None]:
        """
        Execute the strategy on a given node.
        Yields tuples of (NewNode, EdgeToNewNode).
        """
        pass
