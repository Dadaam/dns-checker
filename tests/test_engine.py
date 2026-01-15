import pytest
import threading
from src.engine.core import ScannerEngine
from src.models.graph import Node, Edge, NodeType, EdgeType
from src.strategies.base import Strategy
from typing import Generator, Tuple

class MockStrategy(Strategy):
    def execute(self, node: Node) -> Generator[Tuple[Node, Edge], None, None]:
        if node.value == "root":
            child = Node("child", NodeType.DOMAIN)
            yield child, Edge(node, child, EdgeType.A)

def test_engine_add_node():
    engine = ScannerEngine()
    node = Node("root", NodeType.DOMAIN)
    engine.add_node(node)
    
    assert node in engine.nodes
    assert engine.queue.qsize() == 1 # Scheduled scan

def test_engine_execution():
    engine = ScannerEngine()
    engine.register_strategy(MockStrategy())
    
    root = Node("root", NodeType.DOMAIN)
    engine.add_node(root)
    engine.start()
    
    # Wait a bit for processing
    import time
    time.sleep(0.5)
    engine.stop()
    
    # Check if child was found
    found_values = [n.value for n in engine.nodes]
    assert "child" in found_values
    assert len(engine.edges) == 1
