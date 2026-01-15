import dns.resolver
from typing import Generator, Tuple
from src.models.graph import Node, Edge, NodeType, EdgeType
from src.strategies.base import Strategy

class SrvStrategy(Strategy):
    """
    Brute-forces common SRV records to find services.
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
                    # SRV record content: priority weight port target
                    # We are interested in the target domain and port.
                    # We can represent this as a SERVICE node? Or just the target domain?
                    # "target" in SRV is a domain name.
                    
                    target_domain = str(rdata.target).rstrip('.')
                    port = rdata.port
                    
                    # Yield the discovered service domain
                    new_node = Node(value=target_domain, type=NodeType.DOMAIN)
                    edge = Edge(source=node, target=new_node, type=EdgeType.SRV)
                    yield new_node, edge
                    
                    # We could also arguably yield a "Service" node like "_xmpp-server._tcp.example.com"
                    # pointing to "xmpp.example.com", but the graph might get cluttered.
                    # The prompt asks for "Noeuds... Domaines, IPs, TLDs".
                    # So linking Domain -> Target Domain via SRV edge is good.
                    
            except Exception:
                continue
