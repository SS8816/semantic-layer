"""
DynamoDB service for table relationships - Complete version with hybrid approach
Includes ALL methods from original + subtype support
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

import boto3

from app.config import settings
from app.utils.logger import app_logger as logger


class DynamoDBRelationshipsService:
    """Service for storing and retrieving table relationships in DynamoDB"""

    def __init__(self):
        """Initialize DynamoDB client and table name"""
        self.dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
        self.table_name = "table_relationships"
        self.table = self.dynamodb.Table(self.table_name)

    def ensure_table_exists(self):
        """
        Create the relationships table if it doesn't exist

        Table Schema:
        - PK: relationship_id (UUID)
        - GSI1: source_table (for querying all relationships from a table)
        - GSI2: target_table (for querying all relationships to a table)
        """
        try:
            dynamodb_client = boto3.client("dynamodb", region_name=settings.aws_region)

            # Check if table exists
            existing_tables = dynamodb_client.list_tables()["TableNames"]

            if self.table_name in existing_tables:
                logger.info(f"Table {self.table_name} already exists")
                return

            # Create table
            logger.info(f"Creating table {self.table_name}...")

            dynamodb_client.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {
                        "AttributeName": "relationship_id",
                        "KeyType": "HASH",  # Partition key
                    }
                ],
                AttributeDefinitions=[
                    {"AttributeName": "relationship_id", "AttributeType": "S"},
                    {"AttributeName": "source_table", "AttributeType": "S"},
                    {"AttributeName": "target_table", "AttributeType": "S"},
                ],
                GlobalSecondaryIndexes=[
                    {
                        "IndexName": "source_table_index",
                        "KeySchema": [
                            {"AttributeName": "source_table", "KeyType": "HASH"}
                        ],
                        "Projection": {"ProjectionType": "ALL"},
                        "ProvisionedThroughput": {
                            "ReadCapacityUnits": 5,
                            "WriteCapacityUnits": 5,
                        },
                    },
                    {
                        "IndexName": "target_table_index",
                        "KeySchema": [
                            {"AttributeName": "target_table", "KeyType": "HASH"}
                        ],
                        "Projection": {"ProjectionType": "ALL"},
                        "ProvisionedThroughput": {
                            "ReadCapacityUnits": 5,
                            "WriteCapacityUnits": 5,
                        },
                    },
                ],
                ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
            )

            # Wait for table to be created
            waiter = dynamodb_client.get_waiter("table_exists")
            waiter.wait(TableName=self.table_name)

            logger.info(f"✅ Table {self.table_name} created successfully")

        except Exception as e:
            logger.error(f"Failed to create table {self.table_name}: {e}")
            raise

    def store_relationship(
        self,
        source_table: str,
        source_column: str,
        target_table: str,
        target_column: str,
        relationship_type: str,
        confidence: float,
        reasoning: str = "",
        relationship_subtype: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Store a single relationship in DynamoDB

        Args:
            source_table: Full table name (catalog.schema.table)
            source_column: Column name in source table
            target_table: Full table name (catalog.schema.table)
            target_column: Column name in target table
            relationship_type: Main type (foreign_key, semantic, name_based)
            confidence: Confidence score (0-1)
            reasoning: Explanation from GPT
            relationship_subtype: Optional subtype (geographic, one_to_many, etc.)
            metadata: Additional metadata

        Returns:
            relationship_id
        """
        try:
            relationship_id = str(uuid.uuid4())

            item = {
                "relationship_id": relationship_id,
                "source_table": source_table,
                "source_column": source_column,
                "target_table": target_table,
                "target_column": target_column,
                "relationship_type": relationship_type,
                "confidence": Decimal(str(confidence)),
                "reasoning": reasoning,
                "detected_at": datetime.utcnow().isoformat(),
                "detected_by": "gpt-5",
            }

            # Add subtype if present
            if relationship_subtype:
                item["relationship_subtype"] = relationship_subtype

            if metadata:
                item["metadata"] = metadata

            self.table.put_item(Item=item)

            subtype_str = f" ({relationship_subtype})" if relationship_subtype else ""
            logger.info(
                f"✅ Stored relationship: {source_table}.{source_column} → "
                f"{target_table}.{target_column} ({relationship_type}{subtype_str}, confidence: {confidence:.2f})"
            )

            return relationship_id

        except Exception as e:
            logger.error(f"Failed to store relationship: {e}")
            raise

    def store_relationships_batch(self, relationships: List[Dict[str, Any]]) -> int:
        """
        Store multiple relationships in batch

        Args:
            relationships: List of relationship dictionaries

        Returns:
            Number of relationships stored
        """
        try:
            stored_count = 0

            with self.table.batch_writer() as batch:
                for rel in relationships:
                    relationship_id = str(uuid.uuid4())

                    item = {
                        "relationship_id": relationship_id,
                        "source_table": rel["source_table"],
                        "source_column": rel["source_column"],
                        "target_table": rel["target_table"],
                        "target_column": rel["target_column"],
                        "relationship_type": rel["relationship_type"],
                        "confidence": Decimal(str(rel["confidence"])),
                        "reasoning": rel.get("reasoning", ""),
                        "detected_at": datetime.utcnow().isoformat(),
                        "detected_by": "gpt-5",
                    }

                    # Add subtype if present
                    if "relationship_subtype" in rel and rel["relationship_subtype"]:
                        item["relationship_subtype"] = rel["relationship_subtype"]

                    if "metadata" in rel:
                        item["metadata"] = rel["metadata"]

                    batch.put_item(Item=item)
                    stored_count += 1

            logger.info(f"✅ Stored {stored_count} relationships in batch")
            return stored_count

        except Exception as e:
            logger.error(f"Failed to store relationships batch: {e}")
            raise

    def get_relationships_by_source_table(
        self, source_table: str
    ) -> List[Dict[str, Any]]:
        """
        Get all relationships where the given table is the source

        Args:
            source_table: Full table name (catalog.schema.table)

        Returns:
            List of relationship dictionaries
        """
        try:
            response = self.table.query(
                IndexName="source_table_index",
                KeyConditionExpression="source_table = :table",
                ExpressionAttributeValues={":table": source_table},
            )

            relationships = response.get("Items", [])
            logger.info(f"Found {len(relationships)} relationships from {source_table}")

            return relationships

        except Exception as e:
            logger.error(f"Failed to get relationships by source table: {e}")
            return []

    def get_relationships_by_target_table(
        self, target_table: str
    ) -> List[Dict[str, Any]]:
        """
        Get all relationships where the given table is the target

        Args:
            target_table: Full table name (catalog.schema.table)

        Returns:
            List of relationship dictionaries
        """
        try:
            response = self.table.query(
                IndexName="target_table_index",
                KeyConditionExpression="target_table = :table",
                ExpressionAttributeValues={":table": target_table},
            )

            relationships = response.get("Items", [])
            logger.info(f"Found {len(relationships)} relationships to {target_table}")

            return relationships

        except Exception as e:
            logger.error(f"Failed to get relationships by target table: {e}")
            return []

    def get_all_relationships_for_table(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get all relationships (both source and target) for a table

        Args:
            table_name: Full table name (catalog.schema.table)

        Returns:
            List of relationship dictionaries
        """
        source_rels = self.get_relationships_by_source_table(table_name)
        target_rels = self.get_relationships_by_target_table(table_name)

        all_rels = source_rels + target_rels
        logger.info(f"Found {len(all_rels)} total relationships for {table_name}")

        return all_rels

    def batch_get_relationships_for_tables(
        self, table_names: List[str]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Batch get all relationships (source and target) for multiple tables

        Args:
            table_names: List of full table names

        Returns:
            Dictionary mapping table_name -> list of relationships
        """
        try:
            if not table_names:
                return {}

            results = {}

            # Query all source relationships
            for table_name in table_names:
                source_rels = self.get_relationships_by_source_table(table_name)
                target_rels = self.get_relationships_by_target_table(table_name)
                results[table_name] = source_rels + target_rels

            total_rels = sum(len(rels) for rels in results.values())
            logger.info(
                f"Batch retrieved {total_rels} relationships for {len(table_names)} tables"
            )

            return results

        except Exception as e:
            logger.error(f"Failed to batch get relationships: {e}")
            return {}

    def get_relationships_by_type(
        self,
        table_name: str,
        relationship_type: Optional[str] = None,
        relationship_subtype: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get relationships filtered by type and/or subtype

        Args:
            table_name: Full table name
            relationship_type: Main type (foreign_key, semantic, name_based)
            relationship_subtype: Subtype (geographic, one_to_many, etc.)

        Returns:
            Filtered list of relationships
        """
        all_rels = self.get_all_relationships_for_table(table_name)

        filtered = all_rels

        if relationship_type:
            filtered = [
                r for r in filtered if r.get("relationship_type") == relationship_type
            ]

        if relationship_subtype:
            filtered = [
                r
                for r in filtered
                if r.get("relationship_subtype") == relationship_subtype
            ]

        logger.info(
            f"Filtered to {len(filtered)} relationships "
            f"(type: {relationship_type or 'any'}, subtype: {relationship_subtype or 'any'})"
        )

        return filtered

    def delete_relationship(self, relationship_id: str) -> bool:
        """
        Delete a single relationship by ID

        Args:
            relationship_id: UUID of the relationship

        Returns:
            True if deleted, False otherwise
        """
        try:
            self.table.delete_item(Key={"relationship_id": relationship_id})
            logger.info(f"Deleted relationship {relationship_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete relationship {relationship_id}: {e}")
            return False

    def delete_relationships_for_table(self, table_name: str) -> int:
        """
        Delete all relationships involving a table (when table is deleted)

        Args:
            table_name: Full table name (catalog.schema.table)

        Returns:
            Number of relationships deleted
        """
        try:
            relationships = self.get_all_relationships_for_table(table_name)

            deleted_count = 0
            with self.table.batch_writer() as batch:
                for rel in relationships:
                    batch.delete_item(Key={"relationship_id": rel["relationship_id"]})
                    deleted_count += 1

            logger.info(f"Deleted {deleted_count} relationships for {table_name}")
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to delete relationships: {e}")
            return 0

    def get_relationship_by_id(self, relationship_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single relationship by ID

        Args:
            relationship_id: UUID of the relationship

        Returns:
            Relationship dictionary or None
        """
        try:
            response = self.table.get_item(Key={"relationship_id": relationship_id})
            return response.get("Item")
        except Exception as e:
            logger.error(f"Failed to get relationship {relationship_id}: {e}")
            return None

    def update_relationship_confidence(
        self, relationship_id: str, new_confidence: float
    ) -> bool:
        """
        Update confidence score for a relationship

        Args:
            relationship_id: UUID of the relationship
            new_confidence: New confidence score (0-1)

        Returns:
            True if updated, False otherwise
        """
        try:
            self.table.update_item(
                Key={"relationship_id": relationship_id},
                UpdateExpression="SET confidence = :conf",
                ExpressionAttributeValues={":conf": float(new_confidence)},
            )
            logger.info(f"Updated confidence for {relationship_id} to {new_confidence}")
            return True
        except Exception as e:
            logger.error(f"Failed to update confidence: {e}")
            return False


# Global instance
relationships_service = DynamoDBRelationshipsService()
