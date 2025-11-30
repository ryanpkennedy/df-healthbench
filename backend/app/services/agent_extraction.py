"""
Agent-based extraction service for structured clinical data.

Uses OpenAI Agents SDK to extract entities from medical notes and enrich
with ICD-10-CM codes (via NLM Clinical Tables API) and RxNorm codes
(via NLM RxNav API).
"""

import os
import json
import logging
from typing import List, Optional

import httpx
from openai import OpenAI
from agents import Agent, Runner, function_tool

from app.config import settings
from app.prompts import get_prompt
from app.schemas.extraction import (
    StructuredClinicalData,
    DiagnosisCode,
    MedicationCode,
    VitalSigns,
    PatientInfo,
)

logger = logging.getLogger(__name__)

# ============================================================================
# Tool Functions
# ============================================================================


def extract_clinical_entities_func(note_text: str) -> dict:
    """
    Extract clinical entities from a medical note using LLM.
    
    Returns a dictionary with:
    - diagnoses: list of diagnosis/condition strings
    - medications: list of medication strings
    - vital_signs: dict of vital sign measurements
    - lab_results: list of lab test result strings
    - plan_actions: list of treatment plan items
    - patient_info: dict of patient demographics if available
    """
    client = OpenAI(api_key=settings.openai_api_key)
    
    # Load system prompt from YAML
    system_prompt = get_prompt("agent_extraction.yaml", "entity_extraction_system_prompt")
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {"role": "user", "content": note_text}
        ],
        response_format={"type": "json_object"}
    )
    
    return json.loads(response.choices[0].message.content)


async def lookup_icd10_code_func(condition: str) -> dict:
    """
    Look up ICD-10-CM code for a medical condition using NLM Clinical Tables API.
    
    Args:
        condition: The condition or diagnosis text (e.g., "type 2 diabetes")
    
    Returns:
        dict with code, description, and confidence level
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search",
                params={
                    "sf": "code,name",
                    "terms": condition,
                    "maxList": 1
                }
            )
            response.raise_for_status()
            data = response.json()
            
            # Response format: [count, [codes], null, [[code, name]]]
            count = data[0]
            if count > 0 and len(data) > 3 and data[3]:
                code_info = data[3][0]  # First result
                return {
                    "code": code_info[0],
                    "description": code_info[1],
                    "confidence": "high" if count == 1 else "exact"
                }
            else:
                return {
                    "code": None,
                    "description": None,
                    "confidence": "none"
                }
    except Exception as e:
        logger.error(f"Error looking up ICD code for '{condition}': {e}")
        return {
            "code": None,
            "description": None,
            "confidence": "none",
            "error": str(e)
        }


async def lookup_rxnorm_code_func(medication: str) -> dict:
    """
    Look up RxNorm code (RxCUI) for a medication using NLM RxNav API.
    
    Args:
        medication: The medication text (e.g., "metformin 500mg")
    
    Returns:
        dict with rxcui, name, and confidence level
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Try exact match first
            response = await client.get(
                "https://rxnav.nlm.nih.gov/REST/rxcui.json",
                params={"name": medication}
            )
            response.raise_for_status()
            data = response.json()
            
            if "idGroup" in data and "rxnormId" in data["idGroup"]:
                rxcui = data["idGroup"]["rxnormId"][0]
                
                # Get the name for this RxCUI
                name_response = await client.get(
                    f"https://rxnav.nlm.nih.gov/REST/rxcui/{rxcui}/property.json",
                    params={"propName": "RxNorm Name"}
                )
                name_data = name_response.json()
                
                rxnorm_name = medication  # Default to input
                if "propConceptGroup" in name_data:
                    props = name_data["propConceptGroup"].get("propConcept", [])
                    if props:
                        rxnorm_name = props[0].get("propValue", medication)
                
                return {
                    "rxcui": rxcui,
                    "name": rxnorm_name,
                    "confidence": "exact"
                }
            
            # Try approximate match if exact fails
            approx_response = await client.get(
                "https://rxnav.nlm.nih.gov/REST/approximateTerm.json",
                params={"term": medication, "maxEntries": 1}
            )
            approx_data = approx_response.json()
            
            if "approximateGroup" in approx_data:
                candidates = approx_data["approximateGroup"].get("candidate", [])
                if candidates:
                    best = candidates[0]
                    return {
                        "rxcui": best.get("rxcui"),
                        "name": best.get("name", medication),
                        "confidence": "approximate"
                    }
            
            return {
                "rxcui": None,
                "name": None,
                "confidence": "none"
            }
            
    except Exception as e:
        logger.error(f"Error looking up RxNorm code for '{medication}': {e}")
        return {
            "rxcui": None,
            "name": None,
            "confidence": "none",
            "error": str(e)
        }


