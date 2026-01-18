import threading
import time
from TermTk import TTk, TTkWindow, TTkGridLayout, TTkLabel, TTkLineEdit, TTkButton, TTkLog
from TermTk import TTkContainer, TTkVBoxLayout, TTkHBoxLayout, TTkSpacer
from src.engine.core import ScannerEngine
from src.models.graph import Node, NodeType
from src.tui.widgets.ttk_graph import TTkGraphWidget

# Import des stratégies
from src.strategies.dns import BasicDNSStrategy
from src.strategies.txt import TxtStrategy
from src.strategies.ptr import PtrStrategy
from src.strategies.parents import ParentStrategy

class DNSScannerApp(TTkContainer):
    def __init__(self, root=None):
        super().__init__()
        self._root = root
        
        # Utilise une grille pour le conteneur principal de l'application
        self.setLayout(TTkGridLayout())
        
        # Configuration du Moteur
        self.engine = ScannerEngine(max_depth=3)
        self._register_strategies()
        self.is_scanning = False
        
        # Mise en page
        # Barre supérieure : Domaine, Profondeur, Bouton Scan
        # Envelopper dans un conteneur à ajouter comme widget
        self.top_container = TTkContainer(maxHeight=3, border=False)
        self.top_layout = TTkHBoxLayout()
        self.top_container.setLayout(self.top_layout)
        
        self.layout().addWidget(self.top_container, 0, 0)
        
        self.top_layout.addWidget(TTkLabel(text="Domain:", maxWidth=8))
        self.input_domain = TTkLineEdit(text="pornhub.com")
        self.top_layout.addWidget(self.input_domain)
        
        self.top_layout.addWidget(TTkLabel(text="Depth:", maxWidth=7))
        self.input_depth = TTkLineEdit(text="3", maxWidth=5)
        self.top_layout.addWidget(self.input_depth)
        
        self.btn_scan = TTkButton(text="Scan", border=True, maxWidth=10)
        self.btn_scan.clicked.connect(self.start_scan)
        self.top_layout.addWidget(self.btn_scan)
        
        # Zone principale du graphe
        self.graph_widget = TTkGraphWidget()
        self.layout().addWidget(self.graph_widget, 1, 0)
        
        # Timer pour les mises à jour
        self._timer_active = True
        self._update_loop()

    def _register_strategies(self):
        self.engine.register_strategy(BasicDNSStrategy())
        self.engine.register_strategy(TxtStrategy())
        self.engine.register_strategy(PtrStrategy())
        self.engine.register_strategy(ParentStrategy())

    def _update_loop(self):
        if not self._timer_active: return
        # Rafraîchissement périodique des données du graphe
        if self.is_scanning or self.engine.nodes:
             import networkx as nx
             G = nx.Graph()
             # Copie des données de manière plus ou moins sûre
             try:
                 for node in list(self.engine.nodes):
                     G.add_node(node)
                 for edge in list(self.engine.edges):
                     G.add_edge(edge.source, edge.target)
                 
                 self.graph_widget.setGraph(G)
             except RuntimeError:
                 pass # La taille de l'itérateur a changé
        
        # Planifier proprement le suivant
        threading.Timer(1.0, self._update_loop).start()

    def start_scan(self):
        if self.is_scanning: return
        
        domain = str(self.input_domain.text())
        try:
            depth = int(str(self.input_depth.text()))
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
                self.btn_scan.setText("Scan")
                self.btn_scan.setEnabled(True)

        t = threading.Thread(target=run_scan, daemon=True)
        t.start()


def run():
    root = TTk(layout=TTkGridLayout())
    app = DNSScannerApp(root)
    root.layout().addWidget(app, 0, 0)
    root.mainloop()
