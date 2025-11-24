"""
Neptune Analytics Graph Database Service for storing semantic metadata and relationships
Uses OpenCypher query language and AWS SigV4 authentication
"""

from typing import Any, Dict, List, Optional
import json
import requests
import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest

from app.config import settings
from app.utils.logger import app_logger as logger


class NeptuneAnalyticsService:
    """Service for interacting with Neptune Analytics graph database"""

    def __init__(self):
        """Initialize Neptune Analytics client"""
        self.endpoint = settings.neptune_endpoint
        self.port = settings.neptune_port

        # Neptune Analytics endpoint configuration
        self.base_url = f"https://{self.endpoint}"
        if self.port and self.port != 443:
            self.base_url = f"https://{self.endpoint}:{self.port}"

        # AWS credentials for SigV4 signing
        self.session = boto3.Session()
        self.credentials = self.session.get_credentials()

        logger.info(f"Neptune Analytics service initialized for {self.base_url}")

    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute an OpenCypher query on Neptune Analytics

        Args:
            query: OpenCypher query string
            parameters: Optional query parameters

        Returns:
            Query results
        """
        try:
            url = f"{self.base_url}/opencypher"

            # Prepare request body
            body = {
                "query": query
            }
            if parameters:
                body["parameters"] = parameters

            body_json = json.dumps(body)

            # Prepare headers (Host header is automatically added by requests library)
            headers = {
                'Content-Type': 'application/json'
            }

            # Create AWS request for signing
            request = AWSRequest(
                method='POST',
                url=url,
                data=body_json,
                headers=headers
            )

            # Sign the request with SigV4
            SigV4Auth(self.credentials, 'neptune-graph', 'us-east-1').add_auth(request)

            # Execute the request
            response = requests.post(
                url,
                data=body_json,
                headers=dict(request.headers),
                verify=True  # SSL verification enabled with proper hostname
            )

            response.raise_for_status()
            result = response.json()

            return result.get('results', [])

        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP error executing Neptune Analytics query: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error executing Neptune Analytics query: {e}")
            raise

    # ========== Table Node Operations ==========

    def create_table_node(
        self,
        table_name: str,
        row_count: int,
        column_count: int,
        schema_status: str,
        table_embedding: List[float],
        table_summary: str
    ) -> bool:
        """
        Create or update a table node in Neptune Analytics

        Args:
            table_name: Full table identifier (catalog.schema.table)
            row_count: Number of rows in table
            column_count: Number of columns
            schema_status: Schema status (CURRENT, SCHEMA_CHANGED)
            table_embedding: Embedding vector for the table description
            table_summary: Human-readable summary of the table

        Returns:
            True if successful, False otherwise
        """
        try:
            # Convert embedding to JSON string (Neptune doesn't support large arrays as properties)
            embedding_json = json.dumps(table_embedding)

            # OpenCypher query to merge (upsert) table node
            query = """
            MERGE (t:Table {name: $table_name})
            SET t.row_count = $row_count,
                t.column_count = $column_count,
                t.schema_status = $schema_status,
                t.table_embedding_json = $table_embedding_json,
                t.table_summary = $table_summary,
                t.embedding_dimensions = $embedding_dimensions
            RETURN t
            """

            parameters = {
                'table_name': table_name,
                'row_count': row_count,
                'column_count': column_count,
                'schema_status': schema_status,
                'table_embedding_json': embedding_json,  # Store as JSON string
                'table_summary': table_summary,
                'embedding_dimensions': len(table_embedding)
            }

            self.execute_query(query, parameters)
            logger.info(f"✅ Created/updated table node: {table_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create table node for {table_name}: {e}")
            return False

    def create_column_node(
        self,
        table_name: str,
        column_name: str,
        data_type: str,
        column_type: str,
        semantic_type: Optional[str],
        description: str,
        column_embedding: List[float],
        aliases: List[str],
        cardinality: Optional[int] = None,
        sample_values: Optional[List[str]] = None
    ) -> bool:
        """
        Create or update a column node and link it to its table

        Args:
            table_name: Full table identifier
            column_name: Column name
            data_type: SQL data type
            column_type: Column type (identifier, dimension, measure, etc.)
            semantic_type: Semantic type (geographic, timestamp, etc.)
            description: Column description
            column_embedding: Embedding vector for the column
            aliases: List of human-readable aliases
            cardinality: Number of distinct values
            sample_values: Sample values from the column

        Returns:
            True if successful, False otherwise
        """
        try:
            full_name = f"{table_name}.{column_name}"

            # Convert arrays to JSON strings (Neptune doesn't support large arrays)
            embedding_json = json.dumps(column_embedding)
            aliases_json = json.dumps(aliases)
            sample_values_json = json.dumps(sample_values or [])

            # OpenCypher query to create column node and relationship
            query = """
            MATCH (t:Table {name: $table_name})
            MERGE (c:Column {full_name: $full_name})
            SET c.column_name = $column_name,
                c.data_type = $data_type,
                c.column_type = $column_type,
                c.semantic_type = $semantic_type,
                c.description = $description,
                c.column_embedding_json = $column_embedding_json,
                c.aliases_json = $aliases_json,
                c.cardinality = $cardinality,
                c.sample_values_json = $sample_values_json,
                c.embedding_dimensions = $embedding_dimensions
            MERGE (t)-[:HAS_COLUMN]->(c)
            RETURN c
            """

            parameters = {
                'table_name': table_name,
                'full_name': full_name,
                'column_name': column_name,
                'data_type': data_type,
                'column_type': column_type,
                'semantic_type': semantic_type or '',
                'description': description,
                'column_embedding_json': embedding_json,  # Store as JSON string
                'aliases_json': aliases_json,  # Store as JSON string
                'cardinality': cardinality or 0,
                'sample_values_json': sample_values_json,  # Store as JSON string
                'embedding_dimensions': len(column_embedding)
            }

            self.execute_query(query, parameters)
            logger.info(f"✅ Created/updated column node: {full_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to create column node for {table_name}.{column_name}: {e}")
            return False

    def create_relationship_edge(
        self,
        source_table: str,
        source_column: str,
        target_table: str,
        target_column: str,
        relationship_type: str,
        relationship_subtype: Optional[str],
        confidence: float,
        reasoning: str,
        detected_by: str
    ) -> bool:
        """
        Create a relationship edge between two tables

        Args:
            source_table: Source table name
            source_column: Source column name
            target_table: Target table name
            target_column: Target column name
            relationship_type: Type of relationship (semantic, foreign_key, name_based)
            relationship_subtype: More specific subtype
            confidence: Confidence score (0-1)
            reasoning: Explanation of the relationship
            detected_by: Detection method (e.g., "gpt-5")

        Returns:
            True if successful, False otherwise
        """
        try:
            # OpenCypher query to create relationship edge
            query = """
            MATCH (source:Table {name: $source_table})
            MATCH (target:Table {name: $target_table})
            MERGE (source)-[r:RELATED_TO {
                source_column: $source_column,
                target_column: $target_column
            }]->(target)
            SET r.relationship_type = $relationship_type,
                r.relationship_subtype = $relationship_subtype,
                r.confidence = $confidence,
                r.reasoning = $reasoning,
                r.detected_by = $detected_by
            RETURN r
            """

            parameters = {
                'source_table': source_table,
                'target_table': target_table,
                'source_column': source_column,
                'target_column': target_column,
                'relationship_type': relationship_type,
                'relationship_subtype': relationship_subtype or '',
                'confidence': confidence,
                'reasoning': reasoning,
                'detected_by': detected_by
            }

            self.execute_query(query, parameters)
            logger.info(
                f"✅ Created relationship edge: {source_table}.{source_column} → "
                f"{target_table}.{target_column} ({relationship_type}, {confidence:.2f})"
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to create relationship edge {source_table}.{source_column} → "
                f"{target_table}.{target_column}: {e}"
            )
            return False

    # ========== Query Operations ==========

    def get_table_with_columns(self, table_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a table node with all its columns

        Args:
            table_name: Full table identifier

        Returns:
            Dictionary with table properties and columns
        """
        try:
            query = """
            MATCH (t:Table {name: $table_name})
            OPTIONAL MATCH (t)-[:HAS_COLUMN]->(c:Column)
            RETURN t, collect(c) as columns
            """

            result = self.execute_query(query, {'table_name': table_name})

            if result and len(result) > 0:
                return result[0]
            return None

        except Exception as e:
            logger.error(f"Failed to get table with columns for {table_name}: {e}")
            return None

    def get_table_relationships(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get all relationships for a table

        Args:
            table_name: Full table identifier

        Returns:
            List of relationship dictionaries
        """
        try:
            query = """
            MATCH (source:Table {name: $table_name})-[r:RELATED_TO]->(target:Table)
            RETURN source.name as source, target.name as target, properties(r) as relationship
            """

            result = self.execute_query(query, {'table_name': table_name})
            return result or []

        except Exception as e:
            logger.error(f"Failed to get relationships for {table_name}: {e}")
            return []

    def get_all_tables(self) -> List[str]:
        """
        Get all table names in the graph

        Returns:
            List of table names
        """
        try:
            query = "MATCH (t:Table) RETURN t.name as name"
            result = self.execute_query(query)
            return [r['name'] for r in result] if result else []

        except Exception as e:
            logger.error(f"Failed to get all tables: {e}")
            return []

    def delete_table(self, table_name: str) -> bool:
        """
        Delete a table node and all its columns and relationships

        Args:
            table_name: Full table identifier

        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete table, its columns, and all relationships
            query = """
            MATCH (t:Table {name: $table_name})
            OPTIONAL MATCH (t)-[:HAS_COLUMN]->(c:Column)
            DETACH DELETE t, c
            """

            self.execute_query(query, {'table_name': table_name})
            logger.info(f"✅ Deleted table node and columns: {table_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete table {table_name}: {e}")
            return False

    def search_similar_tables(
        self,
        query_embedding: List[float],
        limit: int = 5,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search for similar tables using vector similarity on embeddings

        NOTE: This requires Neptune Analytics vector index to be configured.
        Embeddings are stored as JSON strings, so vector similarity needs special handling.
        For now, this is a placeholder - implement after setting up vector index.

        Args:
            query_embedding: The embedding vector to search with
            limit: Maximum number of results to return
            threshold: Minimum similarity threshold (0-1)

        Returns:
            List of similar tables with similarity scores
        """
        try:
            logger.warning("Vector similarity search not yet implemented - requires Neptune vector index setup")
            # TODO: Implement with Neptune Analytics vector index
            # Will need to decode JSON embeddings and use Neptune's vector similarity
            return []

        except Exception as e:
            logger.error(f"Failed to search similar tables: {e}")
            return []

    def search_similar_columns(
        self,
        query_embedding: List[float],
        limit: int = 10,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Search for similar columns using vector similarity on embeddings

        NOTE: This requires Neptune Analytics vector index to be configured.
        Embeddings are stored as JSON strings, so vector similarity needs special handling.
        For now, this is a placeholder - implement after setting up vector index.

        Args:
            query_embedding: The embedding vector to search with
            limit: Maximum number of results to return
            threshold: Minimum similarity threshold (0-1)

        Returns:
            List of similar columns with similarity scores
        """
        try:
            logger.warning("Vector similarity search not yet implemented - requires Neptune vector index setup")
            # TODO: Implement with Neptune Analytics vector index
            # Will need to decode JSON embeddings and use Neptune's vector similarity
            return []

        except Exception as e:
            logger.error(f"Failed to search similar columns: {e}")
            return []


# Global Neptune Analytics service instance
neptune_service = NeptuneAnalyticsService()
