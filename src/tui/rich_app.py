import time
from typing import Dict, List, Set, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.prompt import IntPrompt, Prompt
from rich.style import Style
from rich.text import Text
from rich.tree import Tree

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
        root_label = self._node_label(root_node, is_root=True)
        tree = Tree(root_label, guide_style="grey50")

        adj = self._build_adjacency()
        visited = set([root_node])
        self._add_children(root_node, tree, adj, visited)
        return tree

    def _build_adjacency(self) -> Dict[Node, List]:
        adj: Dict[Node, List] = {}
        for edge in self.engine.edges:
            adj.setdefault(edge.source, []).append(edge)
        for edges in adj.values():
            edges.sort(key=lambda edge: (self._node_sort_key(edge.target), edge.type.value))
        return adj

    def _node_sort_key(self, node: Node) -> Tuple[int, str]:
        type_rank = {
            NodeType.DOMAIN: 0,
            NodeType.TLD: 1,
            NodeType.SERVICE: 2,
            NodeType.IP_V4: 3,
            NodeType.IP_V6: 4,
        }
        return type_rank.get(node.type, 99), node.value

    def _add_children(self, node: Node, tree_node: Tree, adj: Dict, visited: Set[Node]):
        for edge in adj.get(node, []):
            target = edge.target
            label = self._edge_label(edge, target)
            if target in visited:
                label.stylize("dim")
                tree_node.add(label)
                continue
            visited.add(target)
            child = tree_node.add(label)
            self._add_children(target, child, adj, visited)

    def _node_label(self, node: Node, is_root: bool = False) -> Text:
        label = Text()
        node_style = self._node_style(node)
        label.append(node.value, style=node_style)
        label.append(f" [{node.type.value}]", style="grey50")
        if is_root:
            label.append("  ROOT", style="bold")
        return label

    def _edge_label(self, edge, target: Node) -> Text:
        label = Text()
        label.append(edge.type.value, style=self._edge_style(edge.type.value))
        label.append("  ")
        label.append(target.value, style=self._node_style(target))
        label.append(f" [{target.type.value}]", style="grey50")
        return label

    def _node_style(self, node: Node) -> Style:
        if node.type == NodeType.DOMAIN:
            return Style(color="bright_blue", bold=True)
        if node.type == NodeType.IP_V4:
            return Style(color="yellow", bold=True)
        if node.type == NodeType.IP_V6:
            return Style(color="red", bold=True)
        if node.type == NodeType.TLD:
            return Style(color="magenta")
        if node.type == NodeType.SERVICE:
            return Style(color="green")
        if node.type == NodeType.TXT:
            return Style(color="white", dim=True)
        return Style(color="white")

    def _edge_style(self, edge_type: str) -> Style:
        palette = {
            "A": Style(color="cyan"),
            "AAAA": Style(color="cyan"),
            "CNAME": Style(color="bright_blue"),
            "NS": Style(color="blue"),
            "MX": Style(color="bright_magenta"),
            "PTR": Style(color="bright_green"),
            "TXT": Style(color="bright_yellow"),
            "SRV": Style(color="green"),
            "PARENT": Style(color="magenta"),
            "NEIGHBOR": Style(color="grey70"),
            "SUBDOMAIN": Style(color="grey70"),
        }
        return palette.get(edge_type, Style(color="white"))

    def run(self, domain: str = None, depth: int = 3):
        self.console.clear()
        self.console.print(Panel.fit("DNS Scanner", style="bold blue"))

        if not domain:
            domain = Prompt.ask("Domaine")
        
        # If depth is passed as default (3) but we are interactive (no domain was passed initially), 
        # we might want to ask? But the signature says default=3. 
        # Let's assume if domain was passed via CLI, depth might be too.
        # If domain IS None, we ask for both.
        if not domain: # Should not happen if Prompt.ask works, but logic structure...
             pass 

        # Actually, simpler logic:
        # If domain is provided, use it. If not, ask.
        # If depth is provided (from CLI default is 3, but argparse will handle it), use it.
        # If interactive, ask for depth.
        
        # Let's refine:
        # If called from CLI, domain will be set.
        # If called interactively (no args), domain is None.
        
        is_interactive = domain is None
        
        if is_interactive:
            domain = Prompt.ask("Domaine")
            depth = IntPrompt.ask("Profondeur", default=3)

        self.console.print(f"\n[green]Scan: {domain} (profondeur {depth})[/green]")
        
        start_time = time.time()
        
        # Setup Engine
        self.engine.max_depth = depth
        root = Node(value=domain, type=NodeType.DOMAIN)
        
        # Sync Scan
        with self.console.status("Scanning...", spinner="dots"):
             self.engine.scan(root)
             
        duration = time.time() - start_time
        stats = self.engine.get_stats()
        
        self.console.print(f"[bold green]Scan termine en {duration:.2f}s[/bold green]")
        self.console.print(f"Nodes: {stats['nodes']} | Edges: {stats['edges']}")
        
        # Display Tree
        self.console.print("\n[bold]Carte des resultats:[/bold]")
        tree = self.build_rich_tree(root)
        self.console.print(tree)

        # Generate DOT
        self.console.print("\nGeneration du DOT...")
        if self.generate_dot():
            self.console.print(f"[bold green]Saved ./scan.dot[/bold green]")

def run():
    app = RichDNSApp()
    app.run()
