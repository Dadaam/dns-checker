from dataclasses import dataclass, field
from enum import Enum
from typing import List, Set, Optional

class NodeType(Enum):
    DOMAIN = "DOMAIN"
    IP_V4 = "IP_V4"
    IP_V6 = "IP_V6"
    TLD = "TLD"
    SERVICE = "SERVICE" # Pour les enregistrements SRV
    TXT = "TXT" # Pour le contenu brut TXT

class EdgeType(Enum):
    A = "A"
    AAAA = "AAAA"
    CNAME = "CNAME"
    NS = "NS"
    MX = "MX"
    PTR = "PTR"
    TXT = "TXT"
    SRV = "SRV"
    PARENT = "PARENT" # Parent déduit
    NEIGHBOR = "NEIGHBOR" # Voisin IP
    SUBDOMAIN = "SUBDOMAIN" # Sous-domaine brute-forcé

@dataclass(frozen=True)
class Node:
    value: str
    type: NodeType
    
    def __repr__(self):
        return f"{self.type.value}:{self.value}"

@dataclass(frozen=True)
class Edge:
    source: Node
    target: Node
    type: EdgeType
    
    def __repr__(self):
        return f"{self.source} --[{self.type.value}]--> {self.target}"
