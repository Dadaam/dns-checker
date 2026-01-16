import time
from typing import Dict, List, Set, Optional

from rich.console import Console
from rich.tree import Tree
from rich.prompt import Prompt, IntPrompt
from rich.panel import Panel
from rich import print as rprint

from src.engine.core import ScannerEngine
from src.models.graph import Node, NodeType

class RichDNSApp:
    def __init__(self):
        self.console = Console()
        self.engine = ScannerEngine(max_depth=3)
        self.register_strategies()

    def register_strategies(self):
        from src.strategies.dns import BasicDNSStrategy
        from src.strategies.txt import TxtStrategy
        from src.strategies.ptr import PtrStrategy
        from src.strategies.parents import ParentStrategy
        self.engine.register_strategy(BasicDNSStrategy())
        self.engine.register_strategy(TxtStrategy())
        self.engine.register_strategy(PtrStrategy())
        self.engine.register_strategy(ParentStrategy())

    def generate_dot(self, filename="scan.dot"):
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write("digraph G {\n")
                f.write("  rankdir=LR;\n")
                f.write("  node [style=filled, fontname=\"Helvetica\"];\n")
                
                nodes = list(self.engine.nodes)
                edges = list(self.engine.edges)
                
                for node in nodes:
                    color = "lightblue"
                    if node.type == NodeType.IP_V4: color = "gold"
                    elif node.type == NodeType.IP_V6: color = "orange"
                    elif node.type == NodeType.TLD: color = "lightgrey"
                    elif node.type == NodeType.SERVICE: color = "pink"
                    
                    safe_id = str(hash(node))
                    label = node.value.replace('"', '\\"')
                    f.write(f'  "{safe_id}" [label="{label}", fillcolor="{color}", shape=box];\n')
                
                for edge in edges:
                    safe_src = str(hash(edge.source))
                    safe_tgt = str(hash(edge.target))
                    f.write(f'  "{safe_src}" -> "{safe_tgt}" [label="{edge.type.value}"];\n')
                
                f.write("}\n")
            return True
        except Exception as e:
            self.console.print(f"[red]Error generating DOT:[/red] {e}")
            return False

    def build_rich_tree(self, root_node: Node) -> Tree:
        """
        Builds a connected Rich Tree from the graph edges.
        """
        # Style for root
        root_txt = f"[bold blue]{root_node.value}[/bold blue]"
        tree = Tree(root_txt)
        
        # We need an adjacency list for easier traversal
        adj: Dict[Node, List] = {}
        for edge in self.engine.edges:
            if edge.source not in adj:
                adj[edge.source] = []
            adj[edge.source].append(edge)

        # Global visited set for Spanning Tree visualization
        visited_global = set()
        visited_global.add(root_node)
        
        self._add_children(root_node, tree, adj, visited_global)
        return tree

    def _add_children(self, node: Node, tree_node: Tree, adj: Dict, visited_global: Set[Node]):
        edges = adj.get(node, [])
        for edge in edges:
            target = edge.target
            
            # Determine color/style
            style = "white"
            if target.type == NodeType.IP_V4: style = "bold yellow"
            elif target.type == NodeType.IP_V6: style = "bold red"
            elif target.type == NodeType.DOMAIN: style = "bold blue"
            elif target.type == NodeType.TLD: style = "bold magenta"
            elif target.type == NodeType.SERVICE: style = "bold cyan"
            
            # Edge style
            edge_style = "dim"
            
            label = f"[{edge_style}]-- {edge.type.value} -->[/{edge_style}] [{style}]{target.value} ({target.type.value})[/{style}]"
            
            if target in visited_global:
                # Duplicate/Reference: Show with dim style, no recursion
                tree_node.add(f"[dim]{label}[/dim]")
            else:
                visited_global.add(target)
                child_tree = tree_node.add(label)
                # Recurse
                self._add_children(target, child_tree, adj, visited_global)

    def run(self):
        self.console.clear()
        self.console.rule("[bold blue]DNS Scanner (Synchronous)[/bold blue]")
        
        domain = Prompt.ask("Enter Domain")
        
        # Depth default infinite (represented as 100 here for practicality, or we can use a very large number)
        depth_str = Prompt.ask("Enter Depth (Leave empty for Infinite)", default="999")
        try:
            depth = int(depth_str)
        except ValueError:
            depth = 999

        self.console.print(f"\n[green]Scanning {domain} (Depth: {depth})...[/green]")
        
        start_time = time.time()
        
        # Setup Engine
        self.engine.max_depth = depth
        root = Node(value=domain, type=NodeType.DOMAIN)
        
        # Sync Scan
        with self.console.status("Scanning...", spinner="dots"):
             self.engine.scan(root)
             
        duration = time.time() - start_time
        stats = self.engine.get_stats()
        
        self.console.print(f"[bold green]Scan Complete in {duration:.2f}s![/bold green]")
        self.console.print(f"Nodes: {stats['nodes']} | Edges: {stats['edges']}")
        
        # Display Tree
        self.console.print("\n[bold]Results Map:[/bold]")
        tree = self.build_rich_tree(root)
        self.console.print(tree)

        # Generate DOT
        self.console.print("\nGenerating DOT file...")
        if self.generate_dot():
            self.console.print(f"[bold green]Saved ./scan.dot[/bold green]")

def run():
    app = RichDNSApp()
    app.run()
