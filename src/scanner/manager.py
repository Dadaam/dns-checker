from .dns_lookup import DNSLookup
from .whois_lookup import WhoisLookup
from .robots_lookup import RobotsLookup
from typing import Dict, Any

class ScannerManager:
    """
    Orchestrates the scanning process, combining DNS and WHOIS lookups.
    """
    
    def __init__(self, domain: str):
        self.domain = domain
        self.dns_scanner = DNSLookup(domain)
        self.whois_scanner = WhoisLookup()
        self.robots_scanner = RobotsLookup()

    def scan_all(self) -> Dict[str, Any]:
        """
        Perform a full scan (DNS + WHOIS + Robots.txt).
        """
        return {
            "domain": self.domain,
            "dns": self.dns_scanner.get_all_records(),
            "whois": self.whois_scanner.get_whois_info(self.domain),
            "robots": self.robots_scanner.get_robots_txt(self.domain)
        }
