import dns.resolver
from typing import Generator, Tuple
from src.models.graph import Node, Edge, NodeType, EdgeType
from src.strategies.base import Strategy

class SrvStrategy(Strategy):
    """
    Brute-force les enregistrements SRV courants pour trouver des services.
    """
    
    COMMON_SERVICES = [
        '_xmpp-server._tcp',
        '_xmpp-client._tcp',
        '_sip._tcp',
        '_sip._udp',
        '_ldap._tcp',
        '_kerberos._tcp',
        '_kerberos._udp',
        '_minecraft._tcp',
        '_autodiscover._tcp',
        '_caldav._tcp',
        '_carddav._tcp'
    ]

    def __init__(self):
        self.resolver = dns.resolver.Resolver()

    def execute(self, node: Node) -> Generator[Tuple[Node, Edge], None, None]:
        if node.type != NodeType.DOMAIN:
            return

        for service in self.COMMON_SERVICES:
            target = f"{service}.{node.value}"
            try:
                answers = self.resolver.resolve(target, "SRV")
                for rdata in answers:
                    # Contenu de l'enregistrement SRV : priorité poids port cible
                    # Nous sommes intéressés par le domaine cible et le port.
                    
                    target_domain = str(rdata.target).rstrip('.')
                    port = rdata.port
                    
                    # Générer le domaine de service découvert
                    new_node = Node(value=target_domain, type=NodeType.DOMAIN)
                    edge = Edge(source=node, target=new_node, type=EdgeType.SRV)
                    yield new_node, edge
                    
                    # On pourrait aussi générer un nœud "Service" comme "_xmpp-server._tcp.example.com"
                    # pointant vers "xmpp.example.com", mais le graphe pourrait devenir encombré.
                    
            except Exception:
                continue
