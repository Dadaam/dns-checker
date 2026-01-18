from abc import ABC, abstractmethod
from typing import List, Generator, Tuple
from src.models.graph import Node, Edge

class Strategy(ABC):
    @abstractmethod
    def execute(self, node: Node) -> Generator[Tuple[Node, Edge], None, None]:
        """
        Exécute la stratégie sur un nœud donné.
        Génère des tuples de (NouveauNœud, ArêteVersNouveauNœud).
        """
        pass
