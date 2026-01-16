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
        self.fitToScreen()
        self.update()

    def recomputeLayout(self):
        if not self._graph.nodes:
            self._pos = {}
            return
        # Use a normalized scale since we handle zoom in rendering
        # spring_layout returns positions roughly in [-1, 1] if scale=1
        try:
            self._pos = nx.spring_layout(self._graph, center=(0,0), scale=1, k=0.5, seed=42)
        except Exception:
             self._pos = nx.spring_layout(self._graph, center=(0,0), scale=1, seed=42)

    def fitToScreen(self):
        # Auto-zoom to fit nodes
        if not self._pos: return
        w, h = self.size()
        
        # Find min/max
        xs = [x for x,y in self._pos.values()]
        ys = [y for x,y in self._pos.values()]
        
        if not xs: return
        
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        
        span_x = (max_x - min_x) if max_x != min_x else 1
        span_y = (max_y - min_y) if max_y != min_y else 1
        
        # We want span * zoom * 2 < w  (extra factor for text)
        # We want span * zoom < h
        
        zoom_x = (w / 2.5) / span_x
        zoom_y = (h / 1.5) / span_y
        
        self._zoom = min(zoom_x, zoom_y)
        self._offset_x = 0
        self._offset_y = 0

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
        
        # Aspect ratio correction: terminal chars are ~2x taller than wide
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

        # Draw Directed Edges
        edge_color = TTkColor.fg("#444444")
        arrow_color = TTkColor.fg("#AAAAAA")
        
        for u, v in self._graph.edges:
            if u not in screen_coords or v not in screen_coords: continue
            
            x0, y0 = screen_coords[u]
            x1, y1 = screen_coords[v]
            
            # Draw line
            self._draw_line(canvas, x0, y0, x1, y1, w, h, edge_color)
            
            # Draw Arrow at MIDPOINT to avoid clutter
            mx = (x0 + x1) // 2
            my = (y0 + y1) // 2
            
            # Add a small offset towards target to indicate direction?
            # Or just use the arrow char.
            
            dx = x1 - x0
            dy = y1 - y0
            
            char = '>' if dx > 0 else '<'
            if abs(dy) > abs(dx): # Vertical-ish
                char = 'v' if dy > 0 else '^'
            
            if 0 <= mx < w and 0 <= my < h:
                 canvas.drawChar(pos=(mx, my), char=char, color=arrow_color)

        # Draw Nodes
        for node, (sx, sy) in screen_coords.items():
            if 0 <= sx < w and 0 <= sy < h:
                color = self._get_node_color(node)
                label = str(node.value) if hasattr(node, 'value') else str(node)
                
                # Draw marker
                canvas.drawChar(pos=(sx, sy), char='●', color=color)
                
                # Draw label
                if sx + 2 < w:
                    canvas.drawText(pos=(sx + 2, sy), text=label, color=color)
        
        # Debug Info
        # canvas.drawText(pos=(0,0), text=f"Zoom: {self._zoom:.2f} Offset: {self._offset_x},{self._offset_y}", color=TTkColor.fg("#FFFFFF"))

    def _draw_line(self, canvas, x0, y0, x1, y1, w, h, color):
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        steps = 0
        limit = max(w, h) * 2 # Safety break
        
        curr_x, curr_y = x0, y0
        
        while steps < limit:
            if 0 <= curr_x < w and 0 <= curr_y < h:
                 # Don't overwrite nodes ideally. simple check?
                 # Canvas usually handles Z-order by draw order.
                 # Draw dim line
                 canvas.drawChar(pos=(curr_x, curr_y), char='·', color=color)
            
            if curr_x == x1 and curr_y == y1: break
            
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                curr_x += sx
            if e2 < dx:
                err += dx
                curr_y += sy
            steps += 1

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
        return True # Swallow event

    def mouseReleaseEvent(self, evt: TTkMouseEvent) -> bool:
        self._is_dragging = False
        return True

    def wheelEvent(self, evt: TTkMouseEvent) -> bool:
        # Check event type properly for TermTk 
        if evt.evt == TTkMouseEvent.Wheel:
            if evt.key == TTkMouseEvent.WheelUp:
                 self._zoom *= 1.2
            elif evt.key == TTkMouseEvent.WheelDown:
                 self._zoom *= 0.8
            self.update()
            return True
        return False

