"""
API endpoints for semantic search using Neptune vector similarity
"""
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from app.services.embedding_service import embedding_service
from app.services.neptune_service import neptune_service, pad_embedding_to_2048
from app.services.dynamodb import dynamodb_service
from app.services.dynamodb_relationships import relationships_service
from app.utils.logger import app_logger as logger

router = APIRouter(prefix="/api", tags=["search"])


# ========== Request/Response Models ==========

class SemanticSearchRequest(BaseModel):
    """Request model for semantic search"""
    query: str = Field(..., description="Natural language query", min_length=1)
    threshold: float = Field(default=0.40, ge=0.0, le=1.0, description="Similarity threshold (0-1)")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "geographic data",
                "threshold": 0.40
            }
        }


class TableMetadataResponse(BaseModel):
    """Table metadata in search response"""
    catalog_schema_table: str
    row_count: int
    column_count: int
    schema_status: str
    enrichment_status: str
    relationship_detection_status: str
    neptune_import_status: str
    similarity_score: float


class ColumnMetadataResponse(BaseModel):
    """Column metadata in search response"""
    catalog_schema_table: str
    column_name: str
    data_type: str
    column_type: str
    semantic_type: Optional[str]
    description: str
    aliases: List[str]
    cardinality: Optional[int]
    null_percentage: Optional[float]
    sample_values: List[Any]
    # Stats columns (from DynamoDB, not in Neptune)
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    avg_value: Optional[Any] = None
    similarity_score: float


class RelationshipResponse(BaseModel):
    """Relationship in search response"""
    source_table: str
    source_column: str
    target_table: str
    target_column: str
    relationship_type: str
    relationship_subtype: Optional[str]
    confidence: float
    reasoning: str
    detected_by: str


class SemanticSearchResponse(BaseModel):
    """Response model for semantic search"""
    query: str
    threshold: float
    query_too_vague: bool
    relationships: List[RelationshipResponse]
    metadata: Dict[str, Any]  # Contains 'tables' and 'columns' lists

    class Config:
        json_schema_extra = {
            "example": {
                "query": "geographic data",
                "threshold": 0.40,
                "query_too_vague": False,
                "relationships": [
                    {
                        "source_table": "table_a",
                        "source_column": "country",
                        "target_table": "table_b",
                        "target_column": "country",
                        "relationship_type": "semantic",
                        "relationship_subtype": "geographic",
                        "confidence": 0.95,
                        "reasoning": "Both columns represent country names",
                        "detected_by": "gpt-5"
                    }
                ],
                "metadata": {
                    "tables": [],
                    "columns": []
                }
            }
        }


# ========== API Endpoints ==========

