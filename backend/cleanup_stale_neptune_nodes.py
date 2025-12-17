"""
Cleanup script to remove stale Neptune nodes for tables marked as 'not_imported' in DynamoDB

This script:
1. Scans DynamoDB for all tables with neptune_import_status != 'imported'
2. Deletes their nodes from Neptune to keep the graph in sync
3. Useful after failed imports or when tables have been reimported

Usage:
    python cleanup_stale_neptune_nodes.py [--dry-run]
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.dynamodb import dynamodb_service
from app.services.neptune_service import neptune_service
from app.utils.logger import app_logger as logger


def cleanup_stale_neptune_nodes(dry_run: bool = True):
    """
    Remove Neptune nodes for tables that are not marked as 'imported' in DynamoDB

    Args:
        dry_run: If True, only print what would be deleted without actually deleting
    """
    logger.info("=" * 80)
    logger.info("NEPTUNE CLEANUP SCRIPT - Removing stale nodes")
    logger.info("=" * 80)

    # Step 1: Get all tables from DynamoDB
    logger.info("\n📋 Step 1: Scanning DynamoDB for all tables...")
    all_tables = dynamodb_service.get_all_tables()
    logger.info(f"Found {len(all_tables)} total tables in DynamoDB")

    # Step 2: Filter tables that are NOT imported
    not_imported_tables = [
        t for t in all_tables
        if t.neptune_import_status.value != 'imported'
    ]

    logger.info(f"\n🔍 Step 2: Found {len(not_imported_tables)} tables NOT imported to Neptune:")
    for table in not_imported_tables:
        status = table.neptune_import_status.value
        logger.info(f"  - {table.catalog_schema_table} (status: {status})")

    if not not_imported_tables:
        logger.info("\n✅ No stale nodes to clean up - all tables are in sync!")
        return

    # Step 3: Delete from Neptune
    logger.info(f"\n🗑️  Step 3: {'[DRY RUN] Would delete' if dry_run else 'Deleting'} {len(not_imported_tables)} tables from Neptune...")

    deleted_count = 0
    failed_count = 0

    for table in not_imported_tables:
        table_name = table.catalog_schema_table

        if dry_run:
            logger.info(f"  [DRY RUN] Would delete: {table_name}")
            deleted_count += 1
        else:
            logger.info(f"  Deleting: {table_name}")
            success = neptune_service.delete_table(table_name)
            if success:
                deleted_count += 1
            else:
                failed_count += 1

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("CLEANUP SUMMARY")
    logger.info("=" * 80)
    if dry_run:
        logger.info(f"[DRY RUN] Would delete {deleted_count} tables from Neptune")
        logger.info("\nTo actually delete, run: python cleanup_stale_neptune_nodes.py --execute")
    else:
        logger.info(f"✅ Successfully deleted: {deleted_count} tables")
        if failed_count > 0:
            logger.info(f"❌ Failed to delete: {failed_count} tables")
        logger.info("\n🎉 Cleanup complete! Neptune is now in sync with DynamoDB.")


if __name__ == "__main__":
    # Check for --dry-run or --execute flag
    dry_run = True
    if len(sys.argv) > 1:
        if sys.argv[1] in ["--execute", "-e"]:
            dry_run = False
            logger.warning("\n⚠️  WARNING: Running in EXECUTE mode - will actually delete nodes!")
            response = input("Are you sure you want to proceed? (yes/no): ")
            if response.lower() != "yes":
                logger.info("Aborted by user")
                sys.exit(0)
        elif sys.argv[1] in ["--dry-run", "-d"]:
            dry_run = True
        else:
            print("Usage: python cleanup_stale_neptune_nodes.py [--dry-run | --execute]")
            sys.exit(1)

    try:
        cleanup_stale_neptune_nodes(dry_run=dry_run)
    except Exception as e:
        logger.error(f"Error during cleanup: {e}", exc_info=True)
        sys.exit(1)
