from textual.widget import Widget
from textual.geometry import Size
from rich.segment import Segment
from textual.strip import Strip
from rich.style import Style
from textual import events
from textual.binding import Binding
import networkx as nx
import math
from src.models.graph import NodeType

class GraphWidget(Widget):
    """
    A Textual widget that renders a NetworkX graph with interactivity.
    Supports:
    - Force-directed layout
    - Pan & Zoom
    - Edge rendering (Bresenham's line algorithm)
    - Node coloring
    """
    
    DEFAULT_CSS = """
    GraphWidget {
        width: 100%;
        height: 100%;
        min-width: 50;
        min-height: 20;
        background: $surface;
    }
    """
    
    BINDINGS = [
        Binding("+", "zoom_in", "Zoom In"),
        Binding("-", "zoom_out", "Zoom Out"),
    ]

    def __init__(self, graph: nx.Graph = None, name: str = None, id: str = None, classes: str = None):
        super().__init__(name=name, id=id, classes=classes)
        self.graph = graph if graph else nx.Graph()
        self._pos = {}
        
        # Viewport state
        self._zoom = 4.0
        self._center_offset_x = 0
        self._center_offset_y = 0
        self._drag_start = None
        self._last_mouse_pos = None
        self._is_dragging = False

        self.recompute_layout()

    def set_graph(self, graph: nx.Graph):
        self.graph = graph
        self.recompute_layout()
        self.refresh()

    def recompute_layout(self):
        if not self.graph.nodes:
            self._pos = {}
            return
        # Use spring layout
        self._pos = nx.spring_layout(self.graph, center=(0,0), scale=20, seed=42)

    # --- Interaction ---

    def on_mouse_down(self, event: events.MouseDown):
        if event.button == 1:
            self._is_dragging = True
            self._drag_start = event.screen_offset
            self._last_mouse_pos = event.offset
            self.capture_mouse()

    def on_mouse_up(self, event: events.MouseUp):
        self._is_dragging = False
        self.release_mouse()

    def on_mouse_move(self, event: events.MouseMove):
        if self._is_dragging and self._last_mouse_pos:
            dx = event.x - self._last_mouse_pos.x
            dy = event.y - self._last_mouse_pos.y
            
            self._center_offset_x += dx
            self._center_offset_y += dy
            self._last_mouse_pos = event.offset
            self.refresh()

    def on_mouse_scroll_down(self, event: events.MouseScrollDown):
        self._zoom = max(0.5, self._zoom * 0.9)
        self.refresh()

    def on_mouse_scroll_up(self, event: events.MouseScrollUp):
        self._zoom = min(50.0, self._zoom * 1.1)
        self.refresh()
        
    def action_zoom_in(self):
        self._zoom *= 1.2
        self.refresh()
        
    def action_zoom_out(self):
        self._zoom *= 0.8
        self.refresh()

    # --- Rendering ---

    def _get_node_style(self, node) -> Style:
        # Determine color based on direct string matching of NodeType enum values or object attributes
        # The node object in networkx might be the Node instance from core.py
        
        # Check if node has 'type' attribute
        ntype = getattr(node, 'type', None)
        
        if ntype == NodeType.IP_V4: return Style(color="yellow", bold=True)
        if ntype == NodeType.IP_V6: return Style(color="red", bold=True)
        if ntype == NodeType.DOMAIN: return Style(color="blue", bold=True)
        if ntype == NodeType.TLD: return Style(color="magenta")
        if ntype == NodeType.SERVICE: return Style(color="green")
        
        return Style(color="white")

    def render_line(self, y: int) -> Strip:
        width = self.size.width
        height = self.size.height
        
        center_x = width // 2 + self._center_offset_x
        center_y = height // 2 + self._center_offset_y
        
        # Prepare this line's segments
        # We will iterate all drawing primitives and see if they intersect this line y.
        # This acts as a "scanline" renderer.
        
        # Buffer for the current line: list of (char, style)
        line_buffer = [(" ", Style()) for _ in range(width)]

        if not self._pos:
            return Strip([Segment(" " * width)])

        scale_x = self._zoom * 2.0
        scale_y = self._zoom
        
        # Helper to transform coords
        def world_to_screen(wx, wy):
            return (int(wx * scale_x + center_x), int(wy * scale_y + center_y))

        # 1. Draw Edges
        # We only draw edges if they cross line y.
        # Using Bresenham logic adapted for scanline:
        # For an edge (x0, y0) -> (x1, y1), does it cross y?
        # If min(y0, y1) <= y <= max(y0, y1), maybe.
        
        # Optimization: Pre-calculate screen coords for all nodes?
        # Doing it every line is somewhat expensive (O(N) * H).
        # But efficiently: N is small (~100-500). H is small (~50).
        # Total ops: 50 * 500 = 25,000 checks. Trivial for Python.
        
        screen_coords = {n: world_to_screen(x, y) for n, (x, y) in self._pos.items()}
        
        edge_style = Style(color="grey50", dim=True)
        edge_char = "·"

        for u, v in self.graph.edges:
            x0, y0 = screen_coords[u]
            x1, y1 = screen_coords[v]
            
            # Check vertical bounds
            if not (min(y0, y1) <= y <= max(y0, y1)):
                continue
                
            # If horizontal, easy
            if y0 == y1 == y:
                start, end = min(x0, x1), max(x0, x1)
                for x in range(start, end + 1):
                    if 0 <= x < width:
                        line_buffer[x] = ("─", edge_style)
                continue

            # General line intersection for row y
            # x = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
            if y1 != y0:
                x = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
                ix = int(x)
                if 0 <= ix < width:
                     line_buffer[ix] = (edge_char, edge_style)

        # 2. Draw Nodes
        # Only if node_y == y
        for node, (sx, sy) in screen_coords.items():
            if sy == y:
                if 0 <= sx < width:
                    style = self._get_node_style(node)
                    line_buffer[sx] = ("●", style)
                    
                    # Label
                    label = str(node.value) if hasattr(node, 'value') else str(node)
                    # Truncate
                    if len(label) > 30: label = label[:27] + "..."
                    
                    for i, char in enumerate(label):
                        if sx + 2 + i < width:
                            line_buffer[sx + 2 + i] = (char, style)

        # Convert buffer to Segments
        # Collapsing adjacent identical styles
        segments = []
        if not line_buffer:
             return Strip([Segment(" " * width)])
             
        current_char, current_style = line_buffer[0]
        current_text = [current_char]
        
        for char, style in line_buffer[1:]:
            if style == current_style:
                current_text.append(char)
            else:
                segments.append(Segment("".join(current_text), current_style))
                current_style = style
                current_text = [char]
        segments.append(Segment("".join(current_text), current_style))
        
        return Strip(segments)
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

