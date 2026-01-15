import dns.reversename
import dns.resolver
import ipaddress
from typing import Generator, Tuple
from src.models.graph import Node, Edge, NodeType, EdgeType
from src.strategies.base import Strategy

class NeighborStrategy(Strategy):
    """
    Checks for contiguous IP neighbors (+1/-1).
    Validates them via PTR lookup primarily.
    """
    def __init__(self):
        self.resolver = dns.resolver.Resolver()
        self.resolver.lifetime = 1.0 # Short timeout for neighbors

    def execute(self, node: Node) -> Generator[Tuple[Node, Edge], None, None]:
        if node.type != NodeType.IP_V4:
            return

        try:
            ip_obj = ipaddress.IPv4Address(node.value)
            # Naive neighbors: +1 and -1
            # We must be careful not to generate invalid IPs or broadcast/network
            neighbors = []
            if ip_obj > ipaddress.IPv4Address("0.0.0.0"):
                neighbors.append(ip_obj - 1)
            if ip_obj < ipaddress.IPv4Address("255.255.255.255"):
                neighbors.append(ip_obj + 1)

            for neighbor_ip in neighbors:
                neighbor_str = str(neighbor_ip)
                
                # Verify logic: Does this neighbor have a PTR?
                # If so, it's a valid node to add.
                try:
                    addr = dns.reversename.from_address(neighbor_str)
                    _ = self.resolver.resolve(addr, "PTR")
                    
                    # If PTR exists, we treat it as a found neighbor
                    new_node = Node(value=neighbor_str, type=NodeType.IP_V4)
                    edge = Edge(source=node, target=new_node, type=EdgeType.NEIGHBOR)
                    yield new_node, edge
                except Exception:
                    # No PTR, or timeout -> assume not interesting for now
                    continue
        except Exception:
            pass
