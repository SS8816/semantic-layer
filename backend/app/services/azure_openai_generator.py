"""
Azure OpenAI text generation service for high-quality metadata generation
Uses GPT-5 for generating column aliases and descriptions
"""

from typing import List, Dict, Any, Optional
from openai import AzureOpenAI

from app.config import settings
from app.utils.logger import app_logger as logger


class AzureOpenAIGenerator:
    """Service for generating text using Azure OpenAI GPT-5"""

    def __init__(self):
        """Initialize Azure OpenAI client"""
        self.client = None
        self.model = settings.azure_openai_deployment  # gpt-5
        logger.info(f"Azure OpenAI Generator initialized with model: {self.model}")

    def _get_client(self) -> AzureOpenAI:
        """Get or create Azure OpenAI client (lazy loading)"""
        if self.client is None:
            if not settings.azure_openai_api_key or not settings.azure_openai_endpoint:
                raise ValueError("Azure OpenAI credentials not configured")

            self.client = AzureOpenAI(
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version,
                azure_endpoint=settings.azure_openai_endpoint
            )
            logger.info("Azure OpenAI client initialized for text generation")

        return self.client

    def generate_aliases(
        self,
        column_name: str,
        data_type: str,
        sample_values: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        table_context: Optional[str] = None
    ) -> List[str]:
        """
        Generate alias suggestions for a column using GPT-5

        Args:
            column_name: Name of the column
            data_type: Data type (varchar, bigint, etc.)
            sample_values: Sample values from the column
            tags: Semantic tags (e.g., ['country', 'geographic'])
            table_context: Brief description of the table

        Returns:
            List of 3-5 alias suggestions
        """
        try:
            client = self._get_client()

            # Build context-rich prompt
            prompt = self._build_alias_prompt(
                column_name, data_type, sample_values, tags, table_context
            )

            # Call GPT-5
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a data catalog expert specializing in generating clear, meaningful aliases for database columns. You understand geographic data, POI (Point of Interest) data, and HERE Maps datasets."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=150
            )

            # Parse response
            result = response.choices[0].message.content.strip()
            aliases = [alias.strip() for alias in result.split(',')]

            # Clean and validate
            aliases = [a for a in aliases if a and len(a) > 2][:5]

            logger.debug(f"Generated {len(aliases)} aliases for column: {column_name}")
            return aliases

        except Exception as e:
            logger.error(f"Failed to generate aliases with GPT-5: {e}")
            return []

    def generate_description(
        self,
        column_name: str,
        data_type: str,
        sample_values: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        min_value: Optional[Any] = None,
        max_value: Optional[Any] = None,
        cardinality: Optional[int] = None,
        table_context: Optional[str] = None
    ) -> str:
        """
        Generate a business-friendly description for a column using GPT-5

        Args:
            column_name: Name of the column
            data_type: Data type
            sample_values: Sample values
            tags: Semantic tags
            min_value: Minimum value
            max_value: Maximum value
            cardinality: Number of distinct values
            table_context: Table description

        Returns:
            1-2 sentence description
        """
        try:
            client = self._get_client()

            # Build context-rich prompt
            prompt = self._build_description_prompt(
                column_name, data_type, sample_values, tags,
                min_value, max_value, cardinality, table_context
            )

            # Call GPT-5
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": """You are a data catalog expert specializing in writing clear, business-friendly descriptions for database columns.

Your expertise includes:
- Geographic data (latitude, longitude, coordinates, administrative regions)
- POI (Point of Interest) data (locations, businesses, landmarks)
- HERE Maps datasets (navigation, routing, mapping data)
- Location-based services and spatial data

Write concise descriptions that explain what the column means in plain English, focusing on business value rather than technical details."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=100
            )

            # Parse and clean response
            description = response.choices[0].message.content.strip()

            # Ensure it ends with a period
            if description and not description.endswith('.'):
                description += '.'

            logger.debug(f"Generated description for column: {column_name}")
            return description

        except Exception as e:
            logger.error(f"Failed to generate description with GPT-5: {e}")
            return ""

    def _build_alias_prompt(
        self,
        column_name: str,
        data_type: str,
        sample_values: Optional[List[str]],
        tags: Optional[List[str]],
        table_context: Optional[str]
    ) -> str:
        """Build prompt for alias generation"""
        prompt = f"""Generate 3-5 clear, meaningful aliases for this database column.

Column: {column_name}
Data Type: {data_type}
"""

        if table_context:
            prompt += f"Table Purpose: {table_context}\n"

        if sample_values and len(sample_values) > 0:
            samples_str = ", ".join([str(v) for v in sample_values[:5]])
            prompt += f"Sample Values: {samples_str}\n"

        if tags and len(tags) > 0:
            prompt += f"Tags: {', '.join(tags)}\n"

        prompt += """
Requirements:
- Provide 3-5 aliases separated by commas
- Use clear, business-friendly language
- Make aliases more readable than the technical column name
- Use proper capitalization and spaces
- Keep aliases concise (2-4 words each)

Examples:
- Column "admin_level_2" → "Administrative Level 2, State, Province, Region"
- Column "poi_id" → "POI ID, Location ID, Place Identifier"
- Column "has_h24x7" → "24/7 Hours, Always Open, Open 24 Hours"

Generate aliases (comma-separated):"""

        return prompt

    def _build_description_prompt(
        self,
        column_name: str,
        data_type: str,
        sample_values: Optional[List[str]],
        tags: Optional[List[str]],
        min_value: Optional[Any],
        max_value: Optional[Any],
        cardinality: Optional[int],
        table_context: Optional[str]
    ) -> str:
        """Build prompt for description generation"""
        prompt = f"""Write a clear, concise description (1-2 sentences) for this database column.

Column: {column_name}
Data Type: {data_type}
"""

        if table_context:
            prompt += f"Table Purpose: {table_context}\n"

        if sample_values and len(sample_values) > 0:
            samples_str = ", ".join([str(v) for v in sample_values[:5]])
            prompt += f"Sample Values: {samples_str}\n"

        if min_value is not None and max_value is not None:
            prompt += f"Range: {min_value} to {max_value}\n"

        if cardinality is not None:
            prompt += f"Distinct Values: {cardinality:,}\n"

        if tags and len(tags) > 0:
            prompt += f"Tags: {', '.join(tags)}\n"

        prompt += """
Requirements:
- Write 1-2 clear sentences (max 50 words)
- Explain what this column represents in business terms
- Use language understandable to non-technical users
- Do NOT repeat the column name verbatim
- Do NOT just say "value stored as [data_type]"
- Focus on what the data means, not how it's stored
- For POI/location data, explain the geographic/business context

Good Examples:
- For "admin_level_2": "Name of the state, province, or primary administrative division where the location is situated."
- For "has_h24x7": "Indicates whether the location operates 24 hours a day, 7 days a week."
- For "latitude": "Geographic coordinate representing the north-south position, measured in decimal degrees (-90 to +90)."
- For "poi_id": "Unique identifier for each point of interest in the dataset."
- For "chains": "Business chain or brand affiliation, indicating if the location is part of a larger franchise network."

Write the description:"""

        return prompt


# Global instance
azure_openai_generator = AzureOpenAIGenerator()
