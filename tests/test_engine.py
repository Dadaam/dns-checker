import tests  # Configure le path

from src.engine.core import ScannerEngine
from src.models.graph import Node, Edge, NodeType, EdgeType
from src.strategies.base import Strategy
from typing import Generator, Tuple

class MockStrategy(Strategy):
    def execute(self, node: Node) -> Generator[Tuple[Node, Edge], None, None]:
        if node.value == "root":
            child = Node("child", NodeType.DOMAIN)
            yield child, Edge(node, child, EdgeType.A)

def test_engine_register_strategy():
    engine = ScannerEngine()
    strategy = MockStrategy()
    engine.register_strategy(strategy)
    
    assert strategy in engine.strategies
    assert len(engine.strategies) == 1

def test_engine_scan():
    engine = ScannerEngine()
    engine.register_strategy(MockStrategy())
    
    root = Node("root", NodeType.DOMAIN)
    engine.scan(root)
    
    # Check if child was found
    found_values = [n.value for n in engine.nodes]
    assert "root" in found_values
    assert "child" in found_values
    assert len(engine.edges) == 1

def test_engine_stats():
    engine = ScannerEngine()
    engine.register_strategy(MockStrategy())
    
    root = Node("root", NodeType.DOMAIN)
    engine.scan(root)
    
    stats = engine.get_stats()
    assert stats["nodes"] == 2
    assert stats["edges"] == 1
    assert stats["visited"] == 2


if __name__ == "__main__":
    test_engine_register_strategy()
    test_engine_scan()
    test_engine_stats()
    print("✓ Tout est OK !")
