from textual.widget import Widget
from textual.geometry import Size
from rich.segment import Segment
from textual.strip import Strip
from rich.style import Style
import networkx as nx
import math

class GraphWidget(Widget):
    """
    A Textual widget that renders a NetworkX graph.
    Uses a force-directed layout (spring_layout) to center the graph.
    """
    
    DEFAULT_CSS = """
    GraphWidget {
        width: 100%;
        height: 100%;
        min-width: 50;
        min-height: 20;
    }
    """

    def __init__(self, graph: nx.Graph = None, name: str = None, id: str = None, classes: str = None):
        super().__init__(name=name, id=id, classes=classes)
        self.graph = graph if graph else nx.Graph()
        self._pos = {}
        self._zoom = 2.0
        self._center_offset_x = 0
        self._center_offset_y = 0
        self.recompute_layout()

    def set_graph(self, graph: nx.Graph):
        self.graph = graph
        self.recompute_layout()
        self.refresh()

    def recompute_layout(self):
        if not self.graph.nodes:
            self._pos = {}
            return
            
        # Compute layout centered at (0,0)
        # Using kamada_kawai for nicer "spread" or spring for force-dir
        # spring_layout is faster for dynamic updates
        self._pos = nx.spring_layout(self.graph, center=(0,0), scale=10, seed=42)

    def render_line(self, y: int) -> Strip:
        width = self.size.width
        height = self.size.height
        
        # Determine the logical y-coordinate relative to center
        # Screen center is (width/2, height/2)
        # We want (0,0) to be at screen center
        
        # logical_y = (y - height/2) / vertical_scale
        
        segments = []
        line_chars = [" "] * width
        
        if not self._pos:
             return Strip([Segment( " " * width )])

        # Very basic rendering: iterate nodes and place them
        # In a real efficient implementation, we'd use a spatial index
        
        center_x = width // 2 + self._center_offset_x
        center_y = height // 2 + self._center_offset_y
        
        # Scaling factors
        scale_x = self._zoom * 2.0 # Characters are taller than wide
        scale_y = self._zoom
        
        nodes_on_line = []
        
        for node, (nx_x, nx_y) in self._pos.items():
            screen_x = int(nx_x * scale_x + center_x)
            screen_y = int(nx_y * scale_y + center_y)
            
            if screen_y == y:
                nodes_on_line.append((screen_x, node))
                
        # Draw edges (naive Bresenham check for every pixel on this line? Too slow).
        # We will skip edge drawing for this V1 textual implementation 
        # unless we find a fast way. Rich's Canvas is gone.
        # We could just verify if a line segment crosses this row 'y' at 'x'.
        # Let's stick to nodes for safety first, maybe add lines if performance allows.
        
        # Draw nodes
        for sx, node in nodes_on_line:
            if 0 <= sx < width:
                # Determine color based on node type if available (unsafe access?)
                node_obj = node # It's the Node object itself if we used Node objects as keys
                
                label = str(node_obj)
                # Truncate if needed
                if len(label) > 20: label = label[:17] + "..."
                
                # Draw marker
                line_chars[sx] = "●" 
                
                # Draw Label
                for i, char in enumerate(label):
                    if sx + 2 + i < width:
                         line_chars[sx + 2 + i] = char

        return Strip([Segment("".join(line_chars))])

