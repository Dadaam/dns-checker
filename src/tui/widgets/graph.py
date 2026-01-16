from collections import defaultdict, deque
from typing import Dict, Iterable, List, Optional, Tuple

import networkx as nx
from rich.segment import Segment
from rich.style import Style
from textual.binding import Binding
from textual.strip import Strip
from textual.widget import Widget

from src.models.graph import NodeType


class GraphWidget(Widget):
    """ASCII graph renderer with colored nodes and directed edges."""

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
        Binding("r", "recompute_layout", "Re-Layout"),
    ]

    def __init__(self, graph: Optional[nx.DiGraph] = None, root=None, name: str = None, id: str = None, classes: str = None):
        super().__init__(name=name, id=id, classes=classes)
        self.graph = graph if graph is not None else nx.DiGraph()
        self.root = root
        self._layout: Dict[object, Tuple[int, int]] = {}
        self._labels: Dict[object, str] = {}
        self._strips: List[Strip] = []
        self._layout_dirty = True
        self._render_dirty = True
        self._layer_gap = 3
        self._max_label_width = 48

    def set_graph(self, graph: nx.DiGraph, root=None):
        self.graph = graph
        if root is not None:
            self.root = root
        self._layout_dirty = True
        self._render_dirty = True
        self.refresh()

    def set_root(self, root):
        self.root = root
        self._layout_dirty = True
        self._render_dirty = True
        self.refresh()

    def recompute_layout(self):
        self._layout_dirty = True
        self._render_dirty = True
        self.refresh()

    def on_resize(self, event) -> None:
        self._layout_dirty = True
        self._render_dirty = True
        self.refresh()

    def action_zoom_in(self):
        self._layer_gap = min(6, self._layer_gap + 1)
        self._render_dirty = True
        self.refresh()

    def action_zoom_out(self):
        self._layer_gap = max(2, self._layer_gap - 1)
        self._render_dirty = True
        self.refresh()

    def action_recompute_layout(self):
        self.recompute_layout()

    def render_line(self, y: int) -> Strip:
        if self._render_dirty or not self._strips:
            self._build_render_cache()
        if y < 0 or y >= len(self._strips):
            return Strip([Segment("")])
        return self._strips[y]

    def _build_render_cache(self):
        width = self.size.width
        height = self.size.height
        if width <= 0 or height <= 0:
            self._strips = [Strip([Segment("")])]
            self._render_dirty = False
            return

        if self._layout_dirty:
            self._layout, self._labels = self._compute_layout(width, height)
            self._layout_dirty = False

        grid = [[(" ", Style()) for _ in range(width)] for _ in range(height)]

        edge_style = Style(color="grey50")
        arrow_style = Style(color="grey70", bold=True)

        for source, target in self.graph.edges:
            if source not in self._layout or target not in self._layout:
                continue
            sx, sy = self._layout[source]
            tx, ty = self._layout[target]
            self._draw_edge(grid, sx, sy, tx, ty, edge_style, arrow_style)

        for node, (x, y) in self._layout.items():
            style = self._node_style(node)
            marker = "O" if node == self.root else "o"
            self._set_cell(grid, x, y, marker, style, force=True)
            label = self._labels.get(node, "")
            if label:
                self._draw_label(grid, x + 2, y, label, style)

        self._strips = [self._row_to_strip(row) for row in grid]
        self._render_dirty = False

    def _compute_layout(self, width: int, height: int) -> Tuple[Dict[object, Tuple[int, int]], Dict[object, str]]:
        nodes = list(self.graph.nodes)
        if not nodes:
            return {}, {}

        layers = self._assign_layers(nodes)
        max_layer = max(layers.values(), default=0)

        layer_gap = max(2, min(self._layer_gap, max(2, (height - 1) // (max_layer + 1))))
        used_height = max_layer * layer_gap + 1
        top_margin = max(0, (height - used_height) // 2)

        by_layer: Dict[int, List[object]] = defaultdict(list)
        for node, layer in layers.items():
            by_layer[layer].append(node)

        for layer_nodes in by_layer.values():
            layer_nodes.sort(key=self._node_sort_key)

        layout: Dict[object, Tuple[int, int]] = {}
        labels: Dict[object, str] = {}

        for layer in range(max_layer + 1):
            layer_nodes = by_layer.get(layer, [])
            if not layer_nodes:
                continue

            count = len(layer_nodes)
            cell_width = max(6, min(self._max_label_width + 2, max(6, width // max(1, count))))
            label_width = max(4, cell_width - 2)

            total_width = cell_width * count
            start_x = max(0, (width - total_width) // 2)
            y = min(height - 1, top_margin + layer * layer_gap)

            for index, node in enumerate(layer_nodes):
                x = start_x + index * cell_width
                layout[node] = (x, y)
                labels[node] = self._node_label(node, label_width)

        return layout, labels

    def _assign_layers(self, nodes: Iterable[object]) -> Dict[object, int]:
        graph = self.graph
        root = self._pick_root(nodes)
        layers: Dict[object, int] = {}

        if root is None:
            return {node: 0 for node in nodes}

        queue = deque([root])
        layers[root] = 0

        while queue:
            node = queue.popleft()
            for _, target in graph.out_edges(node):
                if target not in layers:
                    layers[target] = layers[node] + 1
                    queue.append(target)

        if len(layers) < len(graph.nodes):
            remaining = [n for n in graph.nodes if n not in layers]
            next_layer = max(layers.values(), default=0) + 1
            for node in remaining:
                layers[node] = next_layer

        return layers

    def _pick_root(self, nodes: Iterable[object]):
        if self.root in self.graph:
            return self.root
        nodes = list(nodes)
        if not nodes:
            return None
        try:
            return min(nodes, key=lambda n: (self.graph.in_degree(n), self._node_sort_key(n)))
        except Exception:
            return nodes[0]

    def _node_sort_key(self, node) -> Tuple[int, str]:
        ntype = getattr(node, "type", None)
        type_rank = {
            NodeType.DOMAIN: 0,
            NodeType.TLD: 1,
            NodeType.SERVICE: 2,
            NodeType.IP_V4: 3,
            NodeType.IP_V6: 4,
        }
        rank = type_rank.get(ntype, 99)
        value = getattr(node, "value", str(node))
        return rank, value

    def _node_label(self, node, max_width: int) -> str:
        label = getattr(node, "value", str(node))
        if len(label) <= max_width:
            return label
        if max_width <= 6:
            return label[:max_width]
        head = (max_width - 3) // 2
        tail = max_width - 3 - head
        return f"{label[:head]}...{label[-tail:]}"

    def _node_style(self, node) -> Style:
        ntype = getattr(node, "type", None)
        if ntype == NodeType.IP_V4:
            return Style(color="yellow", bold=True)
        if ntype == NodeType.IP_V6:
            return Style(color="red", bold=True)
        if ntype == NodeType.DOMAIN:
            return Style(color="bright_blue", bold=True)
        if ntype == NodeType.TLD:
            return Style(color="magenta")
        if ntype == NodeType.SERVICE:
            return Style(color="green")
        return Style(color="white")

    def _draw_edge(self, grid, sx: int, sy: int, tx: int, ty: int, style: Style, arrow_style: Style):
        if sx == tx and sy == ty:
            return

        if sy == ty:
            if sx < tx:
                self._draw_horizontal(grid, sy, sx + 1, tx - 1, style)
                self._set_cell(grid, tx - 1, sy, ">", arrow_style, force=True)
            else:
                self._draw_horizontal(grid, sy, tx + 1, sx - 1, style)
                self._set_cell(grid, tx + 1, sy, "<", arrow_style, force=True)
            return

        if sy < ty:
            bend_y = ty - 1
            self._draw_vertical(grid, sx, sy + 1, bend_y, style)
            self._draw_horizontal(grid, bend_y, sx, tx, style)
            self._set_cell(grid, tx, bend_y, "v", arrow_style, force=True)
            return

        bend_y = ty + 1
        self._draw_vertical(grid, sx, sy - 1, bend_y, style)
        self._draw_horizontal(grid, bend_y, sx, tx, style)
        self._set_cell(grid, tx, bend_y, "^", arrow_style, force=True)

    def _draw_horizontal(self, grid, y: int, x1: int, x2: int, style: Style):
        if y < 0 or y >= len(grid):
            return
        start = min(x1, x2)
        end = max(x1, x2)
        for x in range(start, end + 1):
            self._merge_line(grid, x, y, "=", style)

    def _draw_vertical(self, grid, x: int, y1: int, y2: int, style: Style):
        if x < 0 or x >= len(grid[0]):
            return
        start = min(y1, y2)
        end = max(y1, y2)
        for y in range(start, end + 1):
            self._merge_line(grid, x, y, "|", style)

    def _draw_label(self, grid, x: int, y: int, label: str, style: Style):
        if y < 0 or y >= len(grid):
            return
        width = len(grid[0])
        for i, ch in enumerate(label):
            px = x + i
            if 0 <= px < width:
                self._set_cell(grid, px, y, ch, style, force=True)

    def _merge_line(self, grid, x: int, y: int, char: str, style: Style):
        if y < 0 or y >= len(grid):
            return
        if x < 0 or x >= len(grid[0]):
            return
        existing_char, existing_style = grid[y][x]
        if existing_char in ("<", ">", "^", "v"):
            return
        merged = self._merge_line_char(existing_char, char)
        grid[y][x] = (merged, style)

    def _merge_line_char(self, existing: str, new: str) -> str:
        if existing == " ":
            return new
        if existing in ("=", "|") and new in ("=", "|") and existing != new:
            return "+"
        if existing == "+" or new == "+":
            return "+"
        if existing in ("=", "|") and new == existing:
            return existing
        return existing

    def _set_cell(self, grid, x: int, y: int, char: str, style: Style, force: bool = False):
        if y < 0 or y >= len(grid):
            return
        if x < 0 or x >= len(grid[0]):
            return
        existing_char, existing_style = grid[y][x]
        if force or existing_char == " ":
            grid[y][x] = (char, style)

    def _row_to_strip(self, row) -> Strip:
        if not row:
            return Strip([Segment("")])
        segments: List[Segment] = []
        current_char, current_style = row[0]
        current_text = [current_char]
        for char, style in row[1:]:
            if style == current_style:
                current_text.append(char)
            else:
                segments.append(Segment("".join(current_text), current_style))
                current_style = style
                current_text = [char]
        segments.append(Segment("".join(current_text), current_style))
        return Strip(segments)
