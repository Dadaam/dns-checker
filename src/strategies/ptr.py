import dns.reversename
import dns.resolver
from typing import Generator, Tuple
from src.models.graph import Node, Edge, NodeType, EdgeType
from src.strategies.base import Strategy

class PtrStrategy(Strategy):
    """
    Effectue des recherches DNS inversées (PTR) sur les adresses IP.
    """
    def __init__(self):
        self.resolver = dns.resolver.Resolver()
        self.resolver.lifetime = 2.0

    def execute(self, node: Node) -> Generator[Tuple[Node, Edge], None, None]:
        if node.type not in [NodeType.IP_V4, NodeType.IP_V6]:
            return

        try:
            addr = dns.reversename.from_address(node.value)
            answers = self.resolver.resolve(addr, "PTR")
            for rdata in answers:
                hostname = str(rdata).rstrip('.')
                new_node = Node(value=hostname, type=NodeType.DOMAIN)
                edge = Edge(source=node, target=new_node, type=EdgeType.PTR)
                yield new_node, edge
        except Exception:
            pass
