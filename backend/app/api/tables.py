"""
API endpoints for table operations
"""

from typing import List

import pandas as pd  # Add if not already there
from fastapi import APIRouter, HTTPException, Path, Query, Request

from app.models import (
    CatalogsResponse,
    ErrorResponse,
    TableDataResponse,
    TablesInCatalogResponse,
    TablesResponse,
    TableSummary,
)
from app.services import dynamodb_service, starburst_service
from app.utils.logger import app_logger as logger

router = APIRouter(prefix="/api", tags=["tables"])


@router.get(
    "/catalogs",
    response_model=CatalogsResponse,
    responses={500: {"model": ErrorResponse}},
)
async def get_catalogs(request: Request):
    """
    Get list of all available catalogs

    Returns:
        CatalogsResponse containing list of catalogs
    """
    try:
        logger.info("Fetching all catalogs")
        catalogs = starburst_service.get_catalogs(
            username=request.state.username, password=request.state.password
        )

        logger.info(f"Returning {len(catalogs)} catalogs")
        return CatalogsResponse(catalogs=catalogs, total_count=len(catalogs))

    except Exception as e:
        logger.error(f"Error fetching catalogs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/catalogs/{catalog}/schemas", responses={500: {"model": ErrorResponse}})
async def get_schemas_in_catalog(catalog: str, request: Request):
    """
    Get list of schemas in a specific catalog

    Args:
        catalog: Catalog name

    Returns:
        List of schema names
    """
    try:
        logger.info(f"Fetching schemas from catalog: {catalog}")

        # Query Starburst for schemas
        schemas = starburst_service.get_schemas_in_catalog(
            catalog, username=request.state.username, password=request.state.password
        )

        logger.info(f"Returning {len(schemas)} schemas")

        return {"catalog": catalog, "schemas": schemas, "total_count": len(schemas)}

    except Exception as e:
        logger.error(f"Error fetching schemas from {catalog}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/catalogs/{catalog}/schemas/{schema}/tables",
    response_model=TablesInCatalogResponse,
    responses={500: {"model": ErrorResponse}},
)
async def get_tables_in_schema(
    request: Request,
    catalog: str = Path(..., description="Catalog name"),
    schema: str = Path(..., description="Schema name"),
):
    """
    Get list of ALL tables in a specific catalog.schema (from Starburst, not DynamoDB)

    Args:
        catalog: Catalog name
        schema: Schema name

    Returns:
        TablesInCatalogResponse containing list of table names
    """
    try:
        logger.info(f"Fetching tables from {catalog}.{schema}")

        # Get ALL tables from Starburst (not filtered by DynamoDB)
        tables_data = starburst_service.get_tables_in_catalog(
            catalog,
            schema,
            username=request.state.username,
            password=request.state.password,
        )
        table_names = [t["name"] for t in tables_data]

        logger.info(f"Returning {len(table_names)} tables from Starburst")

        return TablesInCatalogResponse(
            catalog=catalog,
            schema=schema,
            tables=table_names,
            total_count=len(table_names),
        )

    except Exception as e:
        logger.error(f"Error fetching tables from {catalog}.{schema}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/tables", response_model=TablesResponse, responses={500: {"model": ErrorResponse}}
)
async def get_tables():
    """
    Get list of all tables WITH metadata (from DynamoDB only)

    Returns:
        TablesResponse containing list of tables with summary information
    """
    try:
        logger.info("Fetching all tables with metadata from DynamoDB")

        # Get all tables from DynamoDB (only tables with generated metadata)
        table_summaries = dynamodb_service.get_all_tables()

        # Sort by table name
        table_summaries.sort(key=lambda x: x.name)

        logger.info(f"Returning {len(table_summaries)} tables with metadata")

        return TablesResponse(tables=table_summaries, total_count=len(table_summaries))

    except Exception as e:
        logger.error(f"Error fetching tables: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/table-data/{catalog}/{schema}/{table_name}",
    response_model=TableDataResponse,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def get_table_data(
    request: Request,
    catalog: str = Path(..., description="Catalog name"),
    schema: str = Path(..., description="Schema name"),
    table_name: str = Path(..., description="Table name"),
    limit: int = Query(
        default=1000, ge=1, le=10000, description="Number of rows to return"
    ),
):
    """
    Get random sample of data from a table

    Args:
        catalog: Catalog name
        schema: Schema name
        table_name: Name of the table
        limit: Number of rows to return (default 1000, max 10000)

    Returns:
        TableDataResponse containing sample data
    """
    try:
        logger.info(
            f"Fetching data for {catalog}.{schema}.{table_name}, limit: {limit}"
        )

        # Get sample data
        df = starburst_service.get_sample_data_with_catalog(
            catalog,
            schema,
            table_name,
            limit=limit,
            username=request.state.username,
            password=request.state.password,
        )
        if df is None or df.empty:
            logger.warning(
                f"No sample data available for {catalog}.{schema}.{table_name}"
            )
            return TableDataResponse(
                table_name=f"{catalog}.{schema}.{table_name}",
                columns=[],
                data=[],
                row_count=0,
            )
        # Convert DataFrame to list format
        columns = df.columns.tolist()
        data = []
        for _, row in df.iterrows():
            row_data = []
            for val in row:
                # Convert complex types to strings
                if isinstance(val, (list, dict)):
                    row_data.append(str(val))
                elif pd.isna(val):
                    row_data.append(None)
                else:
                    row_data.append(val)
            data.append(row_data)

        logger.info(f"Returning {len(data)} rows with {len(columns)} columns")

        return TableDataResponse(
            table_name=f"{catalog}.{schema}.{table_name}",
            columns=columns,
            data=data,
            row_count=len(data),
        )

    except Exception as e:
        logger.error(
            f"Error fetching table data for {catalog}.{schema}.{table_name}: {e}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=str(e))
