"""
Call analysis service for extracting structured data from transcripts.

Uses OpenAI to analyze call transcripts and extract structured information
based on scenario type (driver_checkin or emergency_protocol).
"""

import logging
import json
from typing import Dict, Any
from openai import AsyncOpenAI
from backend.config import get_settings
from backend.constants.analysis_schemas import get_analysis_schema

logger = logging.getLogger(__name__)


class CallAnalyzer:
    """
    Analyzes call transcripts and extracts structured data.
    """

    def __init__(self):
        """Initialize call analyzer with OpenAI client."""
        settings = get_settings()
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        logger.debug("Call analyzer initialized")

    async def analyze_conversation(
        self,
        conversation_history: list,
        scenario_type: str = "driver_checkin",
    ) -> Dict[str, Any]:
        """
        Analyze conversation and extract structured data.
        
        Args:
            conversation_history: List of conversation messages
            scenario_type: Type of scenario (driver_checkin or emergency_protocol)
            
        Returns:
            Dictionary with extracted structured data
        """
        try:
            logger.info(f"Analyzing conversation for scenario: {scenario_type}")
            
            # Get analysis schema for scenario
            schema = get_analysis_schema(scenario_type)
            
            # Build analysis prompt
            analysis_prompt = self._build_analysis_prompt(conversation_history, schema)
            
            # Call OpenAI for analysis
            response = await self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a data extraction expert. Extract the requested information from the conversation and return ONLY a valid JSON object with the specified fields."
                    },
                    {
                        "role": "user",
                        "content": analysis_prompt
                    }
                ],
                temperature=0.3,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            # Parse the response
            extracted_data = json.loads(response.choices[0].message.content)
            
            logger.info(f"✅ Analysis complete: {list(extracted_data.keys())}")
            logger.debug(f"Extracted data: {extracted_data}")
            
            return extracted_data
            
        except Exception as e:
            logger.error(f"Failed to analyze conversation: {e}", exc_info=True)
            return {}

    def _build_analysis_prompt(
        self,
        conversation_history: list,
        schema: list
    ) -> str:
        """
        Build the analysis prompt from conversation and schema.
        
        Args:
            conversation_history: List of messages
            schema: Analysis schema definition
            
        Returns:
            Prompt string for analysis
        """
        # Format conversation
        conversation_text = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in conversation_history
            if msg['role'] != 'system'
        ])
        
        # Format schema fields
        fields_description = "\n".join([
            f"- {field['name']} ({field['type']}): {field['description']}"
            for field in schema
        ])
        
        prompt = f"""Analyze the following conversation and extract structured data.

CONVERSATION:
{conversation_text}

EXTRACT THESE FIELDS (return as JSON):
{fields_description}

Return ONLY a JSON object with these exact field names. If a field cannot be determined, use null or appropriate default value.
"""
        
        return prompt


def get_call_analyzer() -> CallAnalyzer:
    """
    Get call analyzer instance.
    
    Returns:
        CallAnalyzer instance
    """
    return CallAnalyzer()

