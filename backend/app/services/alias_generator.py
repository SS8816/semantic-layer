"""
Alias and description generation service using Azure OpenAI (primary) and HuggingFace models (fallback)
"""
from transformers import T5Tokenizer, T5ForConditionalGeneration
from typing import List, Dict, Any, Optional
import re
from app.config import settings
from app.utils.logger import app_logger as logger


class AliasGenerator:
    """Service for generating column aliases and descriptions using Azure OpenAI (GPT-5) and HuggingFace models as fallback"""

    def __init__(self):
        """Initialize Azure OpenAI generator and HuggingFace models (lazy loaded)"""
        self.alias_model = None
        self.alias_tokenizer = None
        self.description_model = None
        self.description_tokenizer = None
        self._models_loaded = False

        # Initialize Azure OpenAI generator
        self.azure_generator = None
        self._azure_available = False

        try:
            from app.services.azure_openai_generator import azure_openai_generator
            self.azure_generator = azure_openai_generator
            self._azure_available = True
            logger.info("Azure OpenAI generator available for metadata generation")
        except Exception as e:
            logger.warning(f"Azure OpenAI not available, will use HuggingFace: {e}")

        # Abbreviation dictionary for rule-based expansion
        self.abbreviations = {
            'addr': 'Address',
            'amt': 'Amount',
            'avg': 'Average',
            'qty': 'Quantity',
            'cust': 'Customer',
            'desc': 'Description',
            'dept': 'Department',
            'emp': 'Employee',
            'lat': 'Latitude',
            'lon': 'Longitude',
            'lng': 'Longitude',
            'max': 'Maximum',
            'min': 'Minimum',
            'num': 'Number',
            'pct': 'Percentage',
            'std': 'Standard',
            'temp': 'Temperature',
            'ts': 'Timestamp',
            'ttl': 'Total',
            'cnt': 'Count',
            'id': 'ID',
            'cd': 'Code',
            'dt': 'Date',
            'tm': 'Time',
            'val': 'Value',
            'ref': 'Reference',
            'seq': 'Sequence',
            'src': 'Source',
            'dst': 'Destination',
            'pos': 'Position',
            'dir': 'Direction',
            'dist': 'Distance',
            'coord': 'Coordinate',
            'geo': 'Geographic',
            'usd': 'USD',
            'eur': 'EUR',
            'gbp': 'GBP',
            'pvid': 'ID',
            'admin': 'Administrative',
            'km': 'Kilometers',
            'kms': 'Kilometers',
            'poi': 'POI',
            'h24x7': '24/7 Hours'
        }
    
    def load_models(self):
        """Load HuggingFace models (lazy loading)"""
        if self._models_loaded:
            return
        
        try:
            logger.info(f"Loading alias generation model: {settings.alias_model}")
            self.alias_tokenizer = T5Tokenizer.from_pretrained(settings.alias_model)
            self.alias_model = T5ForConditionalGeneration.from_pretrained(settings.alias_model)
            
            logger.info(f"Loading description generation model: {settings.description_model}")
            self.description_tokenizer = T5Tokenizer.from_pretrained(settings.description_model)
            self.description_model = T5ForConditionalGeneration.from_pretrained(settings.description_model)
            
            self._models_loaded = True
            logger.info("HuggingFace models loaded successfully")
        
        except Exception as e:
            logger.error(f"Failed to load HuggingFace models: {e}")
            logger.warning("Falling back to rule-based alias generation only")
    
    def generate_aliases_and_description(
        self,
        column_name: str,
        data_type: str,
        sample_values: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        min_value: Optional[Any] = None,
        max_value: Optional[Any] = None,
        cardinality: Optional[int] = None,
        table_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate BOTH aliases AND description in a SINGLE call (2x faster!)

        Uses Azure OpenAI GPT-5 to generate both in one API call,
        reducing latency and cost by ~50%.

        Args:
            column_name: Name of the column
            data_type: Data type of the column
            sample_values: Sample values from the column
            tags: List of tags (e.g., ['country', 'geographic'])
            min_value: Minimum value (for numeric columns)
            max_value: Maximum value (for numeric columns)
            cardinality: Number of distinct values
            table_context: Brief description of what the table contains

        Returns:
            Dict with 'aliases' (List[str]) and 'description' (str)
        """
        # Try Azure OpenAI GPT-5 combined generation (FASTEST!)
        if self._azure_available and self.azure_generator:
            try:
                result = self.azure_generator.generate_aliases_and_description(
                    column_name, data_type, sample_values, tags,
                    min_value, max_value, cardinality, table_context
                )
                if result.get("aliases") and result.get("description"):
                    logger.info(f"Generated metadata for {column_name} using Azure OpenAI GPT-5 (combined)")
                    return result
            except Exception as e:
                logger.warning(f"Azure OpenAI combined generation failed: {e}, falling back to separate calls")

        # Fallback to separate calls if combined fails
        aliases = self.generate_aliases(column_name, data_type, sample_values, tags, table_context)
        description = self.generate_description(
            column_name, data_type, sample_values, tags,
            min_value, max_value, cardinality, table_context
        )

        return {
            "aliases": aliases,
            "description": description
        }

    def generate_aliases(
        self,
        column_name: str,
        data_type: str,
        sample_values: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        table_context: Optional[str] = None
    ) -> List[str]:
        """
        Generate multiple alias suggestions for a column

        Uses Azure OpenAI GPT-5 (primary) with HuggingFace fallback

        NOTE: For better performance, use generate_aliases_and_description()

        Args:
            column_name: Name of the column
            data_type: Data type of the column
            sample_values: Sample values from the column
            tags: List of tags (e.g., ['country', 'geographic'])
            table_context: Brief description of what the table contains

        Returns:
            List of alias suggestions (3-5 aliases)
        """
        aliases = []

        # Try Azure OpenAI GPT-5 first (highest quality)
        if self._azure_available and self.azure_generator:
            try:
                ai_aliases = self.azure_generator.generate_aliases(
                    column_name,
                    data_type,
                    sample_values,
                    tags,
                    table_context
                )
                if ai_aliases and len(ai_aliases) > 0:
                    logger.info(f"Generated aliases for {column_name} using Azure OpenAI GPT-5")
                    return ai_aliases
            except Exception as e:
                logger.warning(f"Azure OpenAI alias generation failed: {e}, trying fallback")

        # Try HuggingFace AI generation as fallback
        if self.alias_model and self.alias_tokenizer:
            try:
                ai_aliases = self._generate_aliases_with_ai(
                    column_name,
                    data_type,
                    sample_values,
                    tags,
                    table_context
                )
                if ai_aliases and len(ai_aliases) >= 2:
                    return ai_aliases[:5]  # Return top 5
            except Exception as e:
                logger.warning(f"AI alias generation failed for {column_name}: {e}")

        # Fallback to rule-based
        return self._generate_aliases_rule_based(column_name, data_type, tags)
    
    def _generate_aliases_with_ai(
        self,
        column_name: str,
        data_type: str,
        sample_values: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        table_context: Optional[str] = None
    ) -> List[str]:
        """Generate aliases using AI with rich context"""
        
        # Load models if needed
        if not self._models_loaded:
            self.load_models()
        
        if not self._models_loaded:
            return []
        
        # Build rich prompt
        prompt = f"""Generate 3-5 clear, business-friendly aliases for this database column.

Column: {column_name}
Type: {data_type}
"""
        
        if sample_values and len(sample_values) > 0:
            samples_str = ", ".join([str(v) for v in sample_values[:5]])
            prompt += f"Sample values: {samples_str}\n"
        
        if tags and len(tags) > 0:
            prompt += f"Tags: {', '.join(tags)}\n"
        
        if table_context:
            prompt += f"Table purpose: {table_context}\n"
        
        prompt += """
Requirements:
- Each alias must be 2-5 words maximum
- Must be clear to non-technical business users
- Don't just repeat the column name
- Focus on what the data represents
- Use proper capitalization (Title Case)

Return ONLY the aliases, one per line, nothing else.

Examples:
For column 'admin_l1_pvid': 
Province Identifier
Level 1 Region Code
Admin Area ID

For column 'total_kms':
Total Distance (km)
Length in Kilometers
Total Route Length

Now generate aliases:"""
        
        try:
            # Generate
            inputs = self.alias_tokenizer(
                prompt, 
                return_tensors="pt", 
                max_length=512, 
                truncation=True
            )
            
            outputs = self.alias_model.generate(
                **inputs,
                max_length=100,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                top_p=0.9
            )
            
            result = self.alias_tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Parse aliases from result
            aliases = []
            for line in result.split('\n'):
                line = line.strip()
                if line and len(line.split()) <= 6:  # Max 6 words
                    # Clean up
                    line = line.strip('- •*')
                    if line and not line.lower().startswith(('for ', 'column ', 'examples', 'now ')):
                        aliases.append(line)
            
            return aliases[:5]
        
        except Exception as e:
            logger.warning(f"AI alias generation error: {e}")
            return []
    
    def _generate_aliases_rule_based(
        self,
        column_name: str,
        data_type: str,
        tags: Optional[List[str]] = None
    ) -> List[str]:
        """Generate aliases using rules (fallback)"""
        aliases = []
        col_lower = column_name.lower()
        
        # Split column name and expand abbreviations
        parts = re.split(r'[_\-]|(?<=[a-z])(?=[A-Z])', column_name)
        expanded_parts = []
        for part in parts:
            part_lower = part.lower()
            if part_lower in self.abbreviations:
                expanded_parts.append(self.abbreviations[part_lower])
            else:
                expanded_parts.append(part.capitalize())
        
        # Base alias: expanded words
        base_alias = ' '.join(expanded_parts)
        aliases.append(base_alias)
        
        # Pattern-based aliases
        if 'pvid' in col_lower or '_id' in col_lower or col_lower.endswith('id'):
            aliases.append(base_alias.replace('Pvid', 'Identifier').replace(' Id', ' Identifier'))
            aliases.append(base_alias.replace('Pvid', 'Code').replace(' Id', ' Code'))
        
        # Administrative levels
        if 'admin' in col_lower:
            if 'l1' in col_lower or 'level1' in col_lower:
                aliases.extend(['Province Identifier', 'Level 1 Region ID', 'State Code'])
            elif 'l2' in col_lower or 'level2' in col_lower:
                aliases.extend(['Province Name', 'State Name', 'Level 2 Region'])
            elif 'l3' in col_lower or 'level3' in col_lower:
                aliases.extend(['City Name', 'Municipality', 'Level 3 Region'])
            elif 'l4' in col_lower or 'level4' in col_lower:
                aliases.extend(['District Name', 'Locality', 'Level 4 Region'])
        
        # Distance/measurement
        if 'km' in col_lower or 'kilometer' in col_lower:
            aliases.extend(['Distance (km)', 'Length in Kilometers', 'Total Distance'])
        
        # Coordinates
        if tags:
            if 'latitude' in tags:
                aliases.extend(['Latitude Coordinate', 'Lat', 'North-South Position'])
            if 'longitude' in tags:
                aliases.extend(['Longitude Coordinate', 'Lon', 'East-West Position'])
            if 'country' in tags:
                aliases.extend(['Country Name', 'Nation', 'Country Code'])
            if 'city' in tags:
                aliases.append('City Name')
            if 'province' in tags:
                aliases.extend(['Province Name', 'State Name'])
            if 'district' in tags:
                aliases.extend(['District Name', 'Locality Name'])
        
        # Classification
        if 'class' in col_lower or 'type' in col_lower:
            aliases.extend([base_alias + ' Category', base_alias + ' Type'])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_aliases = []
        for alias in aliases:
            if alias not in seen and len(alias.split()) <= 6:
                seen.add(alias)
                unique_aliases.append(alias)
        
        return unique_aliases[:5]
    
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
        Generate a human-readable description for a column

        Uses Azure OpenAI GPT-5 (primary) with HuggingFace and template-based fallbacks

        Args:
            column_name: Technical column name
            data_type: Data type of the column
            sample_values: Sample values from the column
            tags: Detected tags for the column
            min_value: Minimum value (for numeric columns)
            max_value: Maximum value (for numeric columns)
            cardinality: Number of distinct values
            table_context: Brief description of what the table contains

        Returns:
            Description string
        """
        # Try Azure OpenAI GPT-5 first (highest quality)
        if self._azure_available and self.azure_generator:
            try:
                ai_description = self.azure_generator.generate_description(
                    column_name,
                    data_type,
                    sample_values,
                    tags,
                    min_value,
                    max_value,
                    cardinality,
                    table_context
                )
                if ai_description and len(ai_description) > 20:
                    logger.info(f"Generated description for {column_name} using Azure OpenAI GPT-5")
                    return ai_description
            except Exception as e:
                logger.warning(f"Azure OpenAI description generation failed: {e}, trying fallback")

        # Try HuggingFace AI generation as fallback
        if self.description_model and self.description_tokenizer:
            try:
                ai_description = self._generate_description_with_ai(
                    column_name,
                    data_type,
                    sample_values,
                    tags,
                    min_value,
                    max_value,
                    cardinality,
                    table_context
                )
                if ai_description and len(ai_description) > 20:
                    return ai_description
            except Exception as e:
                logger.warning(f"HuggingFace description generation failed for {column_name}: {e}")

        # Fallback to template-based
        return self._generate_description_template_based(
            column_name,
            data_type,
            tags,
            cardinality
        )
    
    def _generate_description_with_ai(
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
        """Generate description using AI with rich context"""
        
        # Load models if needed
        if not self._models_loaded:
            self.load_models()
        
        if not self._models_loaded:
            return ""
        
        # Build rich prompt
        prompt = f"""Write a clear, concise description (1-2 sentences) for this database column.

Column: {column_name}
Type: {data_type}
"""
        
        if sample_values and len(sample_values) > 0:
            samples_str = ", ".join([str(v) for v in sample_values[:5]])
            prompt += f"Sample values: {samples_str}\n"
        
        if min_value is not None and max_value is not None:
            prompt += f"Range: {min_value} to {max_value}\n"
        
        if cardinality is not None:
            prompt += f"Distinct values: {cardinality}\n"
        
        if tags and len(tags) > 0:
            prompt += f"Tags: {', '.join(tags)}\n"
        
        if table_context:
            prompt += f"Table purpose: {table_context}\n"
        
        prompt += """
Requirements:
- Write 1-2 clear sentences (max 50 words)
- Explain what this column represents
- Use language understandable to non-technical users
- Do NOT repeat the column name verbatim
- Do NOT mention the table name
- Focus on business meaning, not technical details

Good examples:
- "Unique identifier for top-level administrative regions such as provinces or states."
- "Geographic coordinate representing the north-south position of a location, measured in decimal degrees."
- "Total distance of the road segment measured in kilometers."

Write the description:"""
        
        try:
            # Generate
            inputs = self.description_tokenizer(
                prompt,
                return_tensors="pt",
                max_length=512,
                truncation=True
            )
            
            outputs = self.description_model.generate(
                **inputs,
                max_length=100,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True
            )
            
            result = self.description_tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Clean up result
            result = result.strip()
            
            # Remove common prefixes
            prefixes_to_remove = [
                'the description is:',
                'description:',
                'this column',
                'this is',
            ]
            for prefix in prefixes_to_remove:
                if result.lower().startswith(prefix):
                    result = result[len(prefix):].strip()
            
            # Capitalize first letter
            if result:
                result = result[0].upper() + result[1:]
            
            # Ensure it ends with a period
            if result and not result.endswith('.'):
                result += '.'
            
            return result
        
        except Exception as e:
            logger.warning(f"AI description generation error: {e}")
            return ""
    
    def _generate_description_template_based(
        self,
        column_name: str,
        data_type: str,
        tags: Optional[List[str]] = None,
        cardinality: Optional[int] = None
    ) -> str:
        """Generate description using templates (fallback)"""
        
        col_lower = column_name.lower()
        tags = tags or []
        
        # ID columns
        if any(p in col_lower for p in ['pvid', '_id', 'uuid', 'guid']) or 'identifier' in tags:
            if 'admin' in col_lower or 'administrative_region' in tags:
                if 'l1' in col_lower or 'level1' in col_lower or 'province' in tags:
                    return "Unique identifier for top-level administrative regions such as provinces or states."
                elif 'l2' in col_lower or 'level2' in col_lower:
                    return "Unique identifier for second-level administrative divisions."
                elif 'l3' in col_lower or 'level3' in col_lower or 'city' in tags:
                    return "Unique identifier for third-level administrative areas such as cities or municipalities."
                elif 'l4' in col_lower or 'level4' in col_lower or 'district' in tags:
                    return "Unique identifier for fourth-level administrative areas such as districts or localities."
                else:
                    return "Unique identifier for an administrative region."
            return f"Unique identifier for the {column_name.replace('_', ' ').replace('pvid', '').replace('id', '').strip()} entity."
        
        # Geographic columns
        if 'latitude' in tags:
            return "Geographic coordinate representing the north-south position, measured in decimal degrees (-90 to +90)."
        
        if 'longitude' in tags:
            return "Geographic coordinate representing the east-west position, measured in decimal degrees (-180 to +180)."
        
        if 'country' in tags:
            return "Country name or ISO country code identifying the nation where the record applies."
        
        if 'province' in tags or ('admin' in col_lower and ('level2' in col_lower or 'l2' in col_lower)):
            return "Name of the province, state, or first-level administrative division."
        
        if 'city' in tags or ('admin' in col_lower and ('level3' in col_lower or 'l3' in col_lower)):
            return "Name of the city, town, or municipality."
        
        if 'district' in tags or ('admin' in col_lower and ('level4' in col_lower or 'l4' in col_lower)):
            return "Name of the district, locality, or sub-municipal administrative area."
        
        # Measurement columns
        if 'km' in col_lower or 'kilometer' in col_lower:
            return "Total distance or length measured in kilometers."
        
        # Classification columns
        if 'class' in col_lower or 'type' in col_lower:
            desc = f"Classification or category for {column_name.replace('_', ' ').replace('class', '').replace('type', '').strip()}."
            if cardinality and cardinality < 20:
                desc += f" Contains {cardinality} distinct categories."
            return desc
        
        # Date/time columns
        if 'date' in col_lower or data_type.lower() in ['timestamp', 'date', 'datetime']:
            if 'change' in col_lower or 'update' in col_lower or 'modified' in col_lower:
                return "Date and time when the record was last changed or updated."
            elif 'create' in col_lower or 'insert' in col_lower:
                return "Date and time when the record was created or inserted."
            return f"Date and time value for {column_name.replace('_', ' ')}."
        
        # Generic fallback
        human_name = column_name.replace('_', ' ').title()
        return f"{human_name} value stored as {data_type}."


# Global alias generator instance
alias_generator = AliasGenerator()