"""
Complete data wipe script for DynamoDB and Neptune Analytics

This script deletes ALL data from:
- DynamoDB: table_metadata_rag_t1, column_metadata_rag_t2, table_relationships
- Neptune Analytics: All nodes and relationships

Usage:
    python cleanup_all_data.py              # Dry run (preview only)
    python cleanup_all_data.py --execute    # Actually delete data
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import boto3
from botocore.exceptions import ClientError
from app.services.neptune_service import neptune_service
from app.config import settings
from app.utils.logger import app_logger as logger


def cleanup_dynamodb_table(table_name: str, dry_run: bool = True) -> dict:
    """
    Delete all items from a DynamoDB table

    Args:
        table_name: Name of the DynamoDB table
        dry_run: If True, only count items without deleting

    Returns:
        dict with stats: {'scanned': int, 'deleted': int, 'errors': int}
    """
    stats = {'scanned': 0, 'deleted': 0, 'errors': 0}

    try:
        dynamodb = boto3.resource('dynamodb', region_name=settings.aws_region)
        table = dynamodb.Table(table_name)

        logger.info(f"\n{'[DRY RUN] ' if dry_run else ''}Processing table: {table_name}")

        # Scan all items
        scan_kwargs = {}
        done = False

        while not done:
            response = table.scan(**scan_kwargs)
            items = response.get('Items', [])
            stats['scanned'] += len(items)

            if not dry_run and items:
                # Batch delete items
                with table.batch_writer() as batch:
                    for item in items:
                        try:
                            # Get primary key(s)
                            key = {}

                            # All tables have catalog_schema_table or source_table as partition key
                            if 'catalog_schema_table' in item:
                                key['catalog_schema_table'] = item['catalog_schema_table']
                            elif 'source_table' in item:
                                key['source_table'] = item['source_table']

                            # Some tables have sort keys
                            if 'column_name' in item:
                                key['column_name'] = item['column_name']
                            elif 'target_table' in item:
                                key['target_table'] = item['target_table']

                            batch.delete_item(Key=key)
                            stats['deleted'] += 1

                        except Exception as e:
                            stats['errors'] += 1
                            logger.error(f"Error deleting item from {table_name}: {e}")

            # Check if there are more items to scan
            if 'LastEvaluatedKey' in response:
                scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
            else:
                done = True

        if dry_run:
            logger.info(f"  Found {stats['scanned']} items (would delete)")
        else:
            logger.info(f"  ✓ Deleted {stats['deleted']} items (scanned: {stats['scanned']}, errors: {stats['errors']})")

        return stats

    except ClientError as e:
        logger.error(f"DynamoDB error on table {table_name}: {e}")
        stats['errors'] += 1
        return stats
    except Exception as e:
        logger.error(f"Unexpected error on table {table_name}: {e}")
        stats['errors'] += 1
        return stats


def cleanup_neptune(dry_run: bool = True) -> dict:
    """
    Delete all nodes and relationships from Neptune Analytics

    Args:
        dry_run: If True, only count nodes without deleting

    Returns:
        dict with stats: {'nodes': int, 'relationships': int, 'deleted': bool, 'errors': int}
    """
    stats = {'nodes': 0, 'relationships': 0, 'deleted': False, 'errors': 0}

    try:
        logger.info(f"\n{'[DRY RUN] ' if dry_run else ''}Processing Neptune Analytics graph")

        # Count nodes and relationships
        count_query = """
        MATCH (n)
        OPTIONAL MATCH (n)-[r]->()
        RETURN count(DISTINCT n) as node_count, count(DISTINCT r) as rel_count
        """

        result = neptune_service.execute_query(count_query, {})
        if result and len(result) > 0:
            stats['nodes'] = result[0].get('node_count', 0)
            stats['relationships'] = result[0].get('rel_count', 0)

        if dry_run:
            logger.info(f"  Found {stats['nodes']} nodes and {stats['relationships']} relationships (would delete)")
        else:
            # Delete everything - DETACH DELETE removes relationships automatically
            delete_query = "MATCH (n) DETACH DELETE n"
            neptune_service.execute_query(delete_query, {})
            stats['deleted'] = True
            logger.info(f"  ✓ Deleted {stats['nodes']} nodes and {stats['relationships']} relationships")

        return stats

    except Exception as e:
        logger.error(f"Neptune error: {e}", exc_info=True)
        stats['errors'] += 1
        return stats


def main(dry_run: bool = True):
    """
    Main cleanup function

    Args:
        dry_run: If True, preview only without deleting
    """
    logger.info("=" * 80)
    logger.info("DATA CLEANUP SCRIPT - Remove all data from DynamoDB and Neptune")
    logger.info("=" * 80)

    if dry_run:
        logger.info("\n🔍 DRY RUN MODE - No data will be deleted")
        logger.info("Run with --execute flag to actually delete data\n")
    else:
        logger.warning("\n⚠️  EXECUTE MODE - Data will be permanently deleted!")
        logger.warning("This action cannot be undone!\n")

        # Require confirmation
        confirmation = input("Type 'DELETE ALL DATA' to confirm: ")
        if confirmation != "DELETE ALL DATA":
            logger.info("Aborted - confirmation not received")
            return

        logger.info("\n🗑️  Starting deletion...\n")

    # Track overall stats
    total_stats = {
        'dynamodb_scanned': 0,
        'dynamodb_deleted': 0,
        'dynamodb_errors': 0,
        'neptune_nodes': 0,
        'neptune_relationships': 0,
        'neptune_errors': 0
    }

    # DynamoDB table names from config
    dynamodb_tables = [
        'table_metadata_rag_t1',
        'column_metadata_rag_t2',
        'table_relationships'
    ]

    # Step 1: Clean DynamoDB tables
    logger.info("=" * 80)
    logger.info("STEP 1: DynamoDB Tables")
    logger.info("=" * 80)

    for table_name in dynamodb_tables:
        try:
            stats = cleanup_dynamodb_table(table_name, dry_run)
            total_stats['dynamodb_scanned'] += stats['scanned']
            total_stats['dynamodb_deleted'] += stats['deleted']
            total_stats['dynamodb_errors'] += stats['errors']
        except Exception as e:
            logger.error(f"Failed to process table {table_name}: {e}")
            total_stats['dynamodb_errors'] += 1

    # Step 2: Clean Neptune
    logger.info("\n" + "=" * 80)
    logger.info("STEP 2: Neptune Analytics Graph")
    logger.info("=" * 80)

    try:
        stats = cleanup_neptune(dry_run)
        total_stats['neptune_nodes'] = stats['nodes']
        total_stats['neptune_relationships'] = stats['relationships']
        total_stats['neptune_errors'] = stats['errors']
    except Exception as e:
        logger.error(f"Failed to clean Neptune: {e}")
        total_stats['neptune_errors'] += 1

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)

    if dry_run:
        logger.info("\n[DRY RUN] Would delete:")
        logger.info(f"  DynamoDB: {total_stats['dynamodb_scanned']} items across 3 tables")
        logger.info(f"  Neptune: {total_stats['neptune_nodes']} nodes, {total_stats['neptune_relationships']} relationships")
        logger.info(f"\nTo actually delete, run: python cleanup_all_data.py --execute")
    else:
        logger.info("\n✅ Deletion complete:")
        logger.info(f"  DynamoDB: {total_stats['dynamodb_deleted']} items deleted (scanned: {total_stats['dynamodb_scanned']})")
        logger.info(f"  Neptune: {total_stats['neptune_nodes']} nodes and {total_stats['neptune_relationships']} relationships deleted")

        if total_stats['dynamodb_errors'] > 0 or total_stats['neptune_errors'] > 0:
            logger.warning(f"\n⚠️  Errors encountered:")
            logger.warning(f"  DynamoDB: {total_stats['dynamodb_errors']} errors")
            logger.warning(f"  Neptune: {total_stats['neptune_errors']} errors")
            logger.warning("Check logs above for details")
        else:
            logger.info("\n🎉 All data successfully deleted - clean slate ready!")


if __name__ == "__main__":
    # Check for --execute flag
    dry_run = True

    if len(sys.argv) > 1:
        if sys.argv[1] in ["--execute", "-e"]:
            dry_run = False
        elif sys.argv[1] in ["--dry-run", "-d"]:
            dry_run = True
        else:
            print("Usage: python cleanup_all_data.py [--dry-run | --execute]")
            print("")
            print("  --dry-run (default): Preview what would be deleted")
            print("  --execute: Actually delete all data")
            sys.exit(1)

    try:
        main(dry_run=dry_run)
    except KeyboardInterrupt:
        logger.info("\n\nAborted by user (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
