#!/usr/bin/env python3
"""
Worker script - Daily schema change detector

This script should be run daily (via cron or scheduled task) to detect schema changes.

Usage:
    python scripts/worker_schema_checker.py                    # Check all tables
    python scripts/worker_schema_checker.py --table TABLE_NAME # Check specific table
"""
import sys
import os
import argparse
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services import (
    starburst_service, dynamodb_service, schema_comparator
)
from app.models import SchemaStatus
from app.config import get_all_table_names
from app.utils.logger import app_logger as logger


def check_schema_for_table(table_name: str) -> bool:
    """
    Check schema for a single table and update status if changes detected
    
    Args:
        table_name: Name of the table to check
        
    Returns:
        True if changes detected, False otherwise
    """
    try:
        logger.info(f"Checking schema for table: {table_name}")
        
        # Get current schema from Starburst
        try:
            current_schema = starburst_service.get_table_schema(table_name)
        except Exception as e:
            logger.error(f"Failed to get current schema for {table_name}: {e}")
            return False
        
        # Get stored schema from DynamoDB
        table_metadata = dynamodb_service.get_table_metadata(table_name)
        if not table_metadata:
            logger.warning(f"No metadata found for {table_name}. Skipping schema check.")
            return False
        
        # Get column metadata to extract stored schema
        column_metadata_list = dynamodb_service.get_all_columns_for_table(table_name)
        if not column_metadata_list:
            logger.warning(f"No column metadata found for {table_name}. Skipping schema check.")
            return False
        
        stored_schema = schema_comparator.get_schema_from_column_metadata(column_metadata_list)
        
        # Compare schemas
        has_changes, schema_change = schema_comparator.compare_schemas(
            current_schema=current_schema,
            stored_schema=stored_schema
        )
        
        if has_changes:
            logger.warning(f"⚠️  Schema changes detected for {table_name}:")
            if schema_change.new_columns:
                logger.warning(f"   New columns: {', '.join(schema_change.new_columns)}")
            if schema_change.removed_columns:
                logger.warning(f"   Removed columns: {', '.join(schema_change.removed_columns)}")
            if schema_change.type_changes:
                logger.warning(f"   Type changes: {len(schema_change.type_changes)} column(s)")
                for change in schema_change.type_changes:
                    logger.warning(f"     - {change['column']}: {change['old_type']} → {change['new_type']}")
            
            # Update schema status in DynamoDB
            success = dynamodb_service.update_table_schema_status(
                table_name=table_name,
                status=SchemaStatus.SCHEMA_CHANGED,
                schema_changes=schema_change
            )
            
            if success:
                logger.info(f"✅ Updated schema status for {table_name} to SCHEMA_CHANGED")
            else:
                logger.error(f"❌ Failed to update schema status for {table_name}")
            
            return True
        
        else:
            logger.info(f"✅ No schema changes detected for {table_name}")
            
            # If status was SCHEMA_CHANGED but now it's back to normal, update it
            if table_metadata.schema_status == SchemaStatus.SCHEMA_CHANGED:
                dynamodb_service.update_table_schema_status(
                    table_name=table_name,
                    status=SchemaStatus.CURRENT,
                    schema_changes=None
                )
                logger.info(f"✅ Reverted schema status for {table_name} to CURRENT")
            
            return False
    
    except Exception as e:
        logger.error(f"Error checking schema for {table_name}: {e}", exc_info=True)
        return False


def main():
    """Main function for schema checker worker"""
    parser = argparse.ArgumentParser(description="Check for schema changes in tables")
    parser.add_argument(
        "--table",
        type=str,
        help="Specific table name to check (if not provided, checks all tables)"
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 70)
    logger.info("METADATA EXPLORER - SCHEMA CHANGE CHECKER")
    logger.info(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 70)
    
    try:
        if args.table:
            # Check specific table
            logger.info(f"Checking schema for table: {args.table}")
            has_changes = check_schema_for_table(args.table)
            
            if has_changes:
                logger.warning(f"⚠️  Schema changes detected for {args.table}")
                return 1
            else:
                logger.info(f"✅ No schema changes for {args.table}")
                return 0
        
        else:
            # Check all tables
            all_tables = dynamodb_service.get_all_table_metadata()
            table_names = [tm.table_name for tm in all_tables]
            
            logger.info(f"Checking schema for {len(table_names)} tables...")
            logger.info("")
            
            changes_detected = {}
            
            for i, table_name in enumerate(table_names, 1):
                logger.info(f"[{i}/{len(table_names)}] Checking: {table_name}")
                has_changes = check_schema_for_table(table_name)
                changes_detected[table_name] = has_changes
            
            # Summary
            total_changes = sum(1 for v in changes_detected.values() if v)
            
            logger.info("")
            logger.info("=" * 70)
            logger.info("SUMMARY")
            logger.info("=" * 70)
            logger.info(f"Total tables checked: {len(changes_detected)}")
            logger.info(f"Tables with changes: {total_changes}")
            logger.info(f"Tables without changes: {len(changes_detected) - total_changes}")
            
            if total_changes > 0:
                logger.warning("")
                logger.warning(f"Tables with schema changes ({total_changes}):")
                for table, has_changes in changes_detected.items():
                    if has_changes:
                        logger.warning(f"  ⚠️  {table}")
            
            logger.info("=" * 70)
            
            return 0
    
    except KeyboardInterrupt:
        logger.warning("\nOperation interrupted by user")
        return 130
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())