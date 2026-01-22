import dns.resolver
import re
from typing import Generator, Tuple
from src.models.graph import Node, Edge, NodeType, EdgeType
from src.strategies.base import Strategy

class TxtStrategy(Strategy):
    """
    Récupère et analyse les enregistrements TXT (SPF, DMARC, etc.) pour extraire des IP et domaines cachés.
    """
    
    # Regex pour les motifs courants
    REGEX_IPV4 = r"ip4:(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
    REGEX_IPV6 = r"ip6:([a-fA-F0-9:]+)"
    REGEX_INCLUDE = r"include:([a-zA-Z0-9._-]+)"
    REGEX_REDIRECT = r"redirect=([a-zA-Z0-9._-]+)"
    # Une regex de domaine simple et large pourrait correspondre à trop de déchets dans les chaînes base64, 
    # donc nous nous concentrons sur des préfixes structurels comme les mécanismes include/redirect/ptr/mx dans SPF.
    
    def __init__(self):
        self.resolver = dns.resolver.Resolver()
        self.resolver.lifetime = 2.0

    def execute(self, node: Node) -> Generator[Tuple[Node, Edge], None, None]:
        if node.type != NodeType.DOMAIN:
            return

        try:
            answers = self.resolver.resolve(node.value, "TXT")
            for rdata in answers:
                txt_content = str(rdata).strip('"')
                
                # Scan pour IPv4
                for ip in re.findall(self.REGEX_IPV4, txt_content):
                    new_node = Node(value=ip, type=NodeType.IP_V4)
                    edge = Edge(source=node, target=new_node, type=EdgeType.TXT)
                    yield new_node, edge
                    
                # Scan pour IPv6
                for ip in re.findall(self.REGEX_IPV6, txt_content):
                    new_node = Node(value=ip, type=NodeType.IP_V6)
                    edge = Edge(source=node, target=new_node, type=EdgeType.TXT)
                    yield new_node, edge

                # Scan pour Domaines (include/redirect)
                for domain in re.findall(self.REGEX_INCLUDE, txt_content):
                    new_node = Node(value=domain, type=NodeType.DOMAIN)
                    edge = Edge(source=node, target=new_node, type=EdgeType.TXT)
                    yield new_node, edge

                for domain in re.findall(self.REGEX_REDIRECT, txt_content):
                    new_node = Node(value=domain, type=NodeType.DOMAIN)
                    edge = Edge(source=node, target=new_node, type=EdgeType.TXT)
                    yield new_node, edge

        except Exception:
            pass
