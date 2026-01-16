import threading
import time
from TermTk import TTk, TTkWindow, TTkGridLayout, TTkLabel, TTkLineEdit, TTkButton, TTkLog
from TermTk import TTkContainer, TTkVBoxLayout, TTkHBoxLayout, TTkSpacer
from src.engine.core import ScannerEngine
from src.models.graph import Node, NodeType
from src.tui.widgets.ttk_graph import TTkGraphWidget

# Import strategies
from src.strategies.dns import BasicDNSStrategy
from src.strategies.txt import TxtStrategy
from src.strategies.ptr import PtrStrategy
from src.strategies.parents import ParentStrategy

class DNSScannerApp(TTkGridLayout):
    def __init__(self, root=None):
        super().__init__()
        self._root = root
        
        # Engine Setup
        self.engine = ScannerEngine(max_depth=3)
        self._register_strategies()
        self.is_scanning = False
        
        # Layout
        # Top Bar: Domain, Depth, Scan Button
        self.top_layout = TTkHBoxLayout()
        self.addWidget(self.top_layout, 0, 0)
        
        self.top_layout.addWidget(TTkLabel(text="Domain:", maxWidth=8))
        self.input_domain = TTkLineEdit(text="pornhub.com")
        self.top_layout.addWidget(self.input_domain)
        
        self.top_layout.addWidget(TTkLabel(text="Depth:", maxWidth=7))
        self.input_depth = TTkLineEdit(text="3", maxWidth=5, inputType=TTkLineEdit.Input_Number)
        self.top_layout.addWidget(self.input_depth)
        
        self.btn_scan = TTkButton(text="Scan", border=True, maxWidth=10)
        self.btn_scan.clicked.connect(self.start_scan)
        self.top_layout.addWidget(self.btn_scan)
        
        # Main Graph Area
        self.graph_widget = TTkGraphWidget()
        self.addWidget(self.graph_widget, 1, 0)
        
        # Log / Status (Optional)
        # self.log = TTkLog(maxHeight=5)
        # self.addWidget(self.log, 2, 0)

        # Timer for updates
        # TermTk doesn't have a simple high-level timer exposed easily in all versions, 
        # but we can rely on mouse events to refresh or simple loop.
        # Actually, let's use a helper thread that calls update() via a safe method if possible.
        # TTk is not strictly thread safe for drawing.
        # We'll use a threading.Timer loop to signal update.
        self._timer_active = True
        self._update_loop()

    def _register_strategies(self):
        self.engine.register_strategy(BasicDNSStrategy())
        self.engine.register_strategy(TxtStrategy())
        self.engine.register_strategy(PtrStrategy())
        self.engine.register_strategy(ParentStrategy())

    def _update_loop(self):
        if not self._timer_active: return
        # Periodic refresh of graph data
        if self.is_scanning or self.engine.nodes:
             # We can't deep copy easily, but we can update the graph object in the widget
             # Ideally we construct a new networkx graph or sync safely
             # For now, let's just trigger a repaint/re-read
             import networkx as nx
             G = nx.Graph()
             # Copy data safely-ish
             try:
                 for node in list(self.engine.nodes):
                     G.add_node(node)
                 for edge in list(self.engine.edges):
                     G.add_edge(edge.source, edge.target)
                 
                 self.graph_widget.setGraph(G)
             except RuntimeError:
                 pass # Iterator changed size
        
        # Cleanly schedule next
        threading.Timer(1.0, self._update_loop).start()

    def start_scan(self):
        if self.is_scanning: return
        
        domain = self.input_domain.text()
        try:
            depth = int(self.input_depth.text())
        except:
            depth = 3
            
        self.is_scanning = True
        self.btn_scan.setEnabled(False)
        self.btn_scan.setText("Scanning...")
        
        def run_scan():
            try:
                self.engine.max_depth = depth
                root = Node(value=domain, type=NodeType.DOMAIN)
                self.engine.scan(root)
            except Exception as e:
                pass
            finally:
                self.is_scanning = False
                # TTk UI updates should ideally be on main thread.
                # But button text update might be fine or racey.
                # Let's leave it for the user to see graph updates.
                self.btn_scan.setText("Scan")
                self.btn_scan.setEnabled(True)

        t = threading.Thread(target=run_scan, daemon=True)
        t.start()

def run():
    root = TTk(layout=TTkGridLayout())
    app = DNSScannerApp(root)
    root.layout().addWidget(app, 0, 0)
    root.mainloop()
