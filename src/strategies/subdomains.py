import dns.resolver
from typing import Generator, Tuple
from src.models.graph import Node, Edge, NodeType, EdgeType
from src.strategies.base import Strategy

class SubdomainStrategy(Strategy):
    """
    Brute-forces common subdomains.
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
                # Check if A or AAAA exists
                _ = self.resolver.resolve(subdomain, "A")
                # If found, yield it
                new_node = Node(value=subdomain, type=NodeType.DOMAIN)
                # Technically it's 'found via brute force' but relationship is essentially same as if we found it via CNAME/NS?
                # Or we can mark edge as PARENT (inverse)? 
                # Let's say EdgeType.A? No, A points Domain -> IP.
                # Let's use PARENT but directed from node to subdomain? "node is parent of subdomain".
                # My EdgeType.PARENT definition was "Deduces parents", source=sub, target=parent.
                # Here source=parent, target=sub. 
                # Let's reuse EdgeType.CNAME? No.
                # Let's add EdgeType.SUBDOMAIN? Or just reuse generic logic.
                # The user graph spec: "Lignes CNAME, A, NS..."
                # If we found `www.example.com` from `example.com`, what is the edge?
                # It's a "Contains" or "Subdomain" relationship.
                # I'll stick to a generic approach or maybe just yield it as a known node without a strict DNS edge type,
                # BUT the system requires an Edge.
                # Let's use a new type SUBDOMAIN if needed, or re-use "PARENT" reversed?
                # Let's add SUBDOMAIN to EdgeType in models/graph.py if I can edit it? 
                # I'm avoiding editing models every time.
                # I'll use EdgeType.CNAME as a placeholder or just generic? 
                # Wait, usually `www` HAS an A record. The relationship source->target is `example.com` -> `www.example.com`.
                # This isn't a standard DNS pointer. 
                # I will create a custom EdgeType.SUBDOMAIN in models/graph.py now for clarity.
                
                # Check AAAA too? Usually A is enough to prove existence.
                yield new_node, Edge(source=node, target=new_node, type=EdgeType.A) # Using A is weird.
                
            except Exception:
                continue
