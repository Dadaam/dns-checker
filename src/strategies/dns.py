import dns.resolver
from typing import Generator, Tuple
from src.models.graph import Node, Edge, NodeType, EdgeType
from src.strategies.base import Strategy

class BasicDNSStrategy(Strategy):
    """
    Scanne les enregistrements DNS standard : A, AAAA, MX, NS, CNAME, TXT, SOA.
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
                    target_value = str(rdata).strip('"') # Nettoie les guillemets des TXT
                    
                    # Traitement spécial pour la préférence MX
                    if rtype == 'MX':
                        target_value = str(rdata.exchange).rstrip('.')
                    
                    # Traitement spécial pour le point final CNAME/NS
                    if rtype in ['CNAME', 'NS']:
                        target_value = target_value.rstrip('.')

                    new_node = Node(value=target_value, type=target_node_type)
                    
                    # Si c'est un enregistrement TXT, définir explicitement le type à TXT pour une visualisation différente
                    if rtype == 'TXT':
                         new_node = Node(value=target_value, type=NodeType.TXT)

                    edge = Edge(source=node, target=new_node, type=edge_type)
                    yield new_node, edge
            except Exception:
                continue
