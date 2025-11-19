"""
API endpoints for table relationships
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

from app.services.dynamodb_relationships import relationships_service
from app.utils.logger import app_logger as logger

router = APIRouter(prefix="/api/relationships", tags=["relationships"])


@router.get("/{catalog}/{schema}/{table_name}")
async def get_table_relationships(
    catalog: str, schema: str, table_name: str
) -> Dict[str, Any]:
    """
    Get all relationships for a table

    Args:
        catalog: Catalog name
        schema: Schema name
        table_name: Table name

    Returns:
        Dictionary with relationships grouped by type
    """
    try:
        full_table_name = f"{catalog}.{schema}.{table_name}"
        logger.info(f"Fetching relationships for {full_table_name}")

        # Get all relationships
        all_relationships = relationships_service.get_all_relationships_for_table(
            full_table_name
        )

        if not all_relationships:
            return {
                "table_name": full_table_name,
                "total_count": 0,
                "relationships_by_type": {},
                "all_relationships": [],
            }

        # Group by main type
        by_type = {"foreign_key": [], "semantic": [], "name_based": []}

        for rel in all_relationships:
            rel_type = rel.get("relationship_type", "unknown")
            if rel_type in by_type:
                by_type[rel_type].append(rel)
            else:
                # Handle unknown types
                if "other" not in by_type:
                    by_type["other"] = []
                by_type["other"].append(rel)

        # Remove empty categories
        by_type = {k: v for k, v in by_type.items() if v}

        # Sort each category by confidence (highest first)
        for rel_type in by_type:
            by_type[rel_type] = sorted(
                by_type[rel_type], key=lambda x: x.get("confidence", 0), reverse=True
            )

        logger.info(
            f"Found {len(all_relationships)} relationships for {full_table_name}"
        )

        return {
            "table_name": full_table_name,
            "total_count": len(all_relationships),
            "relationships_by_type": by_type,
            "all_relationships": all_relationships,
        }

    except Exception as e:
        logger.error(
            f"Failed to fetch relationships for {catalog}.{schema}.{table_name}: {e}"
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{catalog}/{schema}/{table_name}/type/{relationship_type}")
async def get_relationships_by_type(
    catalog: str,
    schema: str,
    table_name: str,
    relationship_type: str,
    subtype: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Get relationships filtered by type and optional subtype

    Args:
        catalog: Catalog name
        schema: Schema name
        table_name: Table name
        relationship_type: Main type (foreign_key, semantic, name_based)
        subtype: Optional subtype filter

    Returns:
        List of filtered relationships
    """
    try:
        full_table_name = f"{catalog}.{schema}.{table_name}"

        relationships = relationships_service.get_relationships_by_type(
            table_name=full_table_name,
            relationship_type=relationship_type,
            relationship_subtype=subtype,
        )

        # Sort by confidence
        relationships = sorted(
            relationships, key=lambda x: x.get("confidence", 0), reverse=True
        )

        return relationships

    except Exception as e:
        logger.error(f"Failed to fetch filtered relationships: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{catalog}/{schema}/{table_name}/count")
async def get_relationship_count(
    catalog: str, schema: str, table_name: str
) -> Dict[str, int]:
    """
    Get count of relationships by type

    Args:
        catalog: Catalog name
        schema: Schema name
        table_name: Table name

    Returns:
        Dictionary with counts by type
    """
    try:
        full_table_name = f"{catalog}.{schema}.{table_name}"

        all_relationships = relationships_service.get_all_relationships_for_table(
            full_table_name
        )

        counts = {
            "total": len(all_relationships),
            "foreign_key": 0,
            "semantic": 0,
            "name_based": 0,
        }

        for rel in all_relationships:
            rel_type = rel.get("relationship_type", "unknown")
            if rel_type in counts:
                counts[rel_type] += 1

        return counts

    except Exception as e:
        logger.error(f"Failed to get relationship count: {e}")
        raise HTTPException(status_code=500, detail=str(e))
