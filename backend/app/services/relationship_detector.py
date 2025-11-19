"""
Relationship detector service using Azure OpenAI GPT-4o/GPT-5
Hybrid approach: 3 main types + GPT-defined subtypes for granularity
"""

import json
from typing import Any, Dict, List, Optional

from openai import AzureOpenAI

from app.config import settings
from app.utils.logger import app_logger as logger


class RelationshipDetector:
    """
    Detects relationships between database tables using GPT-4o/GPT-5
    Hybrid approach: Main types (foreign_key, semantic, name_based) + custom subtypes
    """

    def __init__(self):
        """Initialize Azure OpenAI client"""
        self.client = AzureOpenAI(
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            azure_endpoint=settings.azure_openai_endpoint,
        )
        self.deployment = settings.azure_openai_deployment
        self.source_batch_size = 20  # Process 20 source columns at a time

    async def find_relationships(
        self,
        new_table_name: str,
        new_table_metadata: List[Dict[str, Any]],
        existing_tables_metadata: Dict[str, List[Dict[str, Any]]],
        confidence_threshold: float = 0.6,
    ) -> List[Dict[str, Any]]:
        """
        Find relationships using hybrid approach:
        - Batch source table columns (20 at a time)
        - Compare against ONE target table at a time
        - 3 main types + GPT defines subtypes

        Args:
            new_table_name: Full name of new table (catalog.schema.table)
            new_table_metadata: List of column metadata for new table
            existing_tables_metadata: Dict of {table_name: [column_metadata]}
            confidence_threshold: Minimum confidence to include (0-1)

        Returns:
            List of discovered relationships
        """
        logger.info(f"🔍 Finding relationships for {new_table_name}")
        logger.info(f"  New table: {len(new_table_metadata)} columns")
        logger.info(f"  Existing tables: {len(existing_tables_metadata)} tables")

        all_relationships = []

        # Process new table columns in batches
        total_source_batches = (
            len(new_table_metadata) + self.source_batch_size - 1
        ) // self.source_batch_size

        for batch_start in range(0, len(new_table_metadata), self.source_batch_size):
            batch_end = min(
                batch_start + self.source_batch_size, len(new_table_metadata)
            )
            batch_columns = new_table_metadata[batch_start:batch_end]

            batch_num = batch_start // self.source_batch_size + 1

            logger.info(
                f"\n📦 Source Batch {batch_num}/{total_source_batches}: "
                f"Processing {len(batch_columns)} columns ({batch_columns[0].get('column_name')} ... {batch_columns[-1].get('column_name')})"
            )

            # Compare this source batch against EACH target table ONE AT A TIME
            for target_idx, (target_table_name, target_columns) in enumerate(
                existing_tables_metadata.items(), 1
            ):
                logger.info(
                    f"  🎯 Target {target_idx}/{len(existing_tables_metadata)}: "
                    f"Comparing against {target_table_name} ({len(target_columns)} columns)"
                )

                # Find relationships between this source batch and this single target table
                batch_relationships = await self._find_relationships_for_batch(
                    new_table_name,
                    batch_columns,
                    {target_table_name: target_columns},  # Single target table
                )

                # Filter by confidence threshold
                filtered = [
                    rel
                    for rel in batch_relationships
                    if rel["confidence"] >= confidence_threshold
                ]

                if filtered:
                    logger.info(
                        f"    ✅ Found {len(filtered)} relationships with {target_table_name}"
                    )
                    # Log top relationship
                    top_rel = max(filtered, key=lambda x: x["confidence"])
                    subtype_str = (
                        f" ({top_rel.get('relationship_subtype', 'N/A')})"
                        if top_rel.get("relationship_subtype")
                        else ""
                    )
                    logger.info(
                        f"       Top: {top_rel['source_column']} → {top_rel['target_column']} "
                        f"({top_rel['relationship_type']}{subtype_str}, {top_rel['confidence']:.2f})"
                    )
                    all_relationships.extend(filtered)
                else:
                    logger.debug(
                        f"    No high-confidence relationships with {target_table_name}"
                    )

        logger.info(f"\n✅ TOTAL RELATIONSHIPS FOUND: {len(all_relationships)}")

        # Log summary by relationship type and subtype
        if all_relationships:
            by_type = {}
            by_subtype = {}

            for rel in all_relationships:
                rel_type = rel["relationship_type"]
                by_type[rel_type] = by_type.get(rel_type, 0) + 1

                if "relationship_subtype" in rel and rel["relationship_subtype"]:
                    subtype = f"{rel_type}:{rel['relationship_subtype']}"
                    by_subtype[subtype] = by_subtype.get(subtype, 0) + 1

            logger.info("📊 Relationships by main type:")
            for rel_type, count in sorted(by_type.items()):
                logger.info(f"   {rel_type}: {count}")

            if by_subtype:
                logger.info("📊 Relationships by subtype:")
                for subtype, count in sorted(by_subtype.items()):
                    logger.info(f"   {subtype}: {count}")

        return all_relationships

    async def _find_relationships_for_batch(
        self,
        new_table_name: str,
        new_columns: List[Dict[str, Any]],
        target_table_metadata: Dict[str, List[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        """
        Find relationships for a batch of source columns against ONE target table

        Args:
            new_table_name: Full name of new table
            new_columns: Batch of column metadata from new table
            target_table_metadata: Single target table metadata {table_name: [columns]}

        Returns:
            List of discovered relationships
        """
        # Build prompt with metadata
        prompt = self._build_prompt(new_table_name, new_columns, target_table_metadata)

        try:
            # Call GPT-4o/GPT-5
            logger.debug("      Calling Azure OpenAI...")

            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                temperature=1,  # Low temperature for consistent results
                response_format={"type": "json_object"},  # Ensure JSON response
                # No max_completion_tokens - let it generate fully
            )

            # Parse response
            content = response.choices[0].message.content
            result = json.loads(content)

            relationships = result.get("relationships", [])
            logger.debug(
                f"      GPT found {len(relationships)} potential relationships"
            )

            return relationships

        except json.JSONDecodeError as e:
            logger.error(f"      Failed to parse GPT response as JSON: {e}")
            logger.error(f"      Response content: {content[:500]}")
            return []
        except Exception as e:
            logger.error(f"      Failed to detect relationships: {e}")
            return []

    def _get_system_prompt(self) -> str:
        """Get system prompt for GPT with hybrid approach"""
        return """You are an expert database relationship analyzer. Your task is to identify ALL meaningful relationships between database tables by analyzing their column metadata.

Analyze column metadata including:
- Column names and aliases (semantic meaning)
- Data types (must match or be compatible)
- Semantic types (country, city, latitude, longitude, wkt_geometry, state, etc.)
- Descriptions (business context)
- Column types (identifier, dimension, measure, timestamp, detail)
- Cardinality (relationship hints)

## Identify ALL Types of Relationships:

### 1. **foreign_key** (Main Type)
Traditional referential integrity relationships.

**Subtypes you can use:**
- "one_to_many" - Standard FK (orders → customers)
- "many_to_many" - Junction table relationship
- "self_referential" - Same table reference (employee → manager)
- "composite_key" - Multi-column FK

**Criteria:**
- Column names match/similar (customer_id → id)
- Data types compatible
- Source references target identifier
- Cardinality suggests FK (source >= target)

---

### 2. **semantic** (Main Type)
Same business meaning or domain.

**Subtypes you can use:**
- "geographic" - Location-based (country, state, city, lat/lon)
- "temporal" - Time-based (dates, timestamps)
- "hierarchical" - Parent-child categories
- "measurement" - Units/metrics (distance, weight, currency)
- "status_code" - Status/type lookups
- "identifier_mapping" - Different ID systems for same entity
- "enumeration" - Enumerated values/codes

**Criteria:**
- Same semantic_type (country→country, city→city)
- Descriptions indicate same business entity
- Aliases suggest relationship
- Data types match

---

### 3. **name_based** (Main Type)
Similar names suggesting relationship.

**Subtypes you can use:**
- "exact_match" - Identical column names
- "partial_match" - Similar names (product_name → prod_name)
- "business_logic" - Names suggest business connection
- "derived_field" - Calculated/aggregated values

**Criteria:**
- Column names match or very similar
- Data types match
- Business logic suggests connection

---

## IMPORTANT RULES:
1. **Always assign both main type AND subtype**
2. **Create descriptive subtypes** that explain the specific relationship
3. **Be creative** - if none of the example subtypes fit, create your own!
4. Only return relationships with confidence >= 0.6
5. Higher confidence for stronger evidence:
   - semantic_type match + name match = 0.85-0.95
   - semantic_type match alone = 0.75-0.85
   - name match + compatible types = 0.65-0.75
6. Prioritize semantic_type matches over name matches

## Output JSON Format:
{
  "relationships": [
    {
      "source_table": "catalog.schema.table",
      "source_column": "column_name",
      "target_table": "catalog.schema.table",
      "target_column": "column_name",
      "relationship_type": "foreign_key|semantic|name_based",
      "relationship_subtype": "one_to_many|geographic|exact_match|YOUR_CUSTOM_SUBTYPE",
      "confidence": 0.95,
      "reasoning": "Detailed explanation including why you chose this type and subtype"
    }
  ]
}

**Examples:**

```json
{
  "relationship_type": "foreign_key",
  "relationship_subtype": "one_to_many",
  "reasoning": "orders.customer_id (bigint, identifier) references customers.id (bigint, identifier). Classic one-to-many FK relationship."
}
```

```json
{
  "relationship_type": "semantic",
  "relationship_subtype": "geographic",
  "reasoning": "Both columns have semantic_type='country'. sales.country_code (varchar) matches countries.iso_code (varchar) for geographic lookups."
}
```

```json
{
  "relationship_type": "semantic",
  "relationship_subtype": "hierarchical_category",
  "reasoning": "products.category references categories.name in a hierarchical product categorization system."
}
```

Return VALID JSON with relationships array. If no good matches, return empty array."""

    def _build_prompt(
        self,
        new_table_name: str,
        new_columns: List[Dict[str, Any]],
        target_table_metadata: Dict[str, List[Dict[str, Any]]],
    ) -> str:
        """
        Build prompt with table metadata for GPT

        Args:
            new_table_name: Name of new table
            new_columns: Column metadata from new table (batched)
            target_table_metadata: Single target table metadata

        Returns:
            Formatted prompt string
        """
        # Format new table columns
        new_table_section = {
            "table_name": new_table_name,
            "columns": [
                {
                    "name": col.get("column_name"),
                    "data_type": col.get("data_type"),
                    "column_type": col.get("column_type"),
                    "semantic_type": col.get("semantic_type"),
                    "aliases": col.get("alias", ""),
                    "description": col.get("description", ""),
                    "cardinality": col.get("stats", {}).get("cardinality", 0)
                    if col.get("stats")
                    else 0,
                }
                for col in new_columns
            ],
        }

        # Format target table (single table)
        target_table_section = []
        for table_name, columns in target_table_metadata.items():
            table_info = {
                "table_name": table_name,
                "columns": [
                    {
                        "name": col.get("column_name"),
                        "data_type": col.get("data_type"),
                        "column_type": col.get("column_type"),
                        "semantic_type": col.get("semantic_type"),
                        "aliases": col.get("alias", ""),
                        "description": col.get("description", ""),
                        "cardinality": col.get("stats", {}).get("cardinality", 0)
                        if col.get("stats")
                        else 0,
                    }
                    for col in columns
                ],
            }
            target_table_section.append(table_info)

        prompt = f"""Analyze the SOURCE table columns and find ALL meaningful relationships with the TARGET table.

SOURCE TABLE (NEW):
{json.dumps(new_table_section, indent=2)}

TARGET TABLE (EXISTING):
{json.dumps(target_table_section, indent=2)}

Find ANY meaningful relationships including:
- Foreign keys (referential integrity)
- Semantic relationships (same meaning/domain)
- Hierarchical relationships (parent-child)
- Geographic relationships (location-based)
- Temporal relationships (time-based)
- Lookup relationships (reference data)
- Any other meaningful relationship!

For EACH relationship:
1. Assign main type: foreign_key, semantic, or name_based
2. Create a descriptive subtype (e.g., "geographic", "one_to_many", "hierarchical_category")
3. Provide confidence >= 0.6
4. Explain reasoning clearly

Return VALID JSON with relationships array."""

        return prompt


# Global instance
relationship_detector = RelationshipDetector()
