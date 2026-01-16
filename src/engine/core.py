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
        Scans starting from root_node using an iterative stack (DFS).
        """
        self.nodes.clear()
        self.edges.clear()
        self.visited.clear()
        
        self.nodes.add(root_node)
        
        # Stack stores tuples of (Node, depth)
        stack = [(root_node, 0)]
        
        while stack:
            node, depth = stack.pop()
            
            if depth >= self.max_depth:
                continue
            
            if node in self.visited:
                continue
            self.visited.add(node)
            
            # Execute strategies
            new_edges = []
            for strategy in self.strategies:
                try:
                    results = strategy.execute(node)
                    for _, edge in results:
                        new_edges.append(edge)
                except Exception:
                    pass 
            
            # Process results
            # We iterate in reverse to maintain order when pushing to stack (optional but nice)
            for edge in reversed(new_edges):
                if edge not in self.edges:
                    self.edges.add(edge)
                    target = edge.target
                    if target not in self.nodes:
                        self.nodes.add(target)
                    
                    # Push to stack
                    stack.append((target, depth + 1))

    def get_stats(self):
        return {
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "visited": len(self.visited)
        }
