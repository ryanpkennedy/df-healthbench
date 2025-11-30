"""
Unit tests for agent extraction tools.

Tests individual tool functions with mocked external API calls.
This ensures tools work correctly without hitting real APIs.
"""

import pytest
from unittest.mock import patch, Mock, AsyncMock
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.agent_extraction import lookup_icd10_code_func, lookup_rxnorm_code_func


class TestICD10Lookup:
    """Test ICD-10-CM code lookup tool."""
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_icd10_exact_match(self, mock_client_class):
        """Test successful ICD-10 code lookup with exact match."""
        # Mock the async client context manager and get method
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Mock successful API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            2,  # Count
            ["E11.9", "E11.65"],  # Codes
            None,
            [
                ["E11.9", "Type 2 diabetes mellitus without complications"],
                ["E11.65", "Type 2 diabetes mellitus with hyperglycemia"]
            ]
        ]
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        
        # Test the function
        result = await lookup_icd10_code_func("type 2 diabetes")
        
        # Assertions
        assert result["code"] == "E11.9"
        assert "Type 2 diabetes" in result["description"]
        assert result["confidence"] in ["exact", "high"]
        
        # Verify API was called with correct parameters
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert "clinicaltables.nlm.nih.gov" in str(call_args)
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_icd10_no_results(self, mock_client_class):
        """Test ICD-10 lookup when no results found."""
        # Mock the async client
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Mock empty API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [0, [], None, []]
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        
        # Test the function
        result = await lookup_icd10_code_func("nonexistent condition xyz")
        
        # Should return None/empty with confidence "none"
        assert result["code"] is None
        assert result["confidence"] == "none"
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_icd10_api_error(self, mock_client_class):
        """Test ICD-10 lookup handles API errors gracefully."""
        # Mock the async client to raise an exception
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.get.side_effect = Exception("API connection failed")
        
        # Test the function
        result = await lookup_icd10_code_func("hypertension")
        
        # Should return error information, not crash
        assert isinstance(result, dict)
        assert result["code"] is None
        assert result["confidence"] == "none"
        assert "error" in result


class TestRxNormLookup:
    """Test RxNorm code lookup tool."""
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_rxnorm_exact_match(self, mock_client_class):
        """Test successful RxNorm lookup with exact match."""
        # Mock the async client
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Mock exact match response
        mock_response_exact = Mock()
        mock_response_exact.status_code = 200
        mock_response_exact.json.return_value = {
            "idGroup": {
                "rxnormId": ["860975"]
            }
        }
        mock_response_exact.raise_for_status = Mock()
        
        # Mock name lookup response
        mock_response_name = Mock()
        mock_response_name.status_code = 200
        mock_response_name.json.return_value = {
            "propConceptGroup": {
                "propConcept": [
                    {"propValue": "Metformin 500 MG Oral Tablet"}
                ]
            }
        }
        mock_response_name.raise_for_status = Mock()
        
        # Set up mock to return different responses for sequential calls
        mock_client.get.side_effect = [mock_response_exact, mock_response_name]
        
        # Test the function
        result = await lookup_rxnorm_code_func("metformin")
        
        # Assertions
        assert result["rxcui"] == "860975"
        assert "Metformin" in result["name"]
        assert result["confidence"] == "exact"
        
        # Verify API was called twice (exact match + name lookup)
        assert mock_client.get.call_count == 2
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_rxnorm_approximate_match(self, mock_client_class):
        """Test RxNorm lookup with approximate match fallback."""
        # Mock the async client
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Mock empty exact match response
        mock_response_exact = Mock()
        mock_response_exact.status_code = 200
        mock_response_exact.json.return_value = {"idGroup": {}}
        mock_response_exact.raise_for_status = Mock()
        
        # Mock approximate match response
        mock_response_approx = Mock()
        mock_response_approx.status_code = 200
        mock_response_approx.json.return_value = {
            "approximateGroup": {
                "candidate": [
                    {
                        "rxcui": "197361",
                        "name": "Aspirin 325 MG Oral Tablet",
                        "score": "100"
                    }
                ]
            }
        }
        mock_response_approx.raise_for_status = Mock()
        
        mock_client.get.side_effect = [mock_response_exact, mock_response_approx]
        
        # Test the function
        result = await lookup_rxnorm_code_func("asprin")  # Misspelling
        
        # Should find approximate match
        assert result["rxcui"] == "197361"
        assert "Aspirin" in result["name"]
        assert result["confidence"] == "approximate"
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_rxnorm_no_results(self, mock_client_class):
        """Test RxNorm lookup when no results found."""
        # Mock the async client
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Mock empty response for exact match
        mock_response_exact = Mock()
        mock_response_exact.status_code = 200
        mock_response_exact.json.return_value = {"idGroup": {}}
        mock_response_exact.raise_for_status = Mock()
        
        # Mock empty response for approximate match
        mock_response_approx = Mock()
        mock_response_approx.status_code = 200
        mock_response_approx.json.return_value = {"approximateGroup": {"candidate": []}}
        mock_response_approx.raise_for_status = Mock()
        
        mock_client.get.side_effect = [mock_response_exact, mock_response_approx]
        
        # Test the function
        result = await lookup_rxnorm_code_func("nonexistent drug xyz")
        
        # Should return None with confidence "none"
        assert result["rxcui"] is None
        assert result["confidence"] == "none"
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_rxnorm_api_error(self, mock_client_class):
        """Test RxNorm lookup handles API errors gracefully."""
        # Mock the async client to raise an exception
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.get.side_effect = Exception("Network timeout")
        
        # Test the function
        result = await lookup_rxnorm_code_func("aspirin")
        
        # Should return error information, not crash
        assert isinstance(result, dict)
        assert result["rxcui"] is None
        assert result["confidence"] == "none"
        assert "error" in result


class TestICD10LookupEdgeCases:
    """Test edge cases for ICD-10 lookup."""
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_icd10_empty_string(self, mock_client_class):
        """Test ICD-10 lookup with empty string."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [0, [], None, []]
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        
        result = await lookup_icd10_code_func("")
        
        assert result["code"] is None
        assert result["confidence"] == "none"
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_icd10_multiple_results(self, mock_client_class):
        """Test ICD-10 lookup returns first result when multiple matches."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            3,  # Multiple results
            ["I10", "I11.0", "I11.9"],
            None,
            [
                ["I10", "Essential (primary) hypertension"],
                ["I11.0", "Hypertensive heart disease with heart failure"],
                ["I11.9", "Hypertensive heart disease without heart failure"]
            ]
        ]
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        
        result = await lookup_icd10_code_func("hypertension")
        
        # Should return first result
        assert result["code"] == "I10"
        assert "Essential" in result["description"]


class TestRxNormLookupEdgeCases:
    """Test edge cases for RxNorm lookup."""
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_rxnorm_empty_string(self, mock_client_class):
        """Test RxNorm lookup with empty string."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Mock empty responses
        mock_response1 = Mock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = {"idGroup": {}}
        mock_response1.raise_for_status = Mock()
        
        mock_response2 = Mock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = {"approximateGroup": {"candidate": []}}
        mock_response2.raise_for_status = Mock()
        
        mock_client.get.side_effect = [mock_response1, mock_response2]
        
        result = await lookup_rxnorm_code_func("")
        
        assert result["rxcui"] is None
        assert result["confidence"] == "none"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

