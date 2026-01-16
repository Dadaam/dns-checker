from TermTk import TTkWidget, TTkColor, TTkCanvas
from TermTk import TTkLog, TTkK, TTkMouseEvent
import networkx as nx
import math
from src.models.graph import NodeType

class TTkGraphWidget(TTkWidget):
    __slots__ = ('_graph', '_pos', '_zoom', '_offset_x', '_offset_y', '_drag_start', '_is_dragging')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._graph = nx.Graph()
        self._pos = {}
        
        # Viewport
        self._zoom = 10.0
        self._offset_x = 0
        self._offset_y = 0
        
        self._drag_start = None
        self._is_dragging = False
        
        self.setFocusPolicy(TTkK.ClickFocus)

    def setGraph(self, graph: nx.Graph):
        self._graph = graph
        self.recomputeLayout()
        self.update()

    def recomputeLayout(self):
        if not self._graph.nodes:
            self._pos = {}
            return
        # Force directed layout
        self._pos = nx.spring_layout(self._graph, center=(0,0), scale=1, seed=42)

    def _get_node_color(self, node):
        ntype = getattr(node, 'type', None)
        if ntype == NodeType.IP_V4: return TTkColor.fg("#FFFF00") # Yellow
        if ntype == NodeType.IP_V6: return TTkColor.fg("#FF0000") # Red
        if ntype == NodeType.DOMAIN: return TTkColor.fg("#0088FF") # Blue
        if ntype == NodeType.TLD: return TTkColor.fg("#FF00FF") # Magenta
        if ntype == NodeType.SERVICE: return TTkColor.fg("#00FF00") # Green
        return TTkColor.RST

    def paintEvent(self, canvas: TTkCanvas):
        w, h = self.size()
        center_x = w // 2 + self._offset_x
        center_y = h // 2 + self._offset_y
        
        scale_x = self._zoom * 2.0
        scale_y = self._zoom
        
        if not self._pos:
            canvas.drawText(pos=(w//2 - 5, h//2), text="No Data", color=TTkColor.fg("#888888"))
            return

        # Pre-calc screen coords
        screen_coords = {}
        for node, (nx_x, nx_y) in self._pos.items():
            screen_coords[node] = (
                int(nx_x * scale_x + center_x),
                int(nx_y * scale_y + center_y)
            )

        # Draw Edges
        # Canvas.drawLine is likely not available or robust in all versions, 
        # but let's check basic chars.
        # We'll use a simple Bresenham char drawer or just draw grid points if we want to be safe,
        # but the user wants links. simple bresenham is best.
        
        edge_color = TTkColor.fg("#666666")
        
        # Sort edges by depth? Nah.
        for u, v in self._graph.edges:
            if u not in screen_coords or v not in screen_coords: continue
            
            x0, y0 = screen_coords[u]
            x1, y1 = screen_coords[v]
            
            # Simple line drawing logic (Bresenham)
            dx = abs(x1 - x0)
            dy = abs(y1 - y0)
            sx = 1 if x0 < x1 else -1
            sy = 1 if y0 < y1 else -1
            err = dx - dy
            
            while True:
                if 0 <= x0 < w and 0 <= y0 < h:
                     # Don't overwrite nodes ideally, but we draw nodes later so it's fine
                     canvas.drawChar(pos=(x0, y0), char='·', color=edge_color)
                
                if x0 == x1 and y0 == y1: break
                
                e2 = 2 * err
                if e2 > -dy:
                    err -= dy
                    x0 += sx
                if e2 < dx:
                    err += dx
                    y0 += sy

        # Draw Nodes
        for node, (sx, sy) in screen_coords.items():
            if 0 <= sx < w and 0 <= sy < h:
                color = self._get_node_color(node)
                label = str(node.value) if hasattr(node, 'value') else str(node)
                
                # Draw marker
                canvas.drawChar(pos=(sx, sy), char='●', color=color)
                
                # Draw label
                # Avoid drawing off-screen
                if sx + 2 < w:
                    canvas.drawText(pos=(sx + 2, sy), text=label, color=color)

    # Mouse Interaction
    def mousePressEvent(self, evt: TTkMouseEvent) -> bool:
        if evt.key == TTkMouseEvent.LeftButton:
            self._is_dragging = True
            self._drag_start = (evt.x, evt.y)
            return True
        return False

    def mouseDragEvent(self, evt: TTkMouseEvent) -> bool:
        if self._is_dragging:
            dx = evt.x - self._drag_start[0]
            dy = evt.y - self._drag_start[1]
            self._offset_x += dx
            self._offset_y += dy
            self._drag_start = (evt.x, evt.y)
            self.update()
            return True
        return False

    def mouseReleaseEvent(self, evt: TTkMouseEvent) -> bool:
        self._is_dragging = False
        return True

    def wheelEvent(self, evt: TTkMouseEvent) -> bool:
        if evt.evt == TTkMouseEvent.Wheel:
            # Check delta (how TTk handles this varies, mostly evt.key is UP/DOWN)
            if evt.key == TTkMouseEvent.WheelUp:
                 self._zoom *= 1.1
            elif evt.key == TTkMouseEvent.WheelDown:
                 self._zoom *= 0.9
            self.update()
            return True
        return False
