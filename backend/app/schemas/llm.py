"""
Pydantic schemas for LLM operations validation and serialization.

These schemas are used for request/response validation in LLM-related endpoints.
"""

from pydantic import BaseModel, Field
from typing import Dict, Optional


class SummarizeRequest(BaseModel):
    """
    Schema for medical note summarization request.
    
    Used by POST /summarize_note endpoint to validate incoming requests.
    """
    
    text: str = Field(
        ...,
        min_length=10,
        description="Medical note text to summarize (minimum 10 characters)",
        examples=[
            "Subjective: 45yo male presents with chest pain for 2 hours. "
            "Pain is substernal, 7/10 severity, radiating to left arm. "
            "Denies shortness of breath. Has history of hypertension. "
            "Objective: BP 145/92, HR 88, RR 16, O2 sat 98% on RA. "
            "Appears uncomfortable but not in acute distress. "
            "Heart: regular rate and rhythm, no murmurs. Lungs clear. "
            "Assessment: Chest pain, concerning for ACS. "
            "Plan: EKG, troponin, cardiology consult, aspirin 325mg given."
        ]
    )
    
    model: Optional[str] = Field(
        None,
        description="Optional: Override the default LLM model",
        examples=["gpt-5-nano", "gpt-5-mini", "gpt-5"]
    )


class TokenUsage(BaseModel):
    """
    Schema for token usage information.
    
    Provides transparency into LLM API costs and token consumption.
    """
    
    prompt_tokens: int = Field(..., description="Number of tokens in the prompt")
    completion_tokens: int = Field(..., description="Number of tokens in the completion")
    total_tokens: int = Field(..., description="Total tokens used (prompt + completion)")


class SummarizeResponse(BaseModel):
    """
    Schema for medical note summarization response.
    
    Returns the summary along with metadata about the operation.
    """
    
    summary: str = Field(
        ...,
        description="The generated summary of the medical note",
        examples=[
            "**Chief Complaint:** 45-year-old male with substernal chest pain.\n\n"
            "**Key Findings:**\n"
            "- Pain: 7/10 severity, radiating to left arm, 2-hour duration\n"
            "- Vital signs: BP 145/92, HR 88, stable\n"
            "- Physical exam: Appears uncomfortable, heart regular, lungs clear\n\n"
            "**Assessment:** Chest pain concerning for acute coronary syndrome (ACS)\n\n"
            "**Plan:** EKG, troponin levels, cardiology consultation, aspirin 325mg administered"
        ]
    )
    
    model_used: str = Field(
        ...,
        description="The LLM model that was used for summarization",
        examples=["gpt-5-nano"]
    )
    
    token_usage: TokenUsage = Field(
        ...,
        description="Token usage statistics for cost tracking"
    )
    
    processing_time_ms: int = Field(
        ...,
        description="Processing time in milliseconds",
        examples=[1234]
    )


class ErrorResponse(BaseModel):
    """
    Schema for error responses from LLM endpoints.
    
    Provides consistent error formatting across all LLM operations.
    """
    
    error: str = Field(..., description="Error type")
    detail: str = Field(..., description="Detailed error message")
    status_code: int = Field(..., description="HTTP status code")


