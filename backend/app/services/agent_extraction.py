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


async def lookup_icd10_code_func(detailed_term: str, simplified_term: str) -> dict:
    """
    Look up the best ICD-10-CM code for a medical condition using a two-step process:
    1. Query NLM Clinical Tables API with simplified term to get ALL relevant codes
    2. Use LLM to select the best matching code based on the detailed term
    
    Args:
        detailed_term: Full diagnosis as written in note (e.g., "Asthma exacerbation (likely viral-triggered)")
        simplified_term: Base condition for ICD search (e.g., "asthma")
    
    Returns:
        dict with:
        - code: Best matching ICD-10-CM code (LLM-selected)
        - description: Description of the selected code
        - confidence: Confidence level (exact, high, or none)
        - total_matches: Total number of codes found
        - all_codes: All ICD codes returned by API (for reference)
        
    API Reference: https://clinicaltables.nlm.nih.gov/apidoc/icd10cm/v3/doc.html
    """
    logger.info(f"******** Looking up ICD-10-CM code for '{detailed_term}' (simplified: '{simplified_term}')")
    try:
        # Step 1: Get ALL relevant ICD codes from API using simplified term
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search",
                params={
                    "sf": "code,name",  # Search fields: code and name
                    "terms": simplified_term,  # Use simplified term for broad matching
                    # No maxList - get ALL relevant codes (API default is 7, we want them all)
                }
            )
            response.raise_for_status()
            data = response.json()
            
            # Response format: [count, [codes], null, [[code, name], [code, name], ...]]
            count = data[0]
            
            if count == 0 or not data[3]:
                logger.warning(f"No ICD-10-CM codes found for simplified term '{simplified_term}'")
                return {
                    "code": None,
                    "description": None,
                    "confidence": "none",
                    "total_matches": 0,
                    "all_codes": []
                }
            
            # Collect all returned codes
            all_codes = [
                {"code": code_info[0], "description": code_info[1]}
                for code_info in data[3]
            ]
            
            logger.info(
                f"ICD lookup for '{simplified_term}': found {count} total matches, "
                f"retrieved {len(all_codes)} codes"
            )
            
            # Step 2: If only one result, return it immediately
            if len(all_codes) == 1:
                return {
                    "code": all_codes[0]["code"],
                    "description": all_codes[0]["description"],
                    "confidence": "exact",
                    "total_matches": count,
                    "all_codes": all_codes
                }
            
            # Step 3: Use LLM to select the best matching code based on detailed term
            logger.info(f"Using LLM to select best ICD code from {len(all_codes)} options for '{detailed_term}'")
            
            client_llm = OpenAI(api_key=settings.openai_api_key)
            
            # Format codes for LLM
            codes_text = "\n".join([
                f"{i+1}. {code['code']}: {code['description']}"
                for i, code in enumerate(all_codes)
            ])
            
            llm_prompt = f"""Given this detailed diagnosis from a medical note:
                "{detailed_term}"

                Select the most appropriate ICD-10-CM code from these options:

                {codes_text}

                Respond with ONLY the code number (e.g., "E11.9" or "J45.901"). No explanation needed.
            """

            llm_response = client_llm.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a medical coding specialist. Select the most appropriate ICD-10-CM code."},
                    {"role": "user", "content": llm_prompt}
                ],
                temperature=0.8,  # Low temperature for consistent selection
                max_tokens=20
            )
            
            selected_code_text = llm_response.choices[0].message.content.strip()
            
            # Find the selected code in our results
            selected = None
            for code_info in all_codes:
                if code_info["code"] in selected_code_text:
                    selected = code_info
                    break
            
            # If LLM selection failed, use first result
            if not selected:
                logger.warning(f"LLM selection unclear ('{selected_code_text}'), using first result")
                selected = all_codes[0]
            else:
                logger.info(f"LLM selected: {selected['code']} for '{detailed_term}'")
            
            return {
                "code": selected["code"],
                "description": selected["description"],
                "confidence": "high",
                "total_matches": count,
                "all_codes": all_codes
            }
            
    except Exception as e:
        logger.error(f"Error looking up ICD code for '{detailed_term}' (simplified: '{simplified_term}'): {e}")
        return {
            "code": None,
            "description": None,
            "confidence": "none",
            "error": str(e),
            "total_matches": 0,
            "all_codes": []
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

