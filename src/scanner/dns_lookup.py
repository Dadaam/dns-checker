import dns.resolver
from typing import Dict, Any, List

class DNSLookup:
    """
    Handles DNS record queries for a given domain.
    """
    
    RECORD_TYPES = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'SOA', 'CNAME']

    def __init__(self, domain: str):
        self.domain = domain
        self.resolver = dns.resolver.Resolver()
        # Optional: Configure resolver usage (e.g. timeout, nameservers) if needed in future
        self.resolver.lifetime = 5.0 # Set timeout

    def get_records(self, record_type: str) -> List[str]:
        """
        Fetch specific DNS records for the domain.
        
        Args:
            record_type (str): The DNS record type (e.g., 'A', 'MX').
            
        Returns:
            List[str]: A list of string representations of the records found.
        """
        try:
            answers = self.resolver.resolve(self.domain, record_type)
            return [str(rdata) for rdata in answers]
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            return []
        except dns.resolver.NoNameservers:
            return ["Error: No nameservers could be reached."]
        except Exception as e:
            return [f"Error: {str(e)}"]

    def get_all_records(self) -> Dict[str, List[str]]:
        """
        Fetch all supported DNS records for the domain.
        
        Returns:
            Dict[str, List[str]]: Dictionary mapping record types to their values.
        """
        results = {}
        for record in self.RECORD_TYPES:
            results[record] = self.get_records(record)
        return results

    def get_reverse_dns(self, ip_address: str) -> str:
        """
        Perform a reverse DNS lookup for an IP address.
        """
        try:
            addr = dns.reversename.from_address(ip_address)
            return str(self.resolver.resolve(addr, "PTR")[0])
        except Exception as e:
            return f"Error: {str(e)}"
