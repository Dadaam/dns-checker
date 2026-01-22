import dns.resolver
from typing import Generator, Tuple
from src.models.graph import Node, Edge, NodeType, EdgeType
from src.strategies.base import Strategy

class SubdomainStrategy(Strategy):
    """
    Brute-force les sous-domaines courants.
    """
    
    PREFIXES = [
        'www', 'api', 'dev', 'test', 'staging', 'mail', 
        'vpn', 'remote', 'gateway', 'admin', 'portal',
        'ns1', 'ns2', 'smtp', 'pop', 'imap', 'secure',
        'blog', 'shop', 'store', 'app', 'm'
    ]

    def __init__(self):
        self.resolver = dns.resolver.Resolver()
        self.resolver.lifetime = 1.5

    def execute(self, node: Node) -> Generator[Tuple[Node, Edge], None, None]:
        if node.type != NodeType.DOMAIN:
            return

        for prefix in self.PREFIXES:
            subdomain = f"{prefix}.{node.value}"
            try:
                # Vérifier si A ou AAAA existe
                _ = self.resolver.resolve(subdomain, "A")
                # Si trouvé, le générer
                new_node = Node(value=subdomain, type=NodeType.DOMAIN)
                # Techniquement c'est 'trouvé via brute force' mais la relation est essentiellement la même que si trouvé via CNAME/NS
                # On créer un EdgeType.SUBDOMAIN personnalisé pour la clarté car c'est pas exactement un parent
                
                # On peut Vérifier AAAA aussi ? Généralement A suffit pour prouver l'existence.
                yield new_node, Edge(source=node, target=new_node, type=EdgeType.SUBDOMAIN)
                
            except Exception:
                continue
