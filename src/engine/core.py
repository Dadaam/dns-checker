from typing import Set, List, Optional
from src.models.graph import Node, Edge
from src.strategies.base import Strategy

class ScannerEngine:
    def __init__(self, max_depth: int = 3):
        self.nodes: Set[Node] = set()
        self.edges: Set[Edge] = set()
        self.visited: Set[Node] = set() 
        self.max_depth = max_depth
        self.strategies: List[Strategy] = []

    def register_strategy(self, strategy: Strategy):
        self.strategies.append(strategy)

    def scan(self, root_node: Node):
        """
        Scanne à partir de root_node en utilisant une pile itérative (DFS).
        """
        self.nodes.clear()
        self.edges.clear()
        self.visited.clear()
        
        self.nodes.add(root_node)
        
        # La pile stocke des tuples de (Node, profondeur)
        stack = [(root_node, 0)]
        
        while stack:
            node, depth = stack.pop()
            
            if depth >= self.max_depth:
                continue
            
            if node in self.visited:
                continue
            self.visited.add(node)
            
            # Exécuter les stratégies
            new_edges = []
            for strategy in self.strategies:
                try:
                    results = strategy.execute(node)
                    for _, edge in results:
                        new_edges.append(edge)
                except Exception:
                    pass 
            
            # Traiter les résultats
            # Nous itérons en sens inverse pour maintenir l'ordre lors de l'ajout à la pile (optionnel mais sympa)
            for edge in reversed(new_edges):
                if edge not in self.edges:
                    self.edges.add(edge)
                    target = edge.target
                    if target not in self.nodes:
                        self.nodes.add(target)
                    
                    # Ajouter à la pile
                    stack.append((target, depth + 1))

    def get_stats(self):
        return {
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "visited": len(self.visited)
        }
