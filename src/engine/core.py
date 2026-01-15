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

        try:
            for strategy in self.strategies:
                try:
                    # Strategies verify node type themselves
                    for new_node, edge in strategy.execute(node):
                        self.add_edge(edge, depth)
                except Exception as e:
                    print(f"Error in strategy {strategy.__class__.__name__} for {node}: {e}")
        except Exception as e:
             print(f"Error processing node {node}: {e}")

    def start(self):
        self.running = True
        # Use a separate thread to consume the queue and submit to the pool
        # This prevents blocking the start() method or the TUI loop
        self.dispatcher_thread = threading.Thread(target=self._dispatcher)
        self.dispatcher_thread.daemon = True
        self.dispatcher_thread.start()

    def _dispatcher(self):
        # We need a pool to execute strategies in parallel
        # Max workers = 20 to handle multiple DNS queries concurrently
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            while self.running:
                try:
                    task = self.queue.get(timeout=0.5)
                    executor.submit(task)
                    self.queue.task_done()
                except queue.Empty:
                    continue
                except Exception as e:
                    print(f"Dispatcher error: {e}")

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
