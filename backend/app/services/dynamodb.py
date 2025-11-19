"""
DynamoDB service for storing and retrieving metadata
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

import boto3
import numpy as np
import pandas as pd
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from app.config import settings
from app.models import (
    ColumnMetadata,
    SchemaChange,
    SchemaStatus,
    TableMetadata,
    TableSummary,
    TableWithColumns,
)
from app.utils.logger import app_logger as logger


def _convert_floats_to_decimal(obj):
    """
    Convert Python types to DynamoDB-compatible types
    - float -> Decimal
    - Timestamp/datetime/date -> ISO string
    - NaN/None -> None
    - numpy types -> Python types
    """
    # Handle None and NaN
    if obj is None:
        return None
    if isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
        return None

    # Handle numeric types
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, (np.integer, np.floating)):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return Decimal(str(float(obj))) if isinstance(obj, np.floating) else int(obj)

    # Handle datetime types
    if isinstance(obj, (pd.Timestamp, datetime, date)):
        return obj.isoformat()

    # Handle collections recursively
    if isinstance(obj, dict):
        return {k: _convert_floats_to_decimal(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_convert_floats_to_decimal(i) for i in obj]
    if isinstance(obj, tuple):
        return tuple(_convert_floats_to_decimal(i) for i in obj)

    # Handle numpy/pandas specific types
    if isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    if isinstance(obj, (np.str_, str)):
        return str(obj)

    # Return as-is for other types (str, int, bool, etc.)
    return obj


def _convert_decimals_to_python(obj):
    """Convert Decimal objects back to Python int/float"""
    if isinstance(obj, list):
        return [_convert_decimals_to_python(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: _convert_decimals_to_python(value) for key, value in obj.items()}
    elif isinstance(obj, Decimal):
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    else:
        return obj


class DynamoDBService:
    """Service for interacting with DynamoDB"""

    def __init__(self):
        """Initialize DynamoDB client and resources"""
        # Build session kwargs
        session_kwargs = {"region_name": settings.aws_region}

        # Add credentials if provided
        if settings.aws_access_key_id and settings.aws_secret_access_key:
            session_kwargs.update(
                {
                    "aws_access_key_id": settings.aws_access_key_id,
                    "aws_secret_access_key": settings.aws_secret_access_key,
                }
            )
            if settings.aws_session_token:
                session_kwargs["aws_session_token"] = settings.aws_session_token

        # Create session and resource
        self.session = boto3.Session(**session_kwargs)
        self.dynamodb = self.session.resource("dynamodb")

        self.table_metadata_table = self.dynamodb.Table(
            settings.dynamodb_table_metadata_table
        )
        self.column_metadata_table = self.dynamodb.Table(
            settings.dynamodb_column_metadata_table
        )

        logger.info("DynamoDB service initialized")

    # ========== Table Metadata Operations ==========

    def save_table_metadata(self, table_metadata: TableMetadata) -> bool:
        """Save table metadata to DynamoDB"""
        try:
            item = {
                "catalog_schema_table": table_metadata.catalog_schema_table,  # CHANGED
                "last_updated": table_metadata.last_updated.isoformat(),
                "row_count": table_metadata.row_count,
                "column_count": table_metadata.column_count,
                "schema_status": table_metadata.schema_status.value,
            }

            if table_metadata.schema_change_detected_at:
                item["schema_change_detected_at"] = (
                    table_metadata.schema_change_detected_at.isoformat()
                )

            if table_metadata.schema_changes:
                item["schema_changes"] = {
                    "new_columns": table_metadata.schema_changes.new_columns,
                    "removed_columns": table_metadata.schema_changes.removed_columns,
                    "type_changes": table_metadata.schema_changes.type_changes,
                }

            item = _convert_floats_to_decimal(item)
            self.table_metadata_table.put_item(Item=item)
            logger.info(
                f"Saved table metadata for {table_metadata.catalog_schema_table}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to save table metadata for {table_metadata.catalog_schema_table}: {e}"
            )
            return False

    def get_table_metadata(self, catalog_schema_table: str) -> Optional[TableMetadata]:
        """Get table metadata from DynamoDB"""
        try:
            response = self.table_metadata_table.get_item(
                Key={"catalog_schema_table": catalog_schema_table}  # CHANGED
            )

            if "Item" not in response:
                logger.warning(f"No metadata found for table {catalog_schema_table}")
                return None

            item = _convert_decimals_to_python(response["Item"])

            # Parse schema changes if present
            schema_changes = None
            if "schema_changes" in item:
                schema_changes = SchemaChange(**item["schema_changes"])

            # Parse datetime fields
            last_updated = datetime.fromisoformat(item["last_updated"])
            schema_change_detected_at = None
            if "schema_change_detected_at" in item:
                schema_change_detected_at = datetime.fromisoformat(
                    item["schema_change_detected_at"]
                )

            table_metadata = TableMetadata(
                catalog_schema_table=item["catalog_schema_table"],  # CHANGED
                last_updated=last_updated,
                row_count=item.get("row_count", 0),
                column_count=item.get("column_count", 0),
                schema_status=SchemaStatus(item.get("schema_status", "CURRENT")),
                schema_change_detected_at=schema_change_detected_at,
                schema_changes=schema_changes,
            )

            logger.info(f"Retrieved table metadata for {catalog_schema_table}")
            return table_metadata

        except Exception as e:
            logger.error(
                f"Failed to get table metadata for {catalog_schema_table}: {e}"
            )
            return None

    def get_all_table_identifiers(self) -> List[str]:
        """
        Get list of all table identifiers that have metadata stored

        Returns:
            List of table identifiers in catalog.schema.table format
        """
        try:
            # Scan the table_metadata table to get all tables
            response = self.table_metadata_table.scan(
                ProjectionExpression="catalog_schema_table"
            )

            table_identifiers = [
                item["catalog_schema_table"] for item in response.get("Items", [])
            ]

            # Handle pagination if there are many tables
            while "LastEvaluatedKey" in response:
                response = self.table_metadata_table.scan(
                    ProjectionExpression="catalog_schema_table",
                    ExclusiveStartKey=response["LastEvaluatedKey"],
                )
                table_identifiers.extend(
                    [item["catalog_schema_table"] for item in response.get("Items", [])]
                )

            logger.info(f"Found {len(table_identifiers)} tables with metadata")
            return table_identifiers

        except Exception as e:
            logger.error(f"Failed to get all table identifiers: {e}")
            return []

    def get_all_tables(self) -> List[TableSummary]:
        """Get all tables from DynamoDB"""
        try:
            response = self.table_metadata_table.scan()
            items = _convert_decimals_to_python(response.get("Items", []))

            # Handle pagination
            while "LastEvaluatedKey" in response:
                response = self.table_metadata_table.scan(
                    ExclusiveStartKey=response["LastEvaluatedKey"]
                )
                items.extend(_convert_decimals_to_python(response.get("Items", [])))

            tables = []
            for item in items:
                catalog_schema_table = item["catalog_schema_table"]
                # Extract just table name for display (last part after final dot)
                table_name = catalog_schema_table.split(".")[-1]

                tables.append(
                    TableSummary(
                        name=table_name,
                        catalog_schema_table=catalog_schema_table,
                        schema_status=SchemaStatus(
                            item.get("schema_status", "CURRENT")
                        ),
                        last_updated=datetime.fromisoformat(item["last_updated"]),
                        row_count=item.get("row_count", 0),
                        column_count=item.get("column_count", 0),
                    )
                )

            logger.info(f"Retrieved {len(tables)} tables from DynamoDB")
            return tables

        except Exception as e:
            logger.error(f"Failed to get all tables: {e}")
            return []

    def update_table_schema_status(
        self,
        catalog_schema_table: str,  # CHANGED
        status: SchemaStatus,
        schema_changes: Optional[SchemaChange] = None,
    ) -> bool:
        """Update schema status for a table"""
        try:
            update_expr = "SET schema_status = :status"
            expr_values = {":status": status.value}

            if status == SchemaStatus.SCHEMA_CHANGED and schema_changes:
                update_expr += ", schema_change_detected_at = :detected_at, schema_changes = :changes"
                expr_values[":detected_at"] = datetime.now().isoformat()
                expr_values[":changes"] = {
                    "new_columns": schema_changes.new_columns,
                    "removed_columns": schema_changes.removed_columns,
                    "type_changes": schema_changes.type_changes,
                }
            elif status == SchemaStatus.CURRENT:
                update_expr += " REMOVE schema_change_detected_at, schema_changes"

            expr_values = _convert_floats_to_decimal(expr_values)

            self.table_metadata_table.update_item(
                Key={"catalog_schema_table": catalog_schema_table},  # CHANGED
                UpdateExpression=update_expr,
                ExpressionAttributeValues=expr_values,
            )

            logger.info(
                f"Updated schema status for {catalog_schema_table} to {status.value}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to update schema status for {catalog_schema_table}: {e}"
            )
            return False

    # ========== Column Metadata Operations ==========

    def save_column_metadata(self, column_metadata: ColumnMetadata) -> bool:
        """Save column metadata to DynamoDB"""
        try:
            item = {
                "catalog_schema_table": column_metadata.catalog_schema_table,  # CHANGED
                "column_name": column_metadata.column_name,
                "data_type": column_metadata.data_type,
                "column_type": column_metadata.column_type,
                "semantic_type": column_metadata.semantic_type
                if column_metadata.semantic_type
                else "",
                "aliases": column_metadata.aliases,
                "description": column_metadata.description,
                "cardinality": column_metadata.cardinality,
                "null_count": column_metadata.null_count,
                "null_percentage": column_metadata.null_percentage,
                "sample_values": column_metadata.sample_values,
            }

            # Only add numeric fields if they're not None
            if column_metadata.min_value is not None:
                item["min_value"] = column_metadata.min_value
            if column_metadata.max_value is not None:
                item["max_value"] = column_metadata.max_value
            if column_metadata.avg_value is not None:
                item["avg_value"] = column_metadata.avg_value

            logger.info(
                f"Before conversion - {column_metadata.column_name}: sample_values type = {type(column_metadata.sample_values)}"
            )
            item = _convert_floats_to_decimal(item)
            logger.info(
                f"After conversion - {column_metadata.column_name}: item keys = {list(item.keys())}"
            )

            self.column_metadata_table.put_item(Item=item)
            logger.info(
                f"✅ DynamoDB put_item succeeded for {column_metadata.column_name}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to save column metadata for {column_metadata.catalog_schema_table}.{column_metadata.column_name}: {e}"
            )
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return False

    def get_column_metadata(
        self, catalog_schema_table: str, column_name: str
    ) -> Optional[ColumnMetadata]:
        """Get column metadata from DynamoDB"""
        try:
            response = self.column_metadata_table.get_item(
                Key={
                    "catalog_schema_table": catalog_schema_table,  # CHANGED
                    "column_name": column_name,
                }
            )

            if "Item" not in response:
                logger.warning(
                    f"No metadata found for column {catalog_schema_table}.{column_name}"
                )
                return None

            item = _convert_decimals_to_python(response["Item"])

            column_metadata = ColumnMetadata(
                catalog_schema_table=item["catalog_schema_table"],
                column_name=item["column_name"],
                data_type=item["data_type"],
                column_type=item.get("column_type", "dimension"),
                semantic_type=item.get("semantic_type")
                if item.get("semantic_type")
                else None,
                aliases=item.get("aliases", []),
                description=item.get("description", ""),
                min_value=item.get("min_value"),
                max_value=item.get("max_value"),
                avg_value=item.get("avg_value"),
                cardinality=item.get("cardinality", 0),
                null_count=item.get("null_count", 0),
                null_percentage=item.get("null_percentage", 0.0),
                sample_values=item.get("sample_values", []),
            )

            logger.debug(
                f"Retrieved column metadata for {catalog_schema_table}.{column_name}"
            )
            return column_metadata

        except Exception as e:
            logger.error(
                f"Failed to get column metadata for {catalog_schema_table}.{column_name}: {e}"
            )
            return None

    def get_all_columns_for_table(
        self, catalog_schema_table: str
    ) -> List[ColumnMetadata]:
        """Get metadata for all columns in a table"""
        try:
            response = self.column_metadata_table.query(
                KeyConditionExpression=Key("catalog_schema_table").eq(
                    catalog_schema_table
                )  # CHANGED
            )

            items = _convert_decimals_to_python(response.get("Items", []))

            # Handle pagination
            while "LastEvaluatedKey" in response:
                response = self.column_metadata_table.query(
                    KeyConditionExpression=Key("catalog_schema_table").eq(
                        catalog_schema_table
                    ),
                    ExclusiveStartKey=response["LastEvaluatedKey"],
                )
                items.extend(_convert_decimals_to_python(response.get("Items", [])))

            column_metadata_list = []
            for item in items:
                column_metadata_list.append(
                    ColumnMetadata(
                        catalog_schema_table=item["catalog_schema_table"],
                        column_name=item["column_name"],
                        data_type=item["data_type"],
                        column_type=item.get("column_type", "dimension"),
                        semantic_type=item.get("semantic_type")
                        if item.get("semantic_type")
                        else None,
                        aliases=item.get("aliases", []),
                        description=item.get("description", ""),
                        min_value=item.get("min_value"),
                        max_value=item.get("max_value"),
                        avg_value=item.get("avg_value"),
                        cardinality=item.get("cardinality", 0),
                        null_count=item.get("null_count", 0),
                        null_percentage=item.get("null_percentage", 0.0),
                        sample_values=item.get("sample_values", []),
                    )
                )

            logger.info(
                f"Retrieved metadata for {len(column_metadata_list)} columns in {catalog_schema_table}"
            )
            return column_metadata_list

        except Exception as e:
            logger.error(
                f"Failed to get column metadata for table {catalog_schema_table}: {e}"
            )
            return []

    def update_column_aliases(
        self, catalog_schema_table: str, column_name: str, aliases: List[str]
    ) -> bool:
        """Update aliases for a column"""
        try:
            self.column_metadata_table.update_item(
                Key={
                    "catalog_schema_table": catalog_schema_table,  # CHANGED
                    "column_name": column_name,
                },
                UpdateExpression="SET aliases = :aliases",
                ExpressionAttributeValues={":aliases": aliases},
            )

            logger.info(f"Updated aliases for {catalog_schema_table}.{column_name}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to update aliases for {catalog_schema_table}.{column_name}: {e}"
            )
            return False

    def update_column_metadata_fields(
        self,
        catalog_schema_table: str,
        column_name: str,
        aliases: Optional[List[str]] = None,
        description: Optional[str] = None,
        column_type: Optional[str] = None,
        semantic_type: Optional[str] = None,
    ) -> bool:
        """Update multiple column metadata fields"""
        try:
            update_parts = []
            expr_values = {}

            if aliases is not None:
                update_parts.append("aliases = :aliases")
                expr_values[":aliases"] = aliases

            if description is not None:
                update_parts.append("description = :desc")
                expr_values[":desc"] = description

            if column_type is not None:
                update_parts.append("column_type = :ctype")
                expr_values[":ctype"] = column_type

            if semantic_type is not None:
                update_parts.append("semantic_type = :stype")
                expr_values[":stype"] = semantic_type if semantic_type else ""

            if not update_parts:
                return True

            self.column_metadata_table.update_item(
                Key={
                    "catalog_schema_table": catalog_schema_table,
                    "column_name": column_name,
                },
                UpdateExpression="SET " + ", ".join(update_parts),
                ExpressionAttributeValues=expr_values,
            )

            logger.info(f"Updated metadata for {catalog_schema_table}.{column_name}")
            return True

        except Exception as e:
            logger.error(
                f"Failed to update metadata for {catalog_schema_table}.{column_name}: {e}"
            )
            return False

    def delete_all_columns_for_table(self, catalog_schema_table: str) -> bool:
        """Delete all column metadata for a table"""
        try:
            columns = self.get_all_columns_for_table(catalog_schema_table)

            for column in columns:
                self.column_metadata_table.delete_item(
                    Key={
                        "catalog_schema_table": catalog_schema_table,  # CHANGED
                        "column_name": column.column_name,
                    }
                )

            logger.info(
                f"Deleted {len(columns)} column metadata entries for {catalog_schema_table}"
            )
            return True

        except Exception as e:
            logger.error(
                f"Failed to delete column metadata for {catalog_schema_table}: {e}"
            )
            return False

    def get_table_with_columns(
        self, catalog_schema_table: str
    ) -> Optional[TableWithColumns]:
        """Get complete table metadata with all columns"""
        try:
            table_metadata = self.get_table_metadata(catalog_schema_table)
            if not table_metadata:
                return None

            columns = self.get_all_columns_for_table(catalog_schema_table)

            columns_dict = {}
            for col in columns:
                columns_dict[col.column_name] = {
                    "data_type": col.data_type,
                    "column_type": col.column_type,
                    "semantic_type": col.semantic_type,
                    "aliases": col.aliases,
                    "description": col.description,
                    "min_value": col.min_value,
                    "max_value": col.max_value,
                    "avg_value": col.avg_value,
                    "cardinality": col.cardinality,
                    "null_count": col.null_count,
                    "null_percentage": col.null_percentage,
                    "sample_values": col.sample_values,
                }

            return TableWithColumns(
                catalog_schema_table=table_metadata.catalog_schema_table,
                last_updated=table_metadata.last_updated,
                row_count=table_metadata.row_count,
                column_count=table_metadata.column_count,
                schema_status=table_metadata.schema_status,
                schema_changes=table_metadata.schema_changes,
                columns=columns_dict,
            )

        except Exception as e:
            logger.error(
                f"Failed to get table with columns for {catalog_schema_table}: {e}"
            )
            return None


# Global DynamoDB service instance
dynamodb_service = DynamoDBService()
