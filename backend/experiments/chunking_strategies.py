"""
Chunking strategies for vector store comparison experiments

Defines different ways to format table and column metadata into text for embedding.
Each strategy produces different document structures to test which yields better similarity scores.
"""

from typing import Dict, List, Any, Optional


class ChunkingStrategy:
    """Base class for chunking strategies"""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    def format_table(self, table_metadata: Dict[str, Any], columns: List[Dict[str, Any]]) -> str:
        """Format table metadata into text for embedding"""
        raise NotImplementedError

    def format_column(self, table_name: str, column_metadata: Dict[str, Any], table_context: Optional[str] = None) -> str:
        """Format column metadata into text for embedding"""
        raise NotImplementedError

    def get_chunks(self, table_metadata: Dict[str, Any], columns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Generate chunks for this table

        Returns:
            List of chunks, each with:
            - text: The text to embed
            - type: 'table' or 'column' or 'combined'
            - metadata: Original metadata for reference
        """
        raise NotImplementedError


class BaselineStrategy(ChunkingStrategy):
    """
    Strategy 1: Same as Neptune (Baseline)

    Matches the exact format used in embedding_service.py:
    - Separate vectors for each table and each column
    - Use exact same text formatting as Neptune
    """

    def __init__(self):
        super().__init__(
            name="baseline",
            description="Exact match to current Neptune formatting (separate table and column vectors)"
        )

    def format_table(self, table_metadata: Dict[str, Any], columns: List[Dict[str, Any]]) -> str:
        """Format table exactly like Neptune's generate_table_embedding"""
        table_name = table_metadata['catalog_schema_table']
        parts = table_name.split('.')
        catalog, schema, table = parts[0], parts[1], parts[2] if len(parts) == 3 else ('', '', table_name)

        # Get column summaries (first 15)
        column_summaries = []
        for col in columns[:15]:
            col_name = col['column_name']
            data_type = col.get('data_type', 'unknown')
            col_type = col.get('column_type', 'unknown')
            semantic = col.get('semantic_type', '')
            aliases = col.get('aliases', [])

            semantic_str = f" - {semantic}" if semantic else ""
            aliases_str = f" (aliases: {', '.join(aliases[:2])})" if aliases else ""

            column_summaries.append(
                f"{col_name} ({data_type}, {col_type}{semantic_str}){aliases_str}"
            )

        # Build the summary text
        summary = f"""Table: {table_name}
Catalog: {catalog}, Schema: {schema}, Table: {table}
Row count: {table_metadata.get('row_count', 0):,}
Column count: {table_metadata.get('column_count', 0)}
Schema status: {table_metadata.get('schema_status', 'CURRENT')}

Columns:
{chr(10).join(column_summaries)}
{"... and more columns" if len(columns) > 15 else ""}

Purpose: Database table containing structured data with {table_metadata.get('column_count', 0)} attributes across {table_metadata.get('row_count', 0):,} records.""".strip()

        return summary

    def format_column(self, table_name: str, column_metadata: Dict[str, Any], table_context: Optional[str] = None) -> str:
        """Format column exactly like Neptune's generate_column_embedding"""
        col_name = column_metadata.get('column_name', 'unknown')
        col_type = column_metadata.get('column_type', 'unknown')
        semantic = column_metadata.get('semantic_type', 'none')
        data_type = column_metadata.get('data_type', 'unknown')
        description = column_metadata.get('description', 'No description')
        aliases = column_metadata.get('aliases', [])
        cardinality = column_metadata.get('cardinality')
        null_percentage = column_metadata.get('null_percentage', 0)
        sample_values = column_metadata.get('sample_values', [])

        # Format aliases
        aliases_str = ", ".join(aliases[:3]) if aliases else "none"

        # Format sample values
        sample_values_list = sample_values[:5] if sample_values else []
        sample_str = ", ".join(str(v) for v in sample_values_list) if sample_values_list else "no samples"

        # Build the description text (without table context for baseline)
        col_description = f"""Column: {col_name} in table {table_name}
Data type: {data_type}
Column type: {col_type}
Semantic type: {semantic}
Description: {description}
Aliases: {aliases_str}
Cardinality: {cardinality if cardinality else 'unknown'}
Null percentage: {null_percentage:.1f}%
Sample values: {sample_str}

Purpose: A {col_type} column that stores {semantic} data, used for {'identification' if col_type == 'identifier' else 'analysis and filtering'}.""".strip()

        return col_description

    def get_chunks(self, table_metadata: Dict[str, Any], columns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate separate chunks for table and each column"""
        chunks = []
        table_name = table_metadata['catalog_schema_table']

        # Table chunk
        table_text = self.format_table(table_metadata, columns)
        chunks.append({
            'text': table_text,
            'type': 'table',
            'id': table_name,
            'metadata': table_metadata
        })

        # Column chunks
        for col in columns:
            col_text = self.format_column(table_name, col)
            chunks.append({
                'text': col_text,
                'type': 'column',
                'id': f"{table_name}.{col['column_name']}",
                'metadata': col
            })

        return chunks


class RichColumnStrategy(ChunkingStrategy):
    """
    Strategy 2: Richer Column Representation

    Include more metadata in column text:
    - Add semantic tags
    - Include more sample values
    - Add distinctness metrics
    """

    def __init__(self):
        super().__init__(
            name="rich_column",
            description="Enhanced column representation with more metadata context"
        )

    def format_table(self, table_metadata: Dict[str, Any], columns: List[Dict[str, Any]]) -> str:
        """Same as baseline for tables"""
        baseline = BaselineStrategy()
        return baseline.format_table(table_metadata, columns)

    def format_column(self, table_name: str, column_metadata: Dict[str, Any], table_context: Optional[str] = None) -> str:
        """Enhanced column format with more context"""
        col_name = column_metadata.get('column_name', 'unknown')
        col_type = column_metadata.get('column_type', 'unknown')
        semantic = column_metadata.get('semantic_type', 'none')
        data_type = column_metadata.get('data_type', 'unknown')
        description = column_metadata.get('description', 'No description')
        aliases = column_metadata.get('aliases', [])
        semantic_tags = column_metadata.get('semantic_tags', [])
        cardinality = column_metadata.get('cardinality', 0)
        distinct_count = column_metadata.get('distinct_count', 0)
        null_percentage = column_metadata.get('null_percentage', 0)
        sample_values = column_metadata.get('sample_values', [])
        min_value = column_metadata.get('min_value')
        max_value = column_metadata.get('max_value')

        # Format aliases and tags
        aliases_str = ", ".join(aliases[:5]) if aliases else "none"
        tags_str = ", ".join(semantic_tags[:5]) if semantic_tags else "none"

        # Format sample values (more samples)
        sample_values_list = sample_values[:10] if sample_values else []
        sample_str = ", ".join(str(v) for v in sample_values_list) if sample_values_list else "no samples"

        # Build range info if available
        range_info = ""
        if min_value is not None and max_value is not None:
            range_info = f"\nValue range: {min_value} to {max_value}"

        # Calculate distinctness percentage
        distinctness = ""
        if distinct_count and cardinality:
            distinctness = f"\nDistinctness: {(distinct_count / cardinality * 100):.1f}% ({distinct_count:,} distinct values)"

        col_description = f"""Column: {col_name} in table {table_name}
Data type: {data_type}
Column type: {col_type}
Semantic type: {semantic}
Description: {description}
Semantic tags: {tags_str}
Aliases: {aliases_str}
Cardinality: {cardinality:,} if cardinality else 'unknown'
Null percentage: {null_percentage:.1f}%{distinctness}{range_info}
Sample values: {sample_str}

Purpose: A {col_type} column that stores {semantic} data, used for {'identification' if col_type == 'identifier' else 'analysis and filtering'}. This column has {cardinality:,} total values with {null_percentage:.1f}% nulls.""".strip()

        return col_description

    def get_chunks(self, table_metadata: Dict[str, Any], columns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate separate chunks for table and each column"""
        chunks = []
        table_name = table_metadata['catalog_schema_table']

        # Table chunk
        table_text = self.format_table(table_metadata, columns)
        chunks.append({
            'text': table_text,
            'type': 'table',
            'id': table_name,
            'metadata': table_metadata
        })

        # Column chunks with richer format
        for col in columns:
            col_text = self.format_column(table_name, col)
            chunks.append({
                'text': col_text,
                'type': 'column',
                'id': f"{table_name}.{col['column_name']}",
                'metadata': col
            })

        return chunks


class TableWithColumnsStrategy(ChunkingStrategy):
    """
    Strategy 3: Table + All Columns Combined

    Single vector per table with all column information included.
    This captures the full context in one chunk.
    """

    def __init__(self):
        super().__init__(
            name="table_with_columns",
            description="Single combined chunk per table including all column details"
        )

    def format_table_with_columns(self, table_metadata: Dict[str, Any], columns: List[Dict[str, Any]]) -> str:
        """Format table with all columns in one chunk"""
        table_name = table_metadata['catalog_schema_table']
        parts = table_name.split('.')
        catalog, schema, table = parts[0], parts[1], parts[2] if len(parts) == 3 else ('', '', table_name)

        # Build detailed column descriptions
        column_details = []
        for idx, col in enumerate(columns, 1):
            col_name = col['column_name']
            data_type = col.get('data_type', 'unknown')
            col_type = col.get('column_type', 'unknown')
            description = col.get('description', 'No description')
            semantic_tags = col.get('semantic_tags', [])
            aliases = col.get('aliases', [])
            sample_values = col.get('sample_values', [])

            tags_str = ", ".join(semantic_tags[:3]) if semantic_tags else "none"
            sample_str = ", ".join(str(v) for v in sample_values[:3]) if sample_values else "no samples"
            aliases_str = f" (aliases: {', '.join(aliases[:2])})" if aliases else ""

            column_details.append(
                f"{idx}. {col_name}{aliases_str}: {description}. Type: {data_type} ({col_type}). Tags: {tags_str}. Samples: {sample_str}"
            )

        # Build comprehensive text
        text = f"""Table: {table_name}
Catalog: {catalog}, Schema: {schema}, Table: {table}
Row count: {table_metadata.get('row_count', 0):,}
Column count: {table_metadata.get('column_count', 0)}
Schema status: {table_metadata.get('schema_status', 'CURRENT')}
Search mode: {table_metadata.get('search_mode', 'N/A')}

Columns ({len(columns)} total):
{chr(10).join(column_details)}

Purpose: Database table containing structured data with {table_metadata.get('column_count', 0)} attributes across {table_metadata.get('row_count', 0):,} records. This table includes columns for {', '.join(set(col.get('column_type', 'unknown') for col in columns[:5]))}.
""".strip()

        return text

    def get_chunks(self, table_metadata: Dict[str, Any], columns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate single combined chunk per table"""
        table_name = table_metadata['catalog_schema_table']

        text = self.format_table_with_columns(table_metadata, columns)

        return [{
            'text': text,
            'type': 'combined',
            'id': table_name,
            'metadata': {
                'table': table_metadata,
                'columns': columns
            }
        }]


class SemanticGroupingStrategy(ChunkingStrategy):
    """
    Strategy 4: Semantic Grouping

    Group columns by semantic tags and create thematic chunks.
    E.g., all location columns together, all business columns together.
    """

    def __init__(self):
        super().__init__(
            name="semantic_grouping",
            description="Group columns by semantic type into thematic chunks"
        )

    def get_chunks(self, table_metadata: Dict[str, Any], columns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate chunks grouped by semantic type"""
        chunks = []
        table_name = table_metadata['catalog_schema_table']

        # Group columns by semantic type
        groups = {}
        for col in columns:
            col_type = col.get('column_type', 'unknown')
            semantic = col.get('semantic_type', 'general')

            # Use column_type as primary grouping, semantic_type as secondary
            key = f"{col_type}"
            if semantic and semantic != 'none':
                key = f"{col_type}_{semantic}"

            if key not in groups:
                groups[key] = []
            groups[key].append(col)

        # Create table overview chunk
        baseline = BaselineStrategy()
        table_text = baseline.format_table(table_metadata, columns)
        chunks.append({
            'text': table_text,
            'type': 'table_overview',
            'id': table_name,
            'metadata': table_metadata
        })

        # Create semantic group chunks
        for group_key, group_cols in groups.items():
            col_names = [col['column_name'] for col in group_cols]
            col_descriptions = []

            for col in group_cols:
                desc = col.get('description', 'No description')
                aliases = col.get('aliases', [])
                aliases_str = f" (also known as: {', '.join(aliases[:2])})" if aliases else ""
                col_descriptions.append(f"- {col['column_name']}{aliases_str}: {desc}")

            group_text = f"""Table: {table_name} - {group_key.replace('_', ' ').title()} Columns

This table contains the following {group_key.replace('_', ' ')} columns:
{', '.join(col_names)}

Column details:
{chr(10).join(col_descriptions)}

These columns are part of the {table_name} table which has {table_metadata.get('row_count', 0):,} rows.
Purpose: These {len(group_cols)} {group_key.replace('_', ' ')} columns provide data for analysis and reporting.""".strip()

            chunks.append({
                'text': group_text,
                'type': 'semantic_group',
                'id': f"{table_name}_{group_key}",
                'metadata': {
                    'table_name': table_name,
                    'group_type': group_key,
                    'columns': group_cols
                }
            })

        return chunks


# Strategy registry
STRATEGIES = {
    'baseline': BaselineStrategy(),
    'rich_column': RichColumnStrategy(),
    'table_with_columns': TableWithColumnsStrategy(),
    'semantic_grouping': SemanticGroupingStrategy()
}


def get_strategy(name: str) -> ChunkingStrategy:
    """Get a chunking strategy by name"""
    if name not in STRATEGIES:
        raise ValueError(f"Unknown strategy: {name}. Available: {list(STRATEGIES.keys())}")
    return STRATEGIES[name]
