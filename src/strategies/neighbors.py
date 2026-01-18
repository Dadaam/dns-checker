import dns.reversename
import dns.resolver
import ipaddress
from typing import Generator, Tuple
from src.models.graph import Node, Edge, NodeType, EdgeType
from src.strategies.base import Strategy

class NeighborStrategy(Strategy):
    """
    Vérifie les voisins IP contigus (+1/-1).
    Les valide via une recherche PTR principalement.
    """
    def __init__(self):
        self.resolver = dns.resolver.Resolver()
        self.resolver.lifetime = 1.0 # Court délai pour les voisins

    def execute(self, node: Node) -> Generator[Tuple[Node, Edge], None, None]:
        if node.type != NodeType.IP_V4:
            return

        try:
            ip_obj = ipaddress.IPv4Address(node.value)
            # Voisins naïfs : +1 et -1
            # Nous devons faire attention à ne pas générer d'IP invalides ou broadcast/réseau
            neighbors = []
            if ip_obj > ipaddress.IPv4Address("0.0.0.0"):
                neighbors.append(ip_obj - 1)
            if ip_obj < ipaddress.IPv4Address("255.255.255.255"):
                neighbors.append(ip_obj + 1)

            for neighbor_ip in neighbors:
                neighbor_str = str(neighbor_ip)
                
                # Logique de vérification : Ce voisin a-t-il un PTR ?
                # Si oui, c'est un nœud valide à ajouter.
                try:
                    addr = dns.reversename.from_address(neighbor_str)
                    _ = self.resolver.resolve(addr, "PTR")
                    
                    # Si le PTR existe, nous le traitons comme un voisin trouvé
                    new_node = Node(value=neighbor_str, type=NodeType.IP_V4)
                    edge = Edge(source=node, target=new_node, type=EdgeType.NEIGHBOR)
                    yield new_node, edge
                except Exception:
                    # Pas de PTR, ou délai dépassé -> supposé inintéressant pour l'instant
                    continue
        except Exception:
            pass
