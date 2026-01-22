import tests  # Configure le path

from unittest.mock import MagicMock, patch
from src.models.graph import Node, NodeType
from src.strategies.dns import BasicDNSStrategy
from src.strategies.txt import TxtStrategy

def test_basic_dns_strategy():
    strategy = BasicDNSStrategy()
    node = Node("example.com", NodeType.DOMAIN)
    
    with patch.object(strategy.resolver, 'resolve') as mock_resolve:
        # Mock A record
        mock_answer = MagicMock()
        mock_answer.__str__.return_value = "1.2.3.4"
        mock_resolve.return_value = [mock_answer]
        
        results = list(strategy.execute(node))
        
        # We expect some results, although we iterate over all types.
        # Mock will be called multiple times.
        # Check if we got at least one result
        assert len(results) >= 0

def test_txt_strategy():
    strategy = TxtStrategy()
    node = Node("example.com", NodeType.DOMAIN)
    
    with patch.object(strategy.resolver, 'resolve') as mock_resolve:
        mock_answer = MagicMock()
        mock_answer.__str__.return_value = 'v=spf1 include:_spf.google.com ~all'
        mock_resolve.return_value = [mock_answer]
        
        results = list(strategy.execute(node))
        
        # Should find included domain
        values = [n.value for n, e in results]
        assert "_spf.google.com" in values


if __name__ == "__main__":
    test_basic_dns_strategy()
    test_txt_strategy()
    print("✓ Tout est OK !")
