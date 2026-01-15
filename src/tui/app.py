import TermTk as ttk
import threading
import time
from src.engine.core import ScannerEngine
from src.models.graph import Node, NodeType
from src.strategies.dns import BasicDNSStrategy
from src.strategies.txt import TxtStrategy
from src.strategies.srv import SrvStrategy
from src.strategies.ptr import PtrStrategy
from src.strategies.parents import ParentStrategy
from src.strategies.neighbors import NeighborStrategy
from src.strategies.subdomains import SubdomainStrategy

class DNSScannerApp:
    def __init__(self):
        self.root = ttk.TTk()
        self.root.setLayout(ttk.TTkVBoxLayout())
        self.engine = ScannerEngine(max_depth=3)
        
        # Register Strategies
        self.engine.register_strategy(BasicDNSStrategy())
        self.engine.register_strategy(TxtStrategy())
        self.engine.register_strategy(SrvStrategy())
        self.engine.register_strategy(PtrStrategy())
        self.engine.register_strategy(ParentStrategy())
        self.engine.register_strategy(NeighborStrategy())
        self.engine.register_strategy(SubdomainStrategy())

        self._init_ui()
        
        # Stats Timer
        self.timer = ttk.TTkTimer()
        self.timer.timeout.connect(self._update_ui)
        self.timer.start(1.0) # Update every second

    def _init_ui(self):
        # Top Bar: Input and Controls
        top_frame = ttk.TTkFrame(parent=self.root, border=True, layout=ttk.TTkHBoxLayout(), maxHeight=5, title="Controls")
        
        input_label = ttk.TTkLabel(parent=top_frame, text="Domain:", maxWidth=8)
        self.domain_input = ttk.TTkLineEdit(parent=top_frame, text="google.com")
        self.domain_input.returnPressed.connect(self.start_scan)
        
        depth_label = ttk.TTkLabel(parent=top_frame, text="Depth:", maxWidth=7)
        self.depth_input = ttk.TTkSpinBox(parent=top_frame, value=2, maximum=10, minimum=1, maxWidth=5)
        
        self.scan_btn = ttk.TTkButton(parent=top_frame, text="START SCAN", border=True, maxWidth=12)
        self.scan_btn.clicked.connect(self.start_scan)
        
        self.export_btn = ttk.TTkButton(parent=top_frame, text="Export .dot", border=True, maxWidth=13)
        self.export_btn.clicked.connect(self.export_graphviz)

        # Main Content: Splitter (Tree View | Details/Logs)
        splitter = ttk.TTkSplitter(parent=self.root)
        
        # Left: Tree View
        self.tree = ttk.TTkTree(parent=splitter)
        self.tree.setHeaderLabels(["Type", "Value"])
        
        # Right: Logs/Stats
        right_panel = ttk.TTkFrame(parent=splitter, layout=ttk.TTkVBoxLayout(), border=False)
        self.stats_label = ttk.TTkLabel(parent=right_panel, text="Nodes: 0 | Edges: 0 | Queue: 0")
        self.log_text = ttk.TTkTextEdit(parent=right_panel, readOnly=True)
        
        self.root.layout().addWidget(top_frame)
        self.root.layout().addWidget(splitter)
        
        self.added_nodes = set()

    def log(self, msg):
        self.log_text.append(msg)

    def start_scan(self):
        domain = str(self.domain_input.text()).strip()
        depth = self.depth_input.value()
        if not domain:
            self.log("Error: Invalid domain")
            return

        self.log(f"Starting scan: {domain} (Depth: {depth})")
        self.engine.max_depth = depth
        
        # Initialize with root node
        # Detect if IP or Domain? Simple check.
        # Ideally strategies handle type check, so we guess DOMAIN mostly.
        # But if user enters IP...
        # Let's assume Domain for simplicity unless it looks like IP.
        # If IP strategy is robust, we can start with IP node.
        # For now, default to DOMAIN.
        root_node = Node(value=domain, type=NodeType.DOMAIN)
        self.engine.add_node(root_node)
        self.engine.start()

    def _update_ui(self):
        stats = self.engine.get_stats()
        self.stats_label.setText(f"Nodes: {stats['nodes']} | Edges: {stats['edges']} | Queue: {stats['queue']} | Visited: {stats['visited']}")
        
        # Update Tree (Naive approach: clear and rebuild or just add new? 
        # Rebuilding 1000 nodes every second is heavy.
        # Optim: Only add new nodes if possible.
        # Since tree structure is complex with graph cycles, 
        # let's just list them by Type for now? Or flatten?
        # User wants "Arborescence".
        # Let's try to list nodes under Categories (DOMAIN, IP, etc.)
        
        with self.engine.lock:
            current_nodes = list(self.engine.nodes)
            
        # Very naive incremental update
        # We group by type in the tree
        
        # Initialize categories if empty
        if not hasattr(self, 'cat_items'):
            self.cat_items = {}
            for ntype in NodeType:
                item = ttk.TTkTreeWidgetItem([ntype.value, ""])
                self.tree.addTopLevelItem(item)
                item.setExpanded(True)
                self.cat_items[ntype] = item

        for node in current_nodes:
            if node not in self.added_nodes:
                self.added_nodes.add(node)
                parent = self.cat_items.get(node.type)
                if parent:
                    # Color coding? TTk supports color in text?
                    # text = f"{node.value}"
                    child = ttk.TTkTreeWidgetItem([node.type.value, node.value])
                    parent.addChild(child)

    def export_graphviz(self):
        try:
            filename = "graph.dot"
            with open(filename, "w") as f:
                f.write("digraph G {\n")
                f.write("  rankdir=LR;\n")
                f.write("  node [style=filled];\n")
                
                # Write Nodes
                with self.engine.lock:
                    nodes = list(self.engine.nodes)
                    edges = list(self.engine.edges)
                
                for node in nodes:
                    color = "lightblue"
                    if node.type == NodeType.IP_V4: color = "gold"
                    elif node.type == NodeType.IP_V6: color = "orange"
                    elif node.type == NodeType.TLD: color = "lightgrey"
                    elif node.type == NodeType.SERVICE: color = "pink"
                    
                    # Sanitation
                    safe_id = str(hash(node))
                    label = node.value.replace('"', '\\"')
                    f.write(f'  "{safe_id}" [label="{label}", fillcolor="{color}", shape=box];\n')
                
                # Write Edges
                for edge in edges:
                    safe_src = str(hash(edge.source))
                    safe_tgt = str(hash(edge.target))
                    f.write(f'  "{safe_src}" -> "{safe_tgt}" [label="{edge.type.value}"];\n')
                
                f.write("}\n")
            self.log(f"Exported to {filename}")
        except Exception as e:
            self.log(f"Export failed: {e}")

def run():
    app = DNSScannerApp()
    app.root.mainloop()
