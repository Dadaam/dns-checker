import tldextract
from typing import Generator, Tuple
from src.models.graph import Node, Edge, NodeType, EdgeType
from src.strategies.base import Strategy

class ParentStrategy(Strategy):
    """
    Déduit les domaines parents (remonte vers le TLD).
    ex: sub.example.com -> example.com -> com (s'arrête avant le TLD)
    """
    def execute(self, node: Node) -> Generator[Tuple[Node, Edge], None, None]:
        if node.type != NodeType.DOMAIN:
            return

        domain = node.value
        extracted = tldextract.extract(domain)
        
        # Reconstruit le domaine enregistrable (par ex. example.com)
        registered_domain = extracted.registered_domain
        
        # Si le nœud actuel est le domaine enregistré, doit-on s'arrêter ou aller au TLD ?
        # L'utilisateur a dit "ne pas scanner le TLD public lui-même".
        # Donc nous scannons jusqu'à atteindre le domaine enregistré.
        
        if not registered_domain:
            return

        # Si nous sommes plus profond que le domaine enregistré, retirer un niveau
        # ex: a.b.example.com -> b.example.com
        if domain != registered_domain and domain.endswith(registered_domain):
            parts = domain.split('.')
            parent = '.'.join(parts[1:])
            
            if parent:
                new_node = Node(value=parent, type=NodeType.DOMAIN)
                edge = Edge(source=node, target=new_node, type=EdgeType.PARENT)
                yield new_node, edge
