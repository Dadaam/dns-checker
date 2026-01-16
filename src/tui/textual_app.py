import asyncio
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Input, Label, Static
from textual.containers import Container, Vertical
from textual.binding import Binding
from textual.worker import Worker, get_current_worker
from textual import work
from rich.console import Console

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
        height: auto;
        dock: top;
        padding: 1;
        background: $boost;
        border-bottom: solid green;
    }
    
    GraphWidget {
        background: $surface;
        width: 100%;
        height: 1fr;
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

    def register_strategies(self):
        self.engine.register_strategy(BasicDNSStrategy())
        self.engine.register_strategy(TxtStrategy())
        self.engine.register_strategy(PtrStrategy())
        self.engine.register_strategy(ParentStrategy())

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="controls"):
            yield Label("Domain:")
            yield Input(placeholder="example.com", id="domain_input")
            yield Label("Depth:", classes="pad-left")
            yield Input(placeholder="3", value="3", id="depth_input", type="integer")
        
        yield GraphWidget(id="graph")
        yield Footer()

    def on_mount(self):
        self.query_one("#domain_input").focus()
        # Set up a timer to refresh the graph view periodically if scanning
        self.set_interval(0.5, self.update_graph_view)

    async def on_input_submitted(self, event: Input.Submitted):
        if event.input.id == "domain_input":
            domain = event.value
            depth = int(self.query_one("#depth_input").value)
            
            if domain:
                self.start_scan(domain, depth)
        
        elif event.input.id == "depth_input":
             # Move back to domain input or start if possible
             self.query_one("#domain_input").focus()

    @work(exclusive=True, thread=True)
    def start_scan(self, domain: str, depth: int):
        self.is_scanning = True
        self.engine.max_depth = depth
        
        # Reset engine state manually before scan if needed, or rely on scan() clearing it.
        # core.py scan() clears nodes/edges.
        
        root = Node(value=domain, type=NodeType.DOMAIN)
        
        # We need to bridge the sync engine with UI updates.
        # Ideally, we'd watch the engine.nodes count, but the engine blocks.
        # We can run the engine in this worker thread.
        
        # BUT: The engine.scan is a single blocking call. 
        # We won't see partial results unless the engine has hooks or we change the engine to be iterative/async.
        # The current iterative implementation is a while loop. 
        # For this version, we will only see results AFTER the scan finishes if we just call scan().
        # To make it "live", we would need to modify the engine to be generator-based or callback-based.
        
        # HOWEVER, let's try just running it. 
        # If the user wants to see progress, we really should refactor the engine to yield or run in steps.
        # For now, let's just run it and see the final result, or see if we can hack read-access from another thread (unsafe but might work for viz).
        
        self.notify(f"Starting scan for {domain}...")
        try:
            self.engine.scan(root)
            self.notify("Scan complete!", severity="information")
        except Exception as e:
            self.notify(f"Error: {e}", severity="error")
        finally:
            self.is_scanning = False

    def update_graph_view(self):
        # This is called on the main thread
        # We can read the engine's nodes/edges. 
        # Since engine is modifying them in a thread, this is technically a race condition.
        # But for visualization, it might just flicker or miss a node, which is acceptable for this prototype.
        
        # We create a shallow copy networkx graph
        # Creating a full NX graph every 500ms might be heavy if N is large.
        
        if not self.engine.nodes:
            return

        import networkx as nx
        G = nx.Graph()
        
        # Add nodes
        for node in list(self.engine.nodes): # simple list copy to avoid iteration error size changed
            G.add_node(node) # Use the node object itself
            
        # Add edges
        for edge in list(self.engine.edges):
            G.add_edge(edge.source, edge.target)
            
        # Update widget
        graph_widget = self.query_one(GraphWidget)
        graph_widget.set_graph(G)

    def action_refresh_layout(self):
        self.query_one(GraphWidget).recompute_layout()
        self.query_one(GraphWidget).refresh()

def run():
    app = DNSTextualApp()
    app.run()
