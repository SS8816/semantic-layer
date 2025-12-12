"""
API endpoints for enriched tables overview
"""

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException

from app.services.dynamodb import dynamodb_service
from app.utils.logger import app_logger as logger

router = APIRouter(prefix="/api/enriched-tables", tags=["enriched-tables"])


@router.get("")
async def get_all_enriched_tables() -> Dict[str, Any]:
    """
    Get all tables that have enriched metadata

    Returns:
        Dictionary with list of enriched tables and their metadata
    """
    try:
        logger.info("Fetching all enriched tables")

        tables = dynamodb_service.get_all_tables()

        # Parse catalog, schema, table from catalog_schema_table
        enriched_tables = []
        for table in tables:
            parts = table.catalog_schema_table.split(".")
            if len(parts) >= 3:
                catalog = parts[0]
                schema = parts[1]
                table_name = ".".join(parts[2:])  # In case table name has dots
            else:
                # Fallback
                catalog = "unknown"
                schema = "unknown"
                table_name = table.name

            enriched_tables.append(
                {
                    "catalog": catalog,
                    "schema": schema,
                    "table_name": table_name,
                    "full_name": table.catalog_schema_table,
                    "schema_status": table.schema_status.value,
                    "last_updated": table.last_updated.isoformat(),
                    "row_count": table.row_count,
                    "column_count": table.column_count,
                    "neptune_import_status": table.neptune_import_status.value,
                    "neptune_last_imported": table.neptune_last_imported.isoformat() if table.neptune_last_imported else None,
                    "relationships_status": table.relationships_status.value if table.relationships_status else None,
                    "relationships_count": table.relationships_count,
                }
            )

        logger.info(f"Found {len(enriched_tables)} enriched tables")

        return {"tables": enriched_tables, "total_count": len(enriched_tables)}

    except Exception as e:
        logger.error(f"Failed to fetch enriched tables: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
