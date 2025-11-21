"""
OpenAI Embedding Service for generating vector embeddings of metadata
Used for RAG (Retrieval Augmented Generation) with Neptune graph database
"""

from typing import List, Dict, Any, Optional
from openai import AzureOpenAI

from app.config import settings
from app.models import TableMetadata, ColumnMetadata
from app.utils.logger import app_logger as logger


class EmbeddingService:
    """Service for generating embeddings using Azure OpenAI"""

    def __init__(self):
        """Initialize Azure OpenAI client"""
        self.client = None
        self.model = settings.openai_embedding_model
        logger.info(f"Embedding service initialized with model: {self.model}")

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
            logger.info("Azure OpenAI client initialized for embeddings")

        return self.client

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text

        Args:
            text: Text to embed

        Returns:
            List of floats representing the embedding vector (1536 dimensions for text-embedding-3-small)
        """
        try:
            client = self._get_client()

            # Call OpenAI API
            response = client.embeddings.create(
                model=self.model,
                input=text
            )

            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding of {len(embedding)} dimensions")

            return embedding

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    def generate_table_embedding(
        self,
        table_metadata: TableMetadata,
        columns: Dict[str, ColumnMetadata]
    ) -> tuple[List[float], str]:
        """
        Generate embedding for a table based on its metadata

        Args:
            table_metadata: Table metadata object
            columns: Dictionary of column metadata

        Returns:
            Tuple of (embedding vector, summary text that was embedded)
        """
        try:
            # Build comprehensive table summary for embedding
            table_name = table_metadata.catalog_schema_table
            parts = table_name.split('.')
            catalog, schema, table = parts[0], parts[1], parts[2] if len(parts) == 3 else ('', '', table_name)

            # Get column summaries
            column_summaries = []
            for col_name, col in columns.items():
                col_type = col.column_type if col.column_type else "unknown"
                semantic = f" - {col.semantic_type}" if col.semantic_type else ""
                aliases_str = f" (aliases: {', '.join(col.aliases[:2])})" if col.aliases else ""

                column_summaries.append(
                    f"{col_name} ({col.data_type}, {col_type}{semantic}){aliases_str}"
                )

            # Build the summary text
            summary = f"""
Table: {table_name}
Catalog: {catalog}, Schema: {schema}, Table: {table}
Row count: {table_metadata.row_count:,}
Column count: {table_metadata.column_count}
Schema status: {table_metadata.schema_status.value}

Columns:
{chr(10).join(column_summaries[:15])}
{"... and more columns" if len(column_summaries) > 15 else ""}

Purpose: Database table containing structured data with {table_metadata.column_count} attributes across {table_metadata.row_count:,} records.
            """.strip()

            # Generate embedding
            embedding = self.generate_embedding(summary)

            logger.info(f"✅ Generated table embedding for {table_name} ({len(embedding)} dims)")

            return embedding, summary

        except Exception as e:
            logger.error(f"Failed to generate table embedding for {table_metadata.catalog_schema_table}: {e}")
            raise

    def generate_column_embedding(
        self,
        table_name: str,
        column_metadata: ColumnMetadata
    ) -> tuple[List[float], str]:
        """
        Generate embedding for a column based on its metadata

        Args:
            table_name: Full table identifier
            column_metadata: Column metadata object

        Returns:
            Tuple of (embedding vector, description text that was embedded)
        """
        try:
            # Build comprehensive column description for embedding
            col_name = column_metadata.column_name
            col_type = column_metadata.column_type if column_metadata.column_type else "unknown"
            semantic = column_metadata.semantic_type if column_metadata.semantic_type else "none"

            # Format aliases
            aliases_str = ", ".join(column_metadata.aliases[:3]) if column_metadata.aliases else "none"

            # Format sample values
            sample_values = column_metadata.sample_values[:5] if column_metadata.sample_values else []
            sample_str = ", ".join(str(v) for v in sample_values) if sample_values else "no samples"

            # Build the description text
            description = f"""
Column: {col_name} in table {table_name}
Data type: {column_metadata.data_type}
Column type: {col_type}
Semantic type: {semantic}
Description: {column_metadata.description}
Aliases: {aliases_str}
Cardinality: {column_metadata.cardinality if column_metadata.cardinality else 'unknown'}
Null percentage: {column_metadata.null_percentage:.1f}% if column_metadata.null_percentage else 0
Sample values: {sample_str}

Purpose: A {col_type} column that stores {semantic} data, used for {'identification' if col_type == 'identifier' else 'analysis and filtering'}.
            """.strip()

            # Generate embedding
            embedding = self.generate_embedding(description)

            logger.info(f"✅ Generated column embedding for {table_name}.{col_name} ({len(embedding)} dims)")

            return embedding, description

        except Exception as e:
            logger.error(f"Failed to generate column embedding for {table_name}.{column_metadata.column_name}: {e}")
            raise

    def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in a single API call (more efficient)

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        try:
            client = self._get_client()

            # Call OpenAI API with batch
            response = client.embeddings.create(
                model=self.model,
                input=texts
            )

            embeddings = [item.embedding for item in response.data]
            logger.info(f"✅ Generated {len(embeddings)} embeddings in batch")

            return embeddings

        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {e}")
            raise


# Global embedding service instance
embedding_service = EmbeddingService()
