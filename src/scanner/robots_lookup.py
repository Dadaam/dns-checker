import requests

class RobotsLookup:
    """
    Handles fetching of robots.txt for a given domain.
    """

    @staticmethod
    def get_robots_txt(domain: str) -> str:
        """
        Fetch the robots.txt file content.

        Args:
            domain (str): The domain name.

        Returns:
            str: The content of robots.txt or an error message.
        """
        try:
            # Ensure protocol is present
            if not domain.startswith("http"):
                url = f"http://{domain}/robots.txt"
            else:
                url = f"{domain.rstrip('/')}/robots.txt"
            
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return response.text
            else:
                return f"Error: Received status code {response.status_code}"
        except Exception as e:
            return f"Error fetching robots.txt: {str(e)}"
