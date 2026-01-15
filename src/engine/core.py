import queue
import threading
from typing import Set, List, Optional, Callable
from src.models.graph import Node, Edge, NodeType

from typing import Set, List, Optional, Callable, Dict, Type
from src.models.graph import Node, Edge, NodeType
from src.strategies.base import Strategy

class ScannerEngine:
    def __init__(self, max_depth: int = 3):
        self.queue = queue.Queue()
        self.nodes: Set[Node] = set()
        self.edges: Set[Edge] = set()
        self.visited: Set[Node] = set() 
        self.running = False
        self.lock = threading.Lock()
        self.max_depth = max_depth
        self.strategies: List[Strategy] = []
        
    def register_strategy(self, strategy: Strategy):
        self.strategies.append(strategy)

    def add_node(self, node: Node, depth: int = 0):
        with self.lock:
            if node in self.nodes:
                return
            self.nodes.add(node)
        
        # Schedule scan if within depth limit
        if depth < self.max_depth:
            self.add_task(lambda: self._process_node(node, depth))

    def add_edge(self, edge: Edge, depth: int):
        with self.lock:
            self.edges.add(edge)
            # Add targets. Source is assumed added.
            # We add target with depth + 1
            self.add_node(edge.target, depth + 1)

    def add_task(self, task: Callable):
        self.queue.put(task)

    def _process_node(self, node: Node, depth: int):
        # Mark as visited for processing context if needed, but we check existence in add_node
        # However, we might want to avoid re-scanning the same node if it was added from multiple sources?
        # A set of 'scanned' nodes might be better than 'nodes' (which are just known).
        with self.lock:
            if node in self.visited:
                return
            self.visited.add(node)

        for strategy in self.strategies:
            # Strategies verify node type themselves
            for new_node, edge in strategy.execute(node):
                self.add_edge(edge, depth)

    def start(self):
        self.running = True
        worker_thread = threading.Thread(target=self._worker)
        worker_thread.daemon = True
        worker_thread.start()

    def _worker(self):
        while self.running:
            try:
                task = self.queue.get(timeout=1)
                task()
                self.queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                # Log error?
                pass

    def stop(self):
        self.running = False

    def get_stats(self):
        with self.lock:
            return {
                "nodes": len(self.nodes),
                "edges": len(self.edges),
                "queue": self.queue.qsize(),
                "visited": len(self.visited)
            }
