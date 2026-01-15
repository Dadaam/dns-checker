import dns.resolver
import re
from typing import Generator, Tuple
from src.models.graph import Node, Edge, NodeType, EdgeType
from src.strategies.base import Strategy

class TxtStrategy(Strategy):
    """
    Fetches and parses TXT records (SPF, DMARC, etc.) to extract hidden IPs and Domains.
    """
    
    # Regexes for common patterns
    REGEX_IPV4 = r"ip4:(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"
    REGEX_IPV6 = r"ip6:([a-fA-F0-9:]+)"
    REGEX_INCLUDE = r"include:([a-zA-Z0-9.-]+)"
    REGEX_REDIRECT = r"redirect=([a-zA-Z0-9.-]+)"
    # A simple broad domain regex might match too much garbage in base64 strings, 
    # so we focus on structural prefixes like include/redirect/ptr/mx mechanisms in SPF.
    
    def __init__(self):
        self.resolver = dns.resolver.Resolver()

    def execute(self, node: Node) -> Generator[Tuple[Node, Edge], None, None]:
        if node.type != NodeType.DOMAIN:
            return

        try:
            answers = self.resolver.resolve(node.value, "TXT")
            for rdata in answers:
                txt_content = str(rdata).strip('"')
                
                # Scan for IPv4
                for ip in re.findall(self.REGEX_IPV4, txt_content):
                    new_node = Node(value=ip, type=NodeType.IP_V4)
                    edge = Edge(source=node, target=new_node, type=EdgeType.TXT)
                    yield new_node, edge
                    
                # Scan for IPv6
                for ip in re.findall(self.REGEX_IPV6, txt_content):
                    new_node = Node(value=ip, type=NodeType.IP_V6)
                    edge = Edge(source=node, target=new_node, type=EdgeType.TXT)
                    yield new_node, edge

                # Scan for Domains (include/redirect)
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
