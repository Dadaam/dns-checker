import tldextract
from typing import Generator, Tuple
from src.models.graph import Node, Edge, NodeType, EdgeType
from src.strategies.base import Strategy

class ParentStrategy(Strategy):
    """
    Deduces parent domains (crawl to TLD).
    e.g. sub.example.com -> example.com -> com (stop before TLD)
    """
    def execute(self, node: Node) -> Generator[Tuple[Node, Edge], None, None]:
        if node.type != NodeType.DOMAIN:
            return

        domain = node.value
        extracted = tldextract.extract(domain)
        
        # Reconstruct the registrable domain (e.g. example.com)
        registered_domain = extracted.registered_domain
        
        # If current node is the registered domain, we might stop or go to TLD?
        # User said "ne pas scanner le TLD public lui-même".
        # So we scan until we hit the registered domain.
        
        if not registered_domain:
            return

        # If we are deeper than registered domain, strip one level
        # e.g. a.b.example.com -> b.example.com
        if domain != registered_domain and domain.endswith(registered_domain):
            parts = domain.split('.')
            parent = '.'.join(parts[1:])
            
            if parent:
                new_node = Node(value=parent, type=NodeType.DOMAIN)
                edge = Edge(source=node, target=new_node, type=EdgeType.PARENT)
                yield new_node, edge