# Create tool wrappers for the agent
extract_clinical_entities = function_tool(extract_clinical_entities_func)
lookup_icd10_code = function_tool(lookup_icd10_code_func)
lookup_rxnorm_code = function_tool(lookup_rxnorm_code_func)


# ============================================================================
# Agent Extraction Service
# ============================================================================


class AgentExtractionService:
    """
    Service for extracting structured clinical data from medical notes using agents.
    
    This service uses the OpenAI Agents SDK to orchestrate a multi-tool workflow:
    1. Extract entities from the note text
    2. Enrich diagnoses with ICD-10-CM codes
    3. Enrich medications with RxNorm codes
    4. Return structured, validated data
    """
    
    def __init__(self):
        """Initialize the extraction agent."""
        # Ensure OpenAI API key is available as environment variable
        # (required by OpenAI Agents SDK Runner)
        if not os.getenv("OPENAI_API_KEY"):
            os.environ["OPENAI_API_KEY"] = settings.openai_api_key
        
        # Load agent instructions from YAML
        agent_instructions = get_prompt("agent_extraction.yaml", "agent_instructions")
        
        self.agent = Agent(
            name="Clinical Data Extraction Agent",
            instructions=agent_instructions,
            tools=[extract_clinical_entities, lookup_icd10_code, lookup_rxnorm_code],
            output_type=StructuredClinicalData,
        )
        logger.info("Agent extraction service initialized")
    
    async def extract_structured_data(self, note_text: str) -> StructuredClinicalData:
        """
        Extract structured clinical data from a medical note.
        
        Args:
            note_text: The raw medical note text
            
        Returns:
            StructuredClinicalData with extracted entities and enriched codes
            
        Raises:
            ValueError: If note_text is empty or invalid
            Exception: If agent execution fails
        """
        if not note_text or not note_text.strip():
            raise ValueError("Note text cannot be empty")
        
        logger.info(f"Starting agent extraction for note (length: {len(note_text)} chars)")
        
        try:
            result = await Runner.run(
                self.agent,
                input=f"Extract and enrich clinical data from this medical note:\n\n{note_text}"
            )
            
            structured_data = result.final_output
            
            # Log summary statistics
            logger.info(
                f"Extraction complete: "
                f"{len(structured_data.diagnoses)} diagnoses, "
                f"{len(structured_data.medications)} medications, "
                f"{len(structured_data.lab_results)} labs, "
                f"{len(structured_data.plan_actions)} plan actions"
            )
            
            return structured_data
            
        except Exception as e:
            logger.error(f"Agent extraction failed: {e}", exc_info=True)
            raise


# ============================================================================
# Singleton Instance
# ============================================================================

_extractor_service: Optional[AgentExtractionService] = None


def get_extractor_service() -> AgentExtractionService:
    """
    Get the singleton instance of the agent extraction service.
    
    Returns:
        AgentExtractionService instance
    """
    global _extractor_service
    if _extractor_service is None:
        _extractor_service = AgentExtractionService()
    return _extractor_service

