import whois
from typing import Dict, Any, Union

class WhoisLookup:
    """
    Handles WHOIS lookups for a given domain.
    """

    @staticmethod
    def get_whois_info(domain: str) -> Dict[str, Any]:
        """
        Fetch WHOIS information for the domain.

        Args:
            domain (str): The domain name.

        Returns:
            Dict[str, Any]: A dictionary containing WHOIS data.
        """
        try:
            w = whois.whois(domain)
            # Serialize to dict explicitly if needed, or return the WhoisEntry object as dict
            # whois library returns a WhoisEntry which is dict-like
            if not w.domain_name:
                 return {"error": "No WHOIS data found or lookup failed."}
            return w
        except Exception as e:
            return {"error": f"WHOIS lookup failed: {str(e)}"}