@router.post(
    "/search/semantic",
    response_model=SemanticSearchResponse,
    responses={400: {"description": "Invalid request"}, 500: {"description": "Server error"}}
)
async def semantic_search(request: SemanticSearchRequest = Body(...)):
    """
    Perform semantic search using natural language queries

    This endpoint:
    1. Converts the query to a vector embedding
    2. Searches Neptune Analytics for similar tables and columns
    3. Fetches full metadata from DynamoDB (including stats)
    4. Returns relationships between matched tables

    Only searches tables that have been imported to Neptune (neptune_import_status = 'imported').

    Args:
        request: SemanticSearchRequest with query and optional threshold

    Returns:
        SemanticSearchResponse with relationships and metadata
    """
    try:
        logger.info(f"Semantic search query: '{request.query}' (threshold: {request.threshold})")

        # Step 1: Generate embedding for the query
        query_embedding = embedding_service.generate_embedding(request.query)
        logger.info(f"Generated query embedding: {len(query_embedding)} dimensions")

        # Step 2: Pad to 2048 dimensions for Neptune
        query_embedding_padded = pad_embedding_to_2048(query_embedding)

        # Step 3: Search Neptune for similar tables
        matched_tables = search_tables_by_similarity(query_embedding_padded, request.threshold)
        logger.info(f"Found {len(matched_tables)} matching tables")

        # Step 4: Search Neptune for similar columns
        matched_columns = search_columns_by_similarity(query_embedding_padded, request.threshold)
        logger.info(f"Found {len(matched_columns)} matching columns")

        # Check if query was too vague (no results)
        if not matched_tables and not matched_columns:
            logger.warning(f"No results found for query: '{request.query}'")
            return SemanticSearchResponse(
                query=request.query,
                threshold=request.threshold,
                query_too_vague=True,
                relationships=[],
                metadata={"tables": [], "columns": []}
            )

        # Step 5: Fetch full metadata from DynamoDB for matched tables
        table_metadata_list = []
        for table_name, similarity in matched_tables:
            table_metadata = dynamodb_service.get_table_metadata(table_name)
            if table_metadata:
                table_metadata_list.append(TableMetadataResponse(
                    catalog_schema_table=table_metadata.catalog_schema_table,
                    row_count=table_metadata.row_count,
                    column_count=table_metadata.column_count,
                    schema_status=table_metadata.schema_status.value,
                    enrichment_status=table_metadata.enrichment_status.value,
                    relationship_detection_status=table_metadata.relationship_detection_status.value,
                    neptune_import_status=table_metadata.neptune_import_status.value,
                    similarity_score=similarity
                ))

        # Step 6: Batch fetch full metadata from DynamoDB for matched columns (including stats)
        column_metadata_list = []

        # Build list of (table_name, column_name, similarity) tuples
        column_keys_with_similarity = []
        for column_full_name, similarity in matched_columns:
            parts = column_full_name.rsplit('.', 1)
            if len(parts) == 2:
                table_name, column_name = parts
                column_keys_with_similarity.append((table_name, column_name, similarity))

        # Batch fetch column metadata
        column_keys = [(table, col) for table, col, _ in column_keys_with_similarity]
        columns_batch = dynamodb_service.batch_get_column_metadata(column_keys)

        # Create a lookup map for similarity scores
        similarity_map = {f"{table}.{col}": sim for table, col, sim in column_keys_with_similarity}

        # Build response objects
        for column_metadata in columns_batch:
            full_name = f"{column_metadata.catalog_schema_table}.{column_metadata.column_name}"
            similarity = similarity_map.get(full_name, 0.0)

            column_metadata_list.append(ColumnMetadataResponse(
                catalog_schema_table=column_metadata.catalog_schema_table,
                column_name=column_metadata.column_name,
                data_type=column_metadata.data_type,
                column_type=column_metadata.column_type,
                semantic_type=column_metadata.semantic_type,
                description=column_metadata.description,
                aliases=column_metadata.aliases,
                cardinality=column_metadata.cardinality,
                null_percentage=column_metadata.null_percentage,
                sample_values=column_metadata.sample_values,
                # Stats columns from DynamoDB (not in Neptune)
                min_value=column_metadata.min_value,
                max_value=column_metadata.max_value,
                avg_value=column_metadata.avg_value,
                similarity_score=similarity
            ))

        # Step 7: Fetch relationships between matched tables (only A↔B, not A↔C)
        # Include tables that matched directly AND tables that have matched columns
        matched_table_names = [t for t, _ in matched_tables]

        # Extract table names from matched columns
        for column_full_name, _ in matched_columns:
            parts = column_full_name.rsplit('.', 1)
            if len(parts) == 2:
                table_name = parts[0]
                if table_name not in matched_table_names:
                    matched_table_names.append(table_name)

        relationships_list = []

        if len(matched_table_names) >= 2:
            # Batch fetch all relationships for matched tables
            all_rels_by_table = relationships_service.batch_get_relationships_for_tables(matched_table_names)

            # Process all relationships and filter to only those between matched tables
            for table_name, all_rels in all_rels_by_table.items():
                for rel in all_rels:
                    # Only include relationships where BOTH source and target are in matched tables
                    if rel['source_table'] in matched_table_names and rel['target_table'] in matched_table_names:
                        relationships_list.append(RelationshipResponse(
                            source_table=rel['source_table'],
                            source_column=rel['source_column'],
                            target_table=rel['target_table'],
                            target_column=rel['target_column'],
                            relationship_type=rel['relationship_type'],
                            relationship_subtype=rel.get('relationship_subtype'),
                            confidence=float(rel['confidence']),
                            reasoning=rel['reasoning'],
                            detected_by=rel['detected_by']
                        ))

        # Remove duplicate relationships (since we query from both sides)
        unique_relationships = {}
        for rel in relationships_list:
            key = f"{rel.source_table}:{rel.source_column}:{rel.target_table}:{rel.target_column}"
            if key not in unique_relationships:
                unique_relationships[key] = rel

        relationships_list = list(unique_relationships.values())
        logger.info(f"Found {len(relationships_list)} relationships between matched tables")

        # Step 8: Return response with relationships first, then metadata
        return SemanticSearchResponse(
            query=request.query,
            threshold=request.threshold,
            query_too_vague=False,
            relationships=relationships_list,
            metadata={
                "tables": table_metadata_list,
                "columns": column_metadata_list
            }
        )

    except Exception as e:
        logger.error(f"Error in semantic search: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Semantic search failed: {str(e)}")


# ========== Helper Functions ==========

def search_tables_by_similarity(
    query_embedding_padded: List[float],
    threshold: float
) -> List[tuple[str, float]]:
    """
    Search for similar tables using Neptune vector similarity

    Args:
        query_embedding_padded: Padded 2048-dim query embedding
        threshold: Minimum similarity score (0-1)

    Returns:
        List of (table_name, similarity_score) tuples
    """
    try:
        # Convert embedding to string for inlining (Neptune doesn't support parameterization in CALL)
        embedding_str = str(query_embedding_padded)

        # Use CosineSimilarity with threshold filtering
        query = f"""
        MATCH (t:Table)
        CALL neptune.algo.vectors.distance.byEmbedding(
            t,
            {{
                embedding: {embedding_str},
                metric: "CosineSimilarity"
            }}
        )
        YIELD distance as similarity
        WHERE similarity > $threshold
        RETURN t.name as table_name, similarity
        ORDER BY similarity DESC
        """

        result = neptune_service.execute_query(query, {
            'threshold': threshold
        })

        return [(row['table_name'], row['similarity']) for row in result]

    except Exception as e:
        logger.error(f"Error searching tables by similarity: {e}")
        return []


def search_columns_by_similarity(
    query_embedding_padded: List[float],
    threshold: float
) -> List[tuple[str, float]]:
    """
    Search for similar columns using Neptune vector similarity

    Args:
        query_embedding_padded: Padded 2048-dim query embedding
        threshold: Minimum similarity score (0-1)

    Returns:
        List of (column_full_name, similarity_score) tuples
    """
    try:
        # Convert embedding to string for inlining (Neptune doesn't support parameterization in CALL)
        embedding_str = str(query_embedding_padded)

        # Use CosineSimilarity with threshold filtering
        query = f"""
        MATCH (c:Column)
        CALL neptune.algo.vectors.distance.byEmbedding(
            c,
            {{
                embedding: {embedding_str},
                metric: "CosineSimilarity"
            }}
        )
        YIELD distance as similarity
        WHERE similarity > $threshold
        RETURN c.full_name as column_full_name, similarity
        ORDER BY similarity DESC
        """

        result = neptune_service.execute_query(query, {
            'threshold': threshold
        })

        return [(row['column_full_name'], row['similarity']) for row in result]

    except Exception as e:
        logger.error(f"Error searching columns by similarity: {e}")
        return []
