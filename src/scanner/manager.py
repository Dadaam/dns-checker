from .dns_lookup import DNSLookup
from .whois_lookup import WhoisLookup
from typing import Dict, Any

class ScannerManager:
    """
    Orchestrates the scanning process, combining DNS and WHOIS lookups.
    """
    
    def __init__(self, domain: str):
        self.domain = domain
        self.dns_scanner = DNSLookup(domain)
        self.whois_scanner = WhoisLookup()

    def scan_all(self) -> Dict[str, Any]:
        """
        Perform a full scan (DNS + WHOIS).
        """
        return {
            "domain": self.domain,
            "dns": self.dns_scanner.get_all_records(),
            "whois": self.whois_scanner.get_whois_info(self.domain)
        }
