"""
Verification script to check Neptune search_mode tags vs DynamoDB

This script:
1. Lists all tables in Neptune with their search_mode tags
2. Compares with DynamoDB values
3. Identifies mismatches that need fixing

Usage:
    python verify_neptune_tags.py
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.dynamodb import dynamodb_service
from app.services.neptune_service import neptune_service
from app.utils.logger import app_logger as logger


def verify_neptune_tags():
    """
    Verify Neptune search_mode tags match DynamoDB values
    """
    logger.info("=" * 80)
    logger.info("NEPTUNE TAG VERIFICATION - Checking search_mode consistency")
    logger.info("=" * 80)

    # Step 1: Get all tables from Neptune
    logger.info("\n📋 Step 1: Querying all tables in Neptune...")
    try:
        query = """
        MATCH (t:Table)
        RETURN t.name as table_name, t.search_mode as search_mode
        ORDER BY t.name
        """
        neptune_tables = neptune_service.execute_query(query, {})
        logger.info(f"Found {len(neptune_tables)} tables in Neptune")
    except Exception as e:
        logger.error(f"Failed to query Neptune: {e}")
        return

    # Step 2: Get all tables from DynamoDB
    logger.info("\n📋 Step 2: Scanning DynamoDB for comparison...")
    all_tables = dynamodb_service.get_all_tables()

    # Create lookup map: table_name -> (search_mode, neptune_import_status)
    dynamodb_map = {
        t.catalog_schema_table: (t.search_mode, t.neptune_import_status.value)
        for t in all_tables
    }
    logger.info(f"Found {len(all_tables)} tables in DynamoDB")

    # Step 3: Compare and report
    logger.info("\n" + "=" * 80)
    logger.info("COMPARISON RESULTS")
    logger.info("=" * 80)

    mismatches = []
    stale_nodes = []
    correct = []

    for neptune_row in neptune_tables:
        table_name = neptune_row['table_name']
        neptune_mode = neptune_row.get('search_mode')

        if table_name not in dynamodb_map:
            logger.warning(f"\n⚠️  {table_name}")
            logger.warning(f"    Neptune: search_mode={neptune_mode}")
            logger.warning(f"    DynamoDB: NOT FOUND (orphaned node)")
            stale_nodes.append(table_name)
            continue

        dynamodb_mode, neptune_status = dynamodb_map[table_name]

        # Check if DynamoDB says not imported but node exists in Neptune
        if neptune_status != 'imported':
            logger.warning(f"\n⚠️  {table_name}")
            logger.warning(f"    Neptune: search_mode={neptune_mode} (NODE EXISTS)")
            logger.warning(f"    DynamoDB: search_mode={dynamodb_mode}, status={neptune_status}")
            logger.warning(f"    🔴 STALE NODE - DynamoDB says '{neptune_status}' but node exists in Neptune")
            stale_nodes.append(table_name)
            continue

        # Compare search_mode values
        if neptune_mode != dynamodb_mode:
            logger.warning(f"\n⚠️  {table_name}")
            logger.warning(f"    Neptune: search_mode={neptune_mode}")
            logger.warning(f"    DynamoDB: search_mode={dynamodb_mode}")
            logger.warning(f"    🔴 MISMATCH - Tags don't match!")
            mismatches.append((table_name, neptune_mode, dynamodb_mode))
        else:
            correct.append(table_name)

    # Print summary
    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)
    logger.info(f"✅ Correct (matching tags): {len(correct)}")
    logger.info(f"⚠️  Mismatched tags: {len(mismatches)}")
    logger.info(f"🔴 Stale/orphaned nodes: {len(stale_nodes)}")

    # Recommendations
    if mismatches or stale_nodes:
        logger.info("\n" + "=" * 80)
        logger.info("RECOMMENDATIONS")
        logger.info("=" * 80)

        if mismatches:
            logger.info("\n📝 For MISMATCHED tags:")
            logger.info("   Option 1: Update tags in MetadataViewer UI (will sync to Neptune)")
            logger.info("   Option 2: Re-import these tables to Neptune")
            logger.info("\n   Tables with mismatched tags:")
            for table_name, neptune_mode, dynamodb_mode in mismatches:
                logger.info(f"      • {table_name}")

        if stale_nodes:
            logger.info("\n🗑️  For STALE nodes:")
            logger.info("   These tables exist in Neptune but are marked as 'not_imported' in DynamoDB")
            logger.info("   Run: python cleanup_stale_neptune_nodes.py --execute")
            logger.info("\n   Stale nodes to clean up:")
            for table_name in stale_nodes:
                logger.info(f"      • {table_name}")
    else:
        logger.info("\n🎉 All tables are in sync! Neptune matches DynamoDB perfectly.")


if __name__ == "__main__":
    try:
        verify_neptune_tags()
    except Exception as e:
        logger.error(f"Error during verification: {e}", exc_info=True)
        sys.exit(1)
