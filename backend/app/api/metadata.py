"""
API endpoints for metadata operations
"""
from fastapi import APIRouter, HTTPException, Path, Body, Query
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException, Path, Body, Query, BackgroundTasks
from app.models import (
    TableWithColumns, RefreshMetadataResponse,
    UpdateAliasRequest, UpdateAliasResponse,
    UpdateColumnMetadataRequest, UpdateColumnMetadataResponse,
    UpdateTableConfigRequest, UpdateTableConfigResponse,
    ErrorResponse
)
from app.services import dynamodb_service, metadata_generator
from app.utils.logger import app_logger as logger
from fastapi.responses import JSONResponse
from app.utils.logger import app_logger as logger
from app.services import dynamodb_service, metadata_generator
router = APIRouter(prefix="/api", tags=["metadata"])


@router.get(
    "/metadata/{catalog}/{schema}/{table_name}",
    response_model=TableWithColumns,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def get_metadata(
    catalog: str = Path(..., description="Catalog name"),
    schema: str = Path(..., description="Schema name"),
    table_name: str = Path(..., description="Table name"),
    background_tasks: BackgroundTasks = None #GPT
):
    """
    Get complete metadata for a table including all column metadata
    
    Args:
        catalog: Catalog name
        schema: Schema name
        table_name: Table name
        
    Returns:
        TableWithColumns containing complete metadata
    """
    try:
        catalog_schema_table = f"{catalog}.{schema}.{table_name}"
        logger.info(f"Fetching metadata for: {catalog_schema_table}")
        
        # Get complete table with columns
        table_with_columns = dynamodb_service.get_table_with_columns(catalog_schema_table)
        
        if not table_with_columns:
            raise HTTPException(
                status_code=404, 
                detail=f"Metadata not found for '{catalog_schema_table}'. Please generate metadata first."
            )
        
        logger.info(f"Returning metadata for {catalog_schema_table} with {len(table_with_columns.columns)} columns")
        
        return table_with_columns
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching metadata for {catalog}.{schema}.{table_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/relationship-status/{catalog}/{schema}/{table_name}",
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def get_relationship_status(
    catalog: str = Path(..., description="Catalog name"),
    schema: str = Path(..., description="Schema name"),
    table_name: str = Path(..., description="Table name")
):
    """
    Get only the relationship detection status for a table (lightweight query)

    This endpoint is optimized for polling - it only queries the status field
    without fetching all column metadata.

    Args:
        catalog: Catalog name
        schema: Schema name
        table_name: Table name

    Returns:
        Dictionary with relationship_detection_status
    """
    try:
        catalog_schema_table = f"{catalog}.{schema}.{table_name}"
        logger.info(f"Fetching relationship status for: {catalog_schema_table}")

        # Get only the status (lightweight query)
        status = dynamodb_service.get_relationship_detection_status(catalog_schema_table)

        if status is None:
            raise HTTPException(
                status_code=404,
                detail=f"Table '{catalog_schema_table}' not found"
            )

        return {"relationship_detection_status": status.value}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching relationship status for {catalog}.{schema}.{table_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/refresh-metadata/{catalog}/{schema}/{table_name}",
    response_model=RefreshMetadataResponse,
    responses={500: {"model": ErrorResponse}}
)
async def refresh_metadata(
    catalog: str = Path(..., description="Catalog name"),
    schema: str = Path(..., description="Schema name"),
    table_name: str = Path(..., description="Table name")
):
    """
    Refresh metadata for a table (regenerate all metadata)
    
    Args:
        catalog: Catalog name
        schema: Schema name
        table_name: Table name
        
    Returns:
        RefreshMetadataResponse with status
    """
    try:
        catalog_schema_table = f"{catalog}.{schema}.{table_name}"
        logger.info(f"Refreshing metadata for: {catalog_schema_table}")
        
        # Refresh metadata
        success = metadata_generator.refresh_metadata_for_table(
            catalog_schema_table=catalog_schema_table,
            catalog=catalog,
            schema=schema
        )
        
        if success:
            return RefreshMetadataResponse(
                status="success",
                table_name=catalog_schema_table,
                message=f"Metadata successfully refreshed for '{catalog_schema_table}'"
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to refresh metadata for '{catalog_schema_table}'"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing metadata for {catalog}.{schema}.{table_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch(
    "/column/{catalog}/{schema}/{table_name}/{column_name}/alias",
    response_model=UpdateAliasResponse,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def update_column_alias(
    catalog: str = Path(..., description="Catalog name"),
    schema: str = Path(..., description="Schema name"),
    table_name: str = Path(..., description="Table name"),
    column_name: str = Path(..., description="Column name"),
    request: UpdateAliasRequest = Body(...)
):
    """
    Update aliases for a specific column
    
    Args:
        catalog: Catalog name
        schema: Schema name
        table_name: Table name
        column_name: Column name
        request: UpdateAliasRequest containing new aliases
        
    Returns:
        UpdateAliasResponse with updated aliases
    """
    try:
        catalog_schema_table = f"{catalog}.{schema}.{table_name}"
        logger.info(f"Updating aliases for {catalog_schema_table}.{column_name}")
        
        # Check if column metadata exists
        column_metadata = dynamodb_service.get_column_metadata(catalog_schema_table, column_name)
        if not column_metadata:
            raise HTTPException(
                status_code=404,
                detail=f"Column metadata not found for '{catalog_schema_table}.{column_name}'"
            )
        
        # Update aliases
        success = dynamodb_service.update_column_aliases(
            catalog_schema_table=catalog_schema_table,
            column_name=column_name,
            aliases=request.aliases
        )
        
        if success:
            logger.info(f"Successfully updated aliases for {catalog_schema_table}.{column_name}")
            return UpdateAliasResponse(
                status="success",
                table_name=catalog_schema_table,
                column_name=column_name,
                aliases=request.aliases
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update aliases for '{catalog_schema_table}.{column_name}'"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating aliases for {catalog}.{schema}.{table_name}.{column_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch(
    "/column/{catalog}/{schema}/{table_name}/{column_name}/metadata",
    response_model=UpdateColumnMetadataResponse,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def update_column_metadata(
    catalog: str = Path(..., description="Catalog name"),
    schema: str = Path(..., description="Schema name"),
    table_name: str = Path(..., description="Table name"),
    column_name: str = Path(..., description="Column name"),
    request: UpdateColumnMetadataRequest = Body(...)
):
    """
    Update multiple metadata fields for a column
    
    Can update: aliases, description, column_type, semantic_type
    
    Args:
        catalog: Catalog name
        schema: Schema name
        table_name: Table name
        column_name: Column name
        request: UpdateColumnMetadataRequest containing fields to update
        
    Returns:
        UpdateColumnMetadataResponse with updated fields
    """
    try:
        catalog_schema_table = f"{catalog}.{schema}.{table_name}"
        logger.info(f"Updating metadata for {catalog_schema_table}.{column_name}")
        
        # Check if column metadata exists
        column_metadata = dynamodb_service.get_column_metadata(catalog_schema_table, column_name)
        if not column_metadata:
            raise HTTPException(
                status_code=404,
                detail=f"Column metadata not found for '{catalog_schema_table}.{column_name}'"
            )
        
        # Update metadata fields
        success = dynamodb_service.update_column_metadata_fields(
            catalog_schema_table=catalog_schema_table,
            column_name=column_name,
            aliases=request.aliases,
            description=request.description,
            column_type=request.column_type,
            semantic_type=request.semantic_type
        )
        
        if success:
            # Build list of updated fields
            updated_fields = []
            if request.aliases is not None:
                updated_fields.append("aliases")
            if request.description is not None:
                updated_fields.append("description")
            if request.column_type is not None:
                updated_fields.append("column_type")
            if request.semantic_type is not None:
                updated_fields.append("semantic_type")
            
            logger.info(f"Successfully updated {', '.join(updated_fields)} for {catalog_schema_table}.{column_name}")
            
            return UpdateColumnMetadataResponse(
                status="success",
                catalog_table=catalog_schema_table,
                column_name=column_name,
                updated_fields=updated_fields
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update metadata for '{catalog_schema_table}.{column_name}'"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating metadata for {catalog}.{schema}.{table_name}.{column_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch(
    "/table/{catalog}/{schema}/{table_name}/config",
    response_model=UpdateTableConfigResponse,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}}
)
async def update_table_config(
    catalog: str = Path(..., description="Catalog name"),
    schema: str = Path(..., description="Schema name"),
    table_name: str = Path(..., description="Table name"),
    request: UpdateTableConfigRequest = Body(...)
):
    """
    Update table configuration (search_mode and custom_instructions)

    Args:
        catalog: Catalog name
        schema: Schema name
        table_name: Table name
        request: UpdateTableConfigRequest containing fields to update

    Returns:
        UpdateTableConfigResponse with updated fields
    """
    try:
        catalog_schema_table = f"{catalog}.{schema}.{table_name}"
        logger.info(f"Updating table config for {catalog_schema_table}")

        # Check if table metadata exists
        table_metadata = dynamodb_service.get_table_metadata(catalog_schema_table)
        if not table_metadata:
            raise HTTPException(
                status_code=404,
                detail=f"Table metadata not found for '{catalog_schema_table}'"
            )

        # Update config fields
        success = dynamodb_service.update_table_config_fields(
            catalog_schema_table=catalog_schema_table,
            search_mode=request.search_mode,
            custom_instructions=request.custom_instructions
        )

        if success:
            # Build list of updated fields
            updated_fields = []
            if request.search_mode is not None:
                updated_fields.append("search_mode")
            if request.custom_instructions is not None:
                updated_fields.append("custom_instructions")

            logger.info(f"Successfully updated {', '.join(updated_fields)} for {catalog_schema_table}")

            return UpdateTableConfigResponse(
                status="success",
                catalog_schema_table=catalog_schema_table,
                updated_fields=updated_fields
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update config for '{catalog_schema_table}'"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating table config for {catalog}.{schema}.{table_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))