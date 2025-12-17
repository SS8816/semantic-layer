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
    mode: str = Field(default="datamining", description="Search mode: 'analytics' (table-level) or 'datamining' (column-level)")
    include_relationships: bool = Field(default=True, description="Include relationships in response")

    class Config:
        json_schema_extra = {
            "example": {
                "query": "geographic data",
                "threshold": 0.40,
                "mode": "datamining",
                "include_relationships": True
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
    search_mode: Optional[str] = None
    custom_instructions: Optional[str] = None


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
    similarity_score: Optional[float] = None  # None in Analytics mode, float in Data Mining mode


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
    mode: str
    query_too_vague: bool
    relationships: List[RelationshipResponse]
    metadata: Dict[str, Any]  # Contains 'tables' and 'columns' lists

    class Config:
        json_schema_extra = {
            "example": {
                "query": "geographic data",
                "threshold": 0.40,
                "mode": "datamining",
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
        logger.info(f"Semantic search query: '{request.query}' (mode: {request.mode}, threshold: {request.threshold})")

        # Step 1: Generate embedding for the query
        query_embedding = embedding_service.generate_embedding(request.query)
        logger.info(f"Generated query embedding: {len(query_embedding)} dimensions")

        # Step 2: Pad to 2048 dimensions for Neptune
        query_embedding_padded = pad_embedding_to_2048(query_embedding)

        # Step 3 & 4: Search based on mode
        if request.mode == "analytics":
            # Analytics mode: Table-level matching, return ALL columns
            logger.info("Analytics mode: Searching for tables...")

            # Search tables by threshold (filtered by search_mode)
            matched_tables = search_tables_by_similarity(query_embedding_padded, request.threshold, request.mode)
            logger.info(f"Found {len(matched_tables)} matching tables")

            # Also search columns to extract additional table names (filtered by parent table's search_mode)
            matched_columns_raw = search_columns_by_similarity(query_embedding_padded, request.threshold, request.mode)
            logger.info(f"Found {len(matched_columns_raw)} matching columns")

            # Extract table names from matched columns
            matched_table_names = [t for t, _ in matched_tables]
            for column_full_name, _ in matched_columns_raw:
                parts = column_full_name.rsplit('.', 1)
                if len(parts) == 2:
                    table_name = parts[0]
                    if table_name not in matched_table_names:
                        matched_table_names.append(table_name)

            logger.info(f"Total unique tables after deduplication: {len(matched_table_names)}")

            # In analytics mode, we'll fetch ALL columns for these tables later
            # Set matched_columns to empty for now (will be populated with all columns)
            matched_columns = []

        else:
            # Data Mining mode: Column-level matching (current behavior)
            logger.info("Data Mining mode: Searching for tables and columns...")

            # Search with search_mode filtering
            matched_tables = search_tables_by_similarity(query_embedding_padded, request.threshold, request.mode)
            logger.info(f"Found {len(matched_tables)} matching tables")

            matched_columns = search_columns_by_similarity(query_embedding_padded, request.threshold, request.mode)
            logger.info(f"Found {len(matched_columns)} matching columns")

        # Check if query was too vague (no results)
        if request.mode == "analytics":
            if not matched_table_names:
                logger.warning(f"No results found for query: '{request.query}'")
                return SemanticSearchResponse(
                    query=request.query,
                    threshold=request.threshold,
                    mode=request.mode,
                    query_too_vague=True,
                    relationships=[],
                    metadata={"tables": [], "columns": []}
                )
        else:
            if not matched_tables and not matched_columns:
                logger.warning(f"No results found for query: '{request.query}'")
                return SemanticSearchResponse(
                    query=request.query,
                    threshold=request.threshold,
                    mode=request.mode,
                    query_too_vague=True,
                    relationships=[],
                    metadata={"tables": [], "columns": []}
                )

        # Step 5: Fetch full metadata from DynamoDB for matched tables
        table_metadata_list = []

        if request.mode == "analytics":
            # In analytics mode, fetch metadata for ALL matched tables (including those from column search)
            # Create a map of table_name -> similarity for tables found via table search
            table_similarity_map = {t: sim for t, sim in matched_tables}

            for table_name in matched_table_names:
                table_metadata = dynamodb_service.get_table_metadata(table_name)
                if table_metadata:
                    # Use similarity score from table search, or 0.0 if found only via column search
                    similarity = table_similarity_map.get(table_name, 0.0)
                    table_metadata_list.append(TableMetadataResponse(
                        catalog_schema_table=table_metadata.catalog_schema_table,
                        row_count=table_metadata.row_count,
                        column_count=table_metadata.column_count,
                        schema_status=table_metadata.schema_status.value,
                        enrichment_status=table_metadata.enrichment_status.value,
                        relationship_detection_status=table_metadata.relationship_detection_status.value,
                        neptune_import_status=table_metadata.neptune_import_status.value,
                        similarity_score=similarity,
                        search_mode=table_metadata.search_mode,
                        custom_instructions=table_metadata.custom_instructions
                    ))
        else:
            # In datamining mode, fetch metadata only for tables matched by table search
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
                        similarity_score=similarity,
                        search_mode=table_metadata.search_mode,
                        custom_instructions=table_metadata.custom_instructions
                    ))

        # Step 6: Fetch column metadata based on mode
        column_metadata_list = []

        if request.mode == "analytics":
            # Analytics mode: Fetch ALL columns for matched tables
            logger.info(f"Fetching ALL columns for {len(matched_table_names)} matched tables...")

            # Use the table_similarity_map created earlier
            for table_name in matched_table_names:
                # Get table similarity score (0.0 if only found via column search)
                table_similarity = table_similarity_map.get(table_name, 0.0)

                # Get all columns for this table from DynamoDB
                table_with_columns = dynamodb_service.get_table_with_columns(table_name)
                if table_with_columns and table_with_columns.columns:
                    for col_name, col_dict in table_with_columns.columns.items():
                        # Skip stats-only columns if they exist
                        if col_dict.get('column_type') in ['min', 'max', 'avg']:
                            continue

                        column_metadata_list.append(ColumnMetadataResponse(
                            catalog_schema_table=table_name,
                            column_name=col_name,
                            data_type=col_dict.get('data_type', 'unknown'),
                            column_type=col_dict.get('column_type', 'unknown'),
                            semantic_type=col_dict.get('semantic_type'),
                            description=col_dict.get('description', ''),
                            aliases=col_dict.get('aliases', []),
                            cardinality=col_dict.get('cardinality'),
                            null_percentage=col_dict.get('null_percentage'),
                            sample_values=col_dict.get('sample_values', []),
                            min_value=col_dict.get('min_value'),
                            max_value=col_dict.get('max_value'),
                            avg_value=col_dict.get('avg_value')
                            # similarity_score omitted in Analytics mode - defaults to None
                        ))

            logger.info(f"Fetched {len(column_metadata_list)} total columns for analytics mode")

        else:
            # Data Mining mode: Fetch only matched columns (current behavior)
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

        # Step 7: Prepare matched_table_names for relationships
        # (Already set in analytics mode, need to set in datamining mode)
        if request.mode == "datamining":
            matched_table_names = [t for t, _ in matched_tables]

            # Extract table names from matched columns
            for column_full_name, _ in matched_columns:
                parts = column_full_name.rsplit('.', 1)
                if len(parts) == 2:
                    table_name = parts[0]
                    if table_name not in matched_table_names:
                        matched_table_names.append(table_name)

        # Step 7.5: Top 1 Table Logic (when relationships disabled)
        # Apply two-tier sorting: direct table matches first, then by similarity
        if not request.include_relationships and len(matched_table_names) > 1:
            logger.info("Relationships disabled - applying Top 1 table logic...")

            # Create scoring list: (table_name, is_direct_match, similarity_score)
            table_scores = []

            # Build a map of direct table matches
            direct_table_matches = {t: sim for t, sim in matched_tables}

            # Build a map of max column similarity for each table
            column_table_similarities = {}
            if request.mode == "analytics":
                for column_full_name, sim in matched_columns_raw:
                    parts = column_full_name.rsplit('.', 1)
                    if len(parts) == 2:
                        table_name = parts[0]
                        if table_name not in column_table_similarities or sim > column_table_similarities[table_name]:
                            column_table_similarities[table_name] = sim
            else:
                for column_full_name, sim in matched_columns:
                    parts = column_full_name.rsplit('.', 1)
                    if len(parts) == 2:
                        table_name = parts[0]
                        if table_name not in column_table_similarities or sim > column_table_similarities[table_name]:
                            column_table_similarities[table_name] = sim

            # Score all matched tables
            for table_name in matched_table_names:
                if table_name in direct_table_matches:
                    # Priority 1: Direct table match
                    table_scores.append((table_name, True, direct_table_matches[table_name]))
                else:
                    # Priority 2: Column match only (use max column similarity)
                    max_col_sim = column_table_similarities.get(table_name, 0.0)
                    table_scores.append((table_name, False, max_col_sim))

            # Sort: direct matches first (True > False), then by similarity DESC
            table_scores.sort(key=lambda x: (x[1], x[2]), reverse=True)

            # Take top 1
            top_table = table_scores[0][0]
            logger.info(f"Top 1 table selected: {top_table} (is_direct={table_scores[0][1]}, sim={table_scores[0][2]:.3f})")

            # Update matched_table_names to only contain top 1
            matched_table_names = [top_table]

            # Filter metadata to only include top 1 table
            table_metadata_list = [t for t in table_metadata_list if t.catalog_schema_table == top_table]
            column_metadata_list = [c for c in column_metadata_list if c.catalog_schema_table == top_table]
            logger.info(f"Filtered to {len(column_metadata_list)} columns from top table")

        # Step 8: Fetch relationships (if requested)
        relationships_list = []

        if request.include_relationships and len(matched_table_names) >= 2:
            logger.info(f"Fetching relationships for {len(matched_table_names)} matched tables...")

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
        elif not request.include_relationships:
            logger.info("Relationships disabled by user request")

        # Step 9: Return response with relationships first, then metadata
        return SemanticSearchResponse(
            query=request.query,
            threshold=request.threshold,
            mode=request.mode,
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
    threshold: float,
    mode: str = "datamining"
) -> List[tuple[str, float]]:
    """
    Search for similar tables using Neptune vector similarity

    Args:
        query_embedding_padded: Padded 2048-dim query embedding
        threshold: Minimum similarity score (0-1)
        mode: Search mode ('analytics' or 'datamining')

    Returns:
        List of (table_name, similarity_score) tuples
    """
    try:
        # Convert embedding to string for inlining (Neptune doesn't support parameterization in CALL)
        embedding_str = str(query_embedding_padded)

        # Use CosineSimilarity with threshold and search_mode filtering
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
        WHERE similarity > $threshold AND (t.search_mode IS NULL OR t.search_mode = $mode)
        RETURN t.name as table_name, similarity
        ORDER BY similarity DESC
        """

        result = neptune_service.execute_query(query, {
            'threshold': threshold,
            'mode': mode
        })

        return [(row['table_name'], row['similarity']) for row in result]

    except Exception as e:
        logger.error(f"Error searching tables by similarity: {e}")
        return []


def search_columns_by_similarity(
    query_embedding_padded: List[float],
    threshold: float,
    mode: str = "datamining"
) -> List[tuple[str, float]]:
    """
    Search for similar columns using Neptune vector similarity
    Filters columns by parent table's search_mode to prevent "sneaking in" via columns

    Args:
        query_embedding_padded: Padded 2048-dim query embedding
        threshold: Minimum similarity score (0-1)
        mode: Search mode ('analytics' or 'datamining')

    Returns:
        List of (column_full_name, similarity_score) tuples
    """
    try:
        # Convert embedding to string for inlining (Neptune doesn't support parameterization in CALL)
        embedding_str = str(query_embedding_padded)

        # Use CosineSimilarity with threshold and parent table's search_mode filtering
        query = f"""
        MATCH (t:Table)-[:HAS_COLUMN]->(c:Column)
        CALL neptune.algo.vectors.distance.byEmbedding(
            c,
            {{
                embedding: {embedding_str},
                metric: "CosineSimilarity"
            }}
        )
        YIELD distance as similarity
        WHERE similarity > $threshold AND (t.search_mode IS NULL OR t.search_mode = $mode)
        RETURN c.full_name as column_full_name, similarity
        ORDER BY similarity DESC
        """

        result = neptune_service.execute_query(query, {
            'threshold': threshold,
            'mode': mode
        })

        return [(row['column_full_name'], row['similarity']) for row in result]

    except Exception as e:
        logger.error(f"Error searching columns by similarity: {e}")
        return []
