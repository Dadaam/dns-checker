import pytest
from unittest.mock import MagicMock, patch
from src.scanner.dns_lookup import DNSLookup
import dns.resolver

@pytest.fixture
def dns_scanner():
    return DNSLookup("example.com")

def test_get_records_success(dns_scanner):
    with patch('dns.resolver.Resolver.resolve') as mock_resolve:
        # Mocking the response object
        mock_answer = MagicMock()
        mock_answer.__str__.return_value = "1.2.3.4"
        mock_resolve.return_value = [mock_answer]

        records = dns_scanner.get_records("A")
        assert records == ["1.2.3.4"]
        mock_resolve.assert_called_with("example.com", "A")

def test_get_records_no_answer(dns_scanner):
    with patch('dns.resolver.Resolver.resolve') as mock_resolve:
        mock_resolve.side_effect = dns.resolver.NoAnswer
        records = dns_scanner.get_records("A")
        assert records == []

def test_get_records_nxdomain(dns_scanner):
    with patch('dns.resolver.Resolver.resolve') as mock_resolve:
        mock_resolve.side_effect = dns.resolver.NXDOMAIN
        records = dns_scanner.get_records("A")
        assert records == []

def test_get_all_records(dns_scanner):
    with patch.object(DNSLookup, 'get_records') as mock_get_records:
        mock_get_records.return_value = ["mocked_record"]
        
        results = dns_scanner.get_all_records()
        
        assert "A" in results
        assert "MX" in results
        assert "TXT" in results
        assert results["A"] == ["mocked_record"]
        assert mock_get_records.call_count == len(DNSLookup.RECORD_TYPES)
