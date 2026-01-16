from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Label, Button, Static
from textual.containers import Container
from textual.binding import Binding
from textual import work

from src.engine.core import ScannerEngine
from src.models.graph import Node, NodeType
from src.tui.widgets.graph import GraphWidget

# Make sure all strategies are imported and registered
from src.strategies.dns import BasicDNSStrategy
from src.strategies.txt import TxtStrategy
from src.strategies.ptr import PtrStrategy
from src.strategies.parents import ParentStrategy

class DNSTextualApp(App):
    CSS = """
    Screen {
        layout: vertical;
    }
    
    #controls {
        layout: horizontal;
        height: auto;
        dock: top;
        padding: 1;
        background: $boost;
        border-bottom: solid $accent;
    }
    
    GraphWidget {
        background: $surface;
        width: 100%;
        height: 1fr;
    }

    #stats {
        padding-left: 2;
        color: $text-muted;
    }

    #spacer {
        width: 1fr;
    }

    #close_button {
        min-width: 3;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh_layout", "Re-Layout"),
    ]

    def __init__(self):
        super().__init__()
        self.engine = ScannerEngine(max_depth=3)
        self.register_strategies()
        self.is_scanning = False
        self.root_node = None
        self._last_counts = (0, 0)

    def register_strategies(self):
        self.engine.register_strategy(BasicDNSStrategy())
        self.engine.register_strategy(TxtStrategy())
        self.engine.register_strategy(PtrStrategy())
        self.engine.register_strategy(ParentStrategy())

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="controls"):
            yield Label("Domaine:")
            yield Input(placeholder="exemple.com", id="domain_input")
            yield Label("Profondeur:", classes="pad-left")
            yield Input(placeholder="3", value="3", id="depth_input", type="integer")
            yield Button("-", id="depth_down")
            yield Button("+", id="depth_up")
            yield Button("Scan", id="scan_button")
            yield Label("Idle", id="stats")
            yield Static("", id="spacer")
            yield Button("X", id="close_button", variant="error")
        
        yield GraphWidget(id="graph")
        yield Footer()

    def on_mount(self):
        self.query_one("#domain_input").focus()
        # Set up a timer to refresh the graph view periodically if scanning
        self.set_interval(0.5, self.update_graph_view)

    async def on_input_submitted(self, event: Input.Submitted):
        if event.input.id == "domain_input":
            domain = event.value
            depth = self._parse_depth()
            
            if domain:
                self.begin_scan(domain, depth)
        
        elif event.input.id == "depth_input":
             # Move back to domain input or start if possible
             self.query_one("#domain_input").focus()

    def on_button_pressed(self, event: Button.Pressed):
        if event.button.id == "scan_button":
            domain = self.query_one("#domain_input").value
            depth = self._parse_depth()
            if domain:
                self.begin_scan(domain, depth)
        elif event.button.id == "depth_down":
            self._adjust_depth(-1)
        elif event.button.id == "depth_up":
            self._adjust_depth(1)
        elif event.button.id == "close_button":
            self.exit()

    def begin_scan(self, domain: str, depth: int):
        if self.is_scanning:
            return
        self.is_scanning = True
        self._last_counts = (0, 0)
        self.root_node = Node(value=domain, type=NodeType.DOMAIN)
        self.query_one("#scan_button").disabled = True
        self.query_one("#stats", Label).update("Scanning...")
        self.query_one(GraphWidget).set_root(self.root_node)
        self.start_scan(domain, depth)

    def _parse_depth(self) -> int:
        try:
            return max(1, int(self.query_one("#depth_input").value))
        except (TypeError, ValueError):
            return 3

    def _adjust_depth(self, delta: int):
        depth = self._parse_depth() + delta
        if depth < 1:
            depth = 1
        self.query_one("#depth_input", Input).value = str(depth)

    @work(exclusive=True, thread=True)
    def start_scan(self, domain: str, depth: int):
        self.engine.max_depth = depth
        
        # Reset engine state manually before scan if needed, or rely on scan() clearing it.
        # core.py scan() clears nodes/edges.
        
        root = Node(value=domain, type=NodeType.DOMAIN)
        
        self.notify(f"Starting scan for {domain}...")
        try:
            self.engine.scan(root)
            self.notify("Scan complete!", severity="information")
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
        finally:
            self.is_scanning = False
            self.call_from_thread(self._scan_finished)

    def _scan_finished(self):
        self.query_one("#scan_button").disabled = False
        stats = self.engine.get_stats()
        self.query_one("#stats", Label).update(f"Done: {stats['nodes']} nodes / {stats['edges']} edges")

    def update_graph_view(self):
        # This is called on the main thread
        # We can read the engine's nodes/edges. 
        # Since engine is modifying them in a thread, this is technically a race condition.
        # But for visualization, it might just flicker or miss a node, which is acceptable for this prototype.
        
        # We create a shallow copy networkx graph
        # Creating a full NX graph every 500ms might be heavy if N is large.
        
        import networkx as nx
        G = nx.DiGraph()
        nodes = list(self.engine.nodes)
        edges = list(self.engine.edges)

        if not nodes and not edges:
            return

        # Add nodes
        for node in nodes:
            G.add_node(node)

        # Add edges
        for edge in edges:
            G.add_edge(edge.source, edge.target, edge_type=edge.type)

        counts = (len(nodes), len(edges))
        if counts != self._last_counts:
            self._last_counts = counts
            graph_widget = self.query_one(GraphWidget)
            graph_widget.set_graph(G, root=self.root_node)

        if self.is_scanning:
            self.query_one("#stats", Label).update(f"Scanning... {counts[0]} nodes / {counts[1]} edges")

    def action_refresh_layout(self):
        self.query_one(GraphWidget).recompute_layout()
        self.query_one(GraphWidget).refresh()

def run():
    app = DNSTextualApp()
    app.run()
