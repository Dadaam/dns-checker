import dns.resolver
from typing import Generator, Tuple
from src.models.graph import Node, Edge, NodeType, EdgeType
from src.strategies.base import Strategy

class BasicDNSStrategy(Strategy):
    """
    Scans for standard DNS records: A, AAAA, MX, NS, CNAME, TXT, SOA.
    """
    RECORD_TYPES = {
        'A': (NodeType.IP_V4, EdgeType.A),
        'AAAA': (NodeType.IP_V6, EdgeType.AAAA),
        'CNAME': (NodeType.DOMAIN, EdgeType.CNAME),
        'NS': (NodeType.DOMAIN, EdgeType.NS),
        'MX': (NodeType.DOMAIN, EdgeType.MX),
        'TXT': (NodeType.TXT, EdgeType.TXT),
    }

    def __init__(self):
        self.resolver = dns.resolver.Resolver()
        self.resolver.lifetime = 1.0

    def execute(self, node: Node) -> Generator[Tuple[Node, Edge], None, None]:
        if node.type != NodeType.DOMAIN:
            return

        for rtype, (target_node_type, edge_type) in self.RECORD_TYPES.items():
            try:
                answers = self.resolver.resolve(node.value, rtype)
                for rdata in answers:
                    target_value = str(rdata).strip('"') # Clean quotes from TXT
                    
                    # Special handling for MX preference
                    if rtype == 'MX':
                        target_value = str(rdata.exchange).rstrip('.')
                    
                    # Special handling for CNAME/NS trailing dot
                    if rtype in ['CNAME', 'NS']:
                        target_value = target_value.rstrip('.')

                    new_node = Node(value=target_value, type=target_node_type)
                    
                    # If it's a TXT record, explicitly set the type to TXT so it can be visualized differently
                    if rtype == 'TXT':
                         new_node = Node(value=target_value, type=NodeType.TXT)

                    edge = Edge(source=node, target=new_node, type=edge_type)
                    yield new_node, edge
            except Exception:
                continue
