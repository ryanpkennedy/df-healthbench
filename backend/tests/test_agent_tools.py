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
    """Test ICD-10-CM code lookup tool with LLM-based selection."""
    
    @pytest.mark.asyncio
    @patch('app.services.agent_extraction.OpenAI')
    @patch('httpx.AsyncClient')
    async def test_icd10_single_result(self, mock_client_class, mock_openai_class):
        """Test ICD-10 lookup when only one code is found (no LLM needed)."""
        # Mock the async HTTP client
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Mock API response with single result
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            1,  # Count - only one match
            ["J00"],
            None,
            [["J00", "Acute nasopharyngitis (common cold)"]]
        ]
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        
        # Test the function (should not call LLM for single result)
        result = await lookup_icd10_code_func(
            detailed_term="Viral upper respiratory infection",
            simplified_term="upper respiratory infection"
        )
        
        # Assertions
        assert result["code"] == "J00"
        assert "nasopharyngitis" in result["description"]
        assert result["confidence"] == "exact"
        assert result["total_matches"] == 1
        assert result["all_codes"] == [{"code": "J00", "description": "Acute nasopharyngitis (common cold)"}]
        
        # Verify LLM was NOT called (only one result)
        assert not mock_openai_class.called
    
    @pytest.mark.asyncio
    @patch('app.services.agent_extraction.OpenAI')
    @patch('httpx.AsyncClient')
    async def test_icd10_multiple_results_llm_selection(self, mock_client_class, mock_openai_class):
        """Test ICD-10 lookup with multiple results - uses LLM to select best match."""
        # Mock the async HTTP client
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        
        # Mock API response with multiple asthma codes
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            19,  # Total count (19 asthma codes exist)
            ["J45.901", "J45.40", "J45.41", "J45.50", "J45.51", "J45.20", "J45.21"],
            None,
            [
                ["J45.901", "Unspecified asthma with (acute) exacerbation"],
                ["J45.40", "Moderate persistent asthma, uncomplicated"],
                ["J45.41", "Moderate persistent asthma with (acute) exacerbation"],
                ["J45.50", "Severe persistent asthma, uncomplicated"],
                ["J45.51", "Severe persistent asthma with (acute) exacerbation"],
                ["J45.20", "Mild intermittent asthma, uncomplicated"],
                ["J45.21", "Mild intermittent asthma with (acute) exacerbation"]
            ]
        ]
        mock_response.raise_for_status = Mock()
        mock_client.get.return_value = mock_response
        
        # Mock LLM response selecting the best code
        mock_llm_client = Mock()
        mock_llm_response = Mock()
        mock_llm_response.choices = [Mock(message=Mock(content="J45.901"))]
        mock_llm_client.chat.completions.create.return_value = mock_llm_response
        mock_openai_class.return_value = mock_llm_client
        
        # Test the function
        result = await lookup_icd10_code_func(
            detailed_term="Asthma exacerbation (likely viral-triggered)",
            simplified_term="asthma"
        )
        
        # Assertions
        assert result["code"] == "J45.901"
        assert "exacerbation" in result["description"].lower()
        assert result["confidence"] == "high"
        assert result["total_matches"] == 19
        assert len(result["all_codes"]) == 7  # API returned 7 codes
        
        # Verify LLM was called for selection
        mock_llm_client.chat.completions.create.assert_called_once()
        llm_call_args = mock_llm_client.chat.completions.create.call_args
        assert "Asthma exacerbation" in str(llm_call_args)  # Detailed term passed to LLM
    
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
        result = await lookup_icd10_code_func(
            detailed_term="Nonexistent condition XYZ-123",
            simplified_term="nonexistent condition"
        )
        
        # Should return None/empty with confidence "none"
        assert result["code"] is None
        assert result["confidence"] == "none"
        assert result["total_matches"] == 0
        assert result["all_codes"] == []
    
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient')
    async def test_icd10_api_error(self, mock_client_class):
        """Test ICD-10 lookup handles API errors gracefully."""
        # Mock the async client to raise an exception
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client
        mock_client.get.side_effect = Exception("API connection failed")
        
        # Test the function
        result = await lookup_icd10_code_func(
            detailed_term="Essential hypertension",
            simplified_term="hypertension"
        )
        
        # Should return error information, not crash
        assert isinstance(result, dict)
        assert result["code"] is None
        assert result["confidence"] == "none"
        assert "error" in result
        assert result["total_matches"] == 0


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
        
        result = await lookup_icd10_code_func(
            detailed_term="",
            simplified_term=""
        )
        
        assert result["code"] is None
        assert result["confidence"] == "none"
        assert result["total_matches"] == 0
        assert result["all_codes"] == []


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

