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
        # Mark as visited for processing context if needed
        with self.lock:
            if node in self.visited:
                return
            self.visited.add(node)

        for strategy in self.strategies:
            try:
                for new_node, edge in strategy.execute(node):
                    self.add_edge(edge, depth)
            except Exception:
                pass  # Strategy failures are silently ignored

    def start(self):
        if self.running:
            return
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()

    def _worker(self):
        while self.running:
            try:
                task = self.queue.get(timeout=0.5)
                try:
                    task()
                except Exception:
                    pass  # Task failures are silently ignored
                self.queue.task_done()
            except queue.Empty:
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

    def reset(self):
        with self.lock:
            self.nodes.clear()
            self.edges.clear()
            self.visited.clear()
            with self.queue.mutex:
                self.queue.queue.clear()
