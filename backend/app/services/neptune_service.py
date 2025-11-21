"""
Neptune Graph Database Service for storing semantic metadata and relationships
Uses Gremlin traversal language for graph operations
"""

from typing import Any, Dict, List, Optional
from gremlin_python.driver import client, serializer
from gremlin_python.driver.protocol import GremlinServerError
import json

from app.config import settings
from app.utils.logger import app_logger as logger


class NeptuneService:
    """Service for interacting with Neptune graph database"""

    def __init__(self):
        """Initialize Neptune/Gremlin client"""
        self.endpoint = settings.neptune_endpoint
        self.port = settings.neptune_port

        # Build Neptune endpoint URL
        self.neptune_url = f'wss://{self.endpoint}:{self.port}/gremlin'

        # For local development with SSH tunnel, use ws:// instead of wss://
        if self.endpoint == 'localhost':
            self.neptune_url = f'ws://{self.endpoint}:{self.port}/gremlin'

        self.client = None
        logger.info(f"Neptune service initialized for {self.neptune_url}")

    def connect(self):
        """Establish connection to Neptune"""
        try:
            if self.client is None:
                self.client = client.Client(
                    self.neptune_url,
                    'g',
                    message_serializer=serializer.GraphSONSerializersV2d0()
                )
                logger.info("Successfully connected to Neptune")
            return self.client
        except Exception as e:
            logger.error(f"Failed to connect to Neptune: {e}")
            raise

    def close(self):
        """Close Neptune connection"""
        if self.client:
            self.client.close()
            self.client = None
            logger.info("Neptune connection closed")

    def execute_query(self, query: str, bindings: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute a Gremlin query

        Args:
            query: Gremlin query string
            bindings: Optional parameter bindings

        Returns:
            Query result
        """
        try:
            if self.client is None:
                self.connect()

            result = self.client.submit(query, bindings or {})
            return result.all().result()

        except GremlinServerError as e:
            logger.error(f"Gremlin server error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error executing Neptune query: {e}")
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
        Create or update a table node in Neptune

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
            # Convert embedding to JSON string for storage
            embedding_json = json.dumps(table_embedding)

            # Gremlin query to upsert table node
            query = """
            g.V().has('table', 'name', table_name).fold()
                .coalesce(
                    unfold(),
                    addV('table').property('name', table_name)
                )
                .property('row_count', row_count)
                .property('column_count', column_count)
                .property('schema_status', schema_status)
                .property('table_embedding', table_embedding)
                .property('table_summary', table_summary)
            """

            bindings = {
                'table_name': table_name,
                'row_count': row_count,
                'column_count': column_count,
                'schema_status': schema_status,
                'table_embedding': embedding_json,
                'table_summary': table_summary
            }

            self.execute_query(query, bindings)
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
            # Convert arrays to JSON strings
            embedding_json = json.dumps(column_embedding)
            aliases_json = json.dumps(aliases)
            sample_values_json = json.dumps(sample_values or [])

            # Create column node
            column_query = """
            g.V().has('column', 'full_name', full_name).fold()
                .coalesce(
                    unfold(),
                    addV('column').property('full_name', full_name)
                )
                .property('column_name', column_name)
                .property('data_type', data_type)
                .property('column_type', column_type)
                .property('semantic_type', semantic_type)
                .property('description', description)
                .property('column_embedding', column_embedding)
                .property('aliases', aliases)
                .property('cardinality', cardinality)
                .property('sample_values', sample_values)
            """

            full_name = f"{table_name}.{column_name}"

            column_bindings = {
                'full_name': full_name,
                'column_name': column_name,
                'data_type': data_type,
                'column_type': column_type,
                'semantic_type': semantic_type or '',
                'description': description,
                'column_embedding': embedding_json,
                'aliases': aliases_json,
                'cardinality': cardinality or 0,
                'sample_values': sample_values_json
            }

            self.execute_query(column_query, column_bindings)

            # Create edge from table to column
            edge_query = """
            g.V().has('table', 'name', table_name).as('t')
                .V().has('column', 'full_name', full_name).as('c')
                .coalesce(
                    __.select('t').outE('HAS_COLUMN').where(inV().as('c')),
                    __.select('t').addE('HAS_COLUMN').to('c')
                )
            """

            edge_bindings = {
                'table_name': table_name,
                'full_name': full_name
            }

            self.execute_query(edge_query, edge_bindings)
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
            # Create relationship edge between tables
            query = """
            g.V().has('table', 'name', source_table).as('source')
                .V().has('table', 'name', target_table).as('target')
                .coalesce(
                    __.select('source').outE('RELATED_TO')
                        .has('source_column', source_column)
                        .has('target_column', target_column)
                        .where(inV().as('target')),
                    __.select('source').addE('RELATED_TO').to('target')
                        .property('source_column', source_column)
                        .property('target_column', target_column)
                )
                .property('relationship_type', relationship_type)
                .property('relationship_subtype', relationship_subtype)
                .property('confidence', confidence)
                .property('reasoning', reasoning)
                .property('detected_by', detected_by)
            """

            bindings = {
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

            self.execute_query(query, bindings)
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
            g.V().has('table', 'name', table_name)
                .project('table', 'columns')
                .by(valueMap(true))
                .by(out('HAS_COLUMN').valueMap(true).fold())
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
            g.V().has('table', 'name', table_name)
                .outE('RELATED_TO')
                .project('source', 'target', 'relationship')
                .by(outV().values('name'))
                .by(inV().values('name'))
                .by(valueMap(true))
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
            query = "g.V().hasLabel('table').values('name')"
            result = self.execute_query(query)
            return result or []

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
            # Delete all columns first
            query = """
            g.V().has('table', 'name', table_name)
                .out('HAS_COLUMN').drop()
            """
            self.execute_query(query, {'table_name': table_name})

            # Delete the table and its edges
            query = """
            g.V().has('table', 'name', table_name).drop()
            """
            self.execute_query(query, {'table_name': table_name})

            logger.info(f"✅ Deleted table node and columns: {table_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete table {table_name}: {e}")
            return False


# Global Neptune service instance
neptune_service = NeptuneService()
