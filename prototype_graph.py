from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Static
from textual.binding import Binding
from textual.reactive import reactive
from textual.color import Color
import networkx as nx
from rich.segment import Segment
from rich.style import Style
from textual.strip import Strip
from textual.widget import Widget
from textual.geometry import Size
import math

class GraphWidget(Widget):
    """
    A widget to display a NetworkX graph with force-directed layout.
    """
    
    # Allow the widget to focus to receive scroll events if needed
    can_focus = True

    def __init__(self, graph: nx.Graph, **kwargs):
        super().__init__(**kwargs)
        self.graph = graph
        # Compute layout once (or update later)
        # Spring layout centers around (0,0) by default
        self.pos = nx.spring_layout(self.graph, center=(0,0), scale=20) 
        
        # simple scale factor to map graph units to terminal cells
        self.zoom = 1.0
        self.offset_x = 0
        self.offset_y = 0

    def render_block(self, y: int, x: int) -> str:
        # Check if any node is here
        # This is very inefficient (O(N) per cell), for prototype only
        # In real app, we would cache positions to a grid
        for node, (nx_x, nx_y) in self.pos.items():
            # Transform content to screen coords
            screen_x = int(nx_x * 2 + self.size.width / 2) # *2 for character aspect ratio
            screen_y = int(nx_y + self.size.height / 2)
            
            if screen_x == x and screen_y == y:
                return "O"
        return " "

    def render_line(self, y: int) -> Strip:
        width = self.size.width
        
        # We'll build the strip manually
        segments = []
        
        # Optimize: Pre-calculate node positions on screen
        screen_positions = {}
        for node, (nx_x, nx_y) in self.pos.items():
            screen_x = int(nx_x * 3.0 + width // 2) # X scale
            screen_y = int(nx_y * 1.5 + self.size.height // 2) # Y scale
            screen_positions[node] = (screen_x, screen_y)

        # Draw line by line? No, Textual renders line by line via render_line
        # So for row 'y', we need to produce 'width' cells.
        
        line_chars = [" "] * width
        
        # 1. Draw Edges (Bresenham-ish)
        # This acts on the whole buffer, which we don't have access to line-by-line easily without overhead
        # For this prototype, let's just draw nodes. 
        # Drawing lines per scanline is tricky.
        # Actually, let's just simple-check if a line passes through.
        
        # Better approach for TUI:
        # Use a `Canvas` approach (rich.canvas is deprecated/removed). 
        # We can implement a simple buffer.
        
        # Let's keep it simple: Just draw nodes first.
        
        for node, (sx, sy) in screen_positions.items():
            if sy == y:
                if 0 <= sx < width:
                    # Simple node
                    line_chars[sx] = "O"
                    # Label (if space)
                    label = str(node)
                    if sx + 1 + len(label) < width:
                        for i, char in enumerate(label):
                            line_chars[sx + 1 + i] = char

        # Convert to segments
        text = "".join(line_chars)
        return Strip([Segment(text)])

class PrototypeApp(App):
    CSS = """
    GraphWidget {
        width: 100%;
        height: 100%;
        border: solid green;
    }
    """
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        # Create a sample graph
        G = nx.Graph()
        G.add_edge("Root", "A")
        G.add_edge("Root", "B")
        G.add_edge("A", "A1")
        G.add_edge("A", "A2")
        G.add_edge("B", "B1")
        
        yield GraphWidget(G)
        yield Footer()

if __name__ == "__main__":
    app = PrototypeApp()
    app.run()
