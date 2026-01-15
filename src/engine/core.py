import queue
import threading
from typing import Set, List, Optional, Callable
from src.models.graph import Node, Edge, NodeType

class ScannerEngine:
    def __init__(self):
        self.queue = queue.Queue()
        self.nodes: Set[Node] = set()
        self.edges: Set[Edge] = set()
        self.visited: Set[str] = set() # Track visited values to prevent infinite loops
        self.running = False
        self.lock = threading.Lock()
        
    def add_node(self, node: Node):
        with self.lock:
            if node not in self.nodes:
                self.nodes.add(node)
                # Auto-schedule tasks for this new node based on its type?
                # For now, just adding to graph. The strategy calling this should add tasks.
                
    def add_edge(self, edge: Edge):
        with self.lock:
            self.edges.add(edge)
            self.add_node(edge.source)
            self.add_node(edge.target)

    def add_task(self, task: Callable):
        self.queue.put(task)

    def start(self):
        self.running = True
        # For now, simple synchronous consumption or thread pool
        # User wants "real time dashboard", so maybe a background thread is best
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
                print(f"Error executing task: {e}")

    def stop(self):
        self.running = False

    def get_stats(self):
        with self.lock:
            return {
                "nodes": len(self.nodes),
                "edges": len(self.edges),
                "queue": self.queue.qsize()
            }
