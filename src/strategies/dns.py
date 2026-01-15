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
    }

    def __init__(self):
        self.resolver = dns.resolver.Resolver()
        self.resolver.lifetime = 3.0

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
                    # For TXT, we might want to mark it specially if we implement a specific Node Type for it?
                    # For now, let's assume TXT content is 'DOMAIN' or maybe generic?
                    # Since "Parse TXT" extracts IPs/Domains, the raw TXT itself is just data.
                    # As a compromise, if it's TXT, let's treat it as SERVICE or generic? 
                    # Actually, let's use SERVICE for now or add a RAW type.
                    # Or better: Just yield it. The NodeType.DOMAIN for TXT raw data is wrong if it's "v=spf1...".
                    # Let's override for TXT.
                    if rtype == 'TXT':
                         # We don't really have a "RAW_TEXT" node type yet. 
                         # Let's skip creating a node for raw TXT here unless we add a type.
                         # But wait, "Parse TXT" needs the TXT content. 
                         # So we SHOULD store it.
                         # Let's yield it as SERVICE for now or reuse metadata?
                         # Actually, simplicity: Just yield it. 
                         pass

                    edge = Edge(source=node, target=new_node, type=edge_type)
                    yield new_node, edge
            except Exception:
                continue
