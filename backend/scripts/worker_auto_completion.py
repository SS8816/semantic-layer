"""
Auto-completion worker script for table operations

This worker script runs periodically (every 30 minutes via cron) to ensure all
onboarded tables have completed enrichment, relationship detection, and Neptune import.

It automatically:
- Enriches tables with metadata if enrichment is incomplete
- Detects relationships if enrichment is complete but relationships are not
- Imports to Neptune if enrichment is complete but import is not
- Respects dependencies (enrichment → relationships/neptune)
- Handles retries (max 3 attempts per operation)
- Skips tables with operations IN_PROGRESS to avoid conflicts

Usage:
    python worker_auto_completion.py
"""

import sys
import os
from datetime import datetime
from typing import Dict, List

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.dynamodb import dynamodb_service
from app.services.metadata_generator import metadata_generator
from app.services.relationship_tasks import start_relationship_detection_task
from app.services.neptune_service import neptune_service
from app.models.table import (
    EnrichmentStatus,
    RelationshipDetectionStatus,
    NeptuneImportStatus
)
from app.utils.logger import app_logger as logger


# Constants
MAX_RETRIES = 3


def should_process_enrichment(table_metadata) -> bool:
    """Check if enrichment should be processed for this table"""
    status = table_metadata.enrichment_status
    retry_count = table_metadata.enrichment_retry_count

    # Skip if in progress
    if status == EnrichmentStatus.IN_PROGRESS:
        return False

    # Skip if maxed out retries
    if retry_count >= MAX_RETRIES:
        return False

    # Process if not started or failed (with retries remaining)
    if status in [EnrichmentStatus.NOT_STARTED, EnrichmentStatus.FAILED]:
        return True

    return False


def should_process_relationships(table_metadata) -> bool:
    """Check if relationships should be processed for this table"""
    # Dependency: enrichment must be completed
    if table_metadata.enrichment_status != EnrichmentStatus.COMPLETED:
        return False

    status = table_metadata.relationship_detection_status
    retry_count = table_metadata.relationship_retry_count

    # Skip if in progress
    if status == RelationshipDetectionStatus.IN_PROGRESS:
        return False

    # Skip if maxed out retries
    if retry_count >= MAX_RETRIES:
        return False

    # Process if not started or failed (with retries remaining)
    if status in [RelationshipDetectionStatus.NOT_STARTED, RelationshipDetectionStatus.FAILED]:
        return True

    return False


def should_process_neptune(table_metadata) -> bool:
    """Check if Neptune import should be processed for this table"""
    # Dependency: enrichment must be completed
    if table_metadata.enrichment_status != EnrichmentStatus.COMPLETED:
        return False

    status = table_metadata.neptune_import_status
    retry_count = table_metadata.neptune_retry_count

    # Skip if importing
    if status == NeptuneImportStatus.IMPORTING:
        return False

    # Skip if maxed out retries
    if retry_count >= MAX_RETRIES:
        return False

    # Process if not imported or failed (with retries remaining)
    if status in [NeptuneImportStatus.NOT_IMPORTED, NeptuneImportStatus.FAILED]:
        return True

    return False


def process_enrichment(catalog_schema_table: str) -> bool:
    """
    Run metadata generation (enrichment) for a table

    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Starting enrichment for {catalog_schema_table}")

        # Update status to IN_PROGRESS
        dynamodb_service.update_table_metadata_field(
            catalog_schema_table,
            'enrichment_status',
            EnrichmentStatus.IN_PROGRESS.value
        )

        # Parse table name
        parts = catalog_schema_table.split('.')
        if len(parts) != 3:
            raise ValueError(f"Invalid table name format: {catalog_schema_table}")

        catalog, schema, table = parts

        # Run metadata generation
        metadata_generator.generate_metadata(catalog, schema, table)

        # Update status to COMPLETED
        dynamodb_service.update_table_metadata_fields(
            catalog_schema_table,
            {
                'enrichment_status': EnrichmentStatus.COMPLETED.value,
                'enrichment_timestamp': datetime.now().isoformat(),
                'enrichment_error': None
            }
        )

        logger.info(f"✅ Enrichment completed for {catalog_schema_table}")
        return True

    except Exception as e:
        logger.error(f"❌ Enrichment failed for {catalog_schema_table}: {e}", exc_info=True)

        # Get current retry count
        table_metadata = dynamodb_service.get_table_metadata(catalog_schema_table)
        new_retry_count = (table_metadata.enrichment_retry_count if table_metadata else 0) + 1

        # Update status to FAILED and increment retry count
        dynamodb_service.update_table_metadata_fields(
            catalog_schema_table,
            {
                'enrichment_status': EnrichmentStatus.FAILED.value,
                'enrichment_retry_count': new_retry_count,
                'enrichment_error': str(e)[:500]  # Limit error message length
            }
        )

        return False


def process_relationships(catalog_schema_table: str) -> bool:
    """
    Run relationship detection for a table

    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Starting relationship detection for {catalog_schema_table}")

        # Update status to IN_PROGRESS
        dynamodb_service.update_table_metadata_field(
            catalog_schema_table,
            'relationship_detection_status',
            RelationshipDetectionStatus.IN_PROGRESS.value
        )

        # Start relationship detection (runs in background thread)
        start_relationship_detection_task(catalog_schema_table)

        logger.info(f"✅ Relationship detection started for {catalog_schema_table}")
        # Note: Status will be updated to COMPLETED by the background thread
        return True

    except Exception as e:
        logger.error(f"❌ Relationship detection failed for {catalog_schema_table}: {e}", exc_info=True)

        # Get current retry count
        table_metadata = dynamodb_service.get_table_metadata(catalog_schema_table)
        new_retry_count = (table_metadata.relationship_retry_count if table_metadata else 0) + 1

        # Update status to FAILED and increment retry count
        dynamodb_service.update_table_metadata_fields(
            catalog_schema_table,
            {
                'relationship_detection_status': RelationshipDetectionStatus.FAILED.value,
                'relationship_retry_count': new_retry_count,
                'relationship_error': str(e)[:500]
            }
        )

        return False


def process_neptune_import(catalog_schema_table: str) -> bool:
    """
    Import table to Neptune Analytics

    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Starting Neptune import for {catalog_schema_table}")

        # Update status to IMPORTING
        dynamodb_service.update_table_metadata_field(
            catalog_schema_table,
            'neptune_import_status',
            NeptuneImportStatus.IMPORTING.value
        )

        # Get table metadata
        table_metadata = dynamodb_service.get_table_metadata(catalog_schema_table)
        if not table_metadata:
            raise ValueError(f"Table metadata not found: {catalog_schema_table}")

        # Import to Neptune
        success = neptune_service.import_table_to_neptune(catalog_schema_table)

        if success:
            # Update status to IMPORTED
            dynamodb_service.update_table_metadata_fields(
                catalog_schema_table,
                {
                    'neptune_import_status': NeptuneImportStatus.IMPORTED.value,
                    'neptune_import_timestamp': datetime.now().isoformat(),
                    'neptune_import_error': None
                }
            )
            logger.info(f"✅ Neptune import completed for {catalog_schema_table}")
            return True
        else:
            raise Exception("Neptune import returned False")

    except Exception as e:
        logger.error(f"❌ Neptune import failed for {catalog_schema_table}: {e}", exc_info=True)

        # Get current retry count
        table_metadata = dynamodb_service.get_table_metadata(catalog_schema_table)
        new_retry_count = (table_metadata.neptune_retry_count if table_metadata else 0) + 1

        # Update status to FAILED and increment retry count
        dynamodb_service.update_table_metadata_fields(
            catalog_schema_table,
            {
                'neptune_import_status': NeptuneImportStatus.FAILED.value,
                'neptune_retry_count': new_retry_count,
                'neptune_import_error': str(e)[:500]
            }
        )

        return False


def process_table(table_metadata) -> Dict[str, bool]:
    """
    Process a single table - check and run incomplete operations

    Returns:
        Dict with operation results: {'enrichment': bool, 'relationships': bool, 'neptune': bool}
    """
    catalog_schema_table = table_metadata.catalog_schema_table
    results = {
        'enrichment': None,
        'relationships': None,
        'neptune': None
    }

    # Check and process enrichment
    if should_process_enrichment(table_metadata):
        results['enrichment'] = process_enrichment(catalog_schema_table)

        # Refresh metadata after enrichment
        table_metadata = dynamodb_service.get_table_metadata(catalog_schema_table)
        if not table_metadata:
            return results

    # Check and process relationships (only if enrichment completed)
    if should_process_relationships(table_metadata):
        results['relationships'] = process_relationships(catalog_schema_table)

    # Check and process Neptune import (only if enrichment completed)
    if should_process_neptune(table_metadata):
        results['neptune'] = process_neptune_import(catalog_schema_table)

    return results


def main():
    """Main worker function - process all onboarded tables"""
    logger.info("=" * 80)
    logger.info("AUTO-COMPLETION WORKER - Starting run")
    logger.info("=" * 80)

    # Track statistics
    stats = {
        'total_tables': 0,
        'enrichment_processed': 0,
        'enrichment_success': 0,
        'enrichment_failed': 0,
        'relationships_processed': 0,
        'relationships_success': 0,
        'relationships_failed': 0,
        'neptune_processed': 0,
        'neptune_success': 0,
        'neptune_failed': 0
    }

    try:
        # Get all onboarded tables
        all_tables = dynamodb_service.get_all_tables()
        stats['total_tables'] = len(all_tables)

        logger.info(f"Found {stats['total_tables']} onboarded tables")

        if stats['total_tables'] == 0:
            logger.info("No tables to process")
            return

        # Process each table sequentially
        for table_metadata in all_tables:
            catalog_schema_table = table_metadata.catalog_schema_table
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing: {catalog_schema_table}")
            logger.info(f"  Enrichment: {table_metadata.enrichment_status.value} (retry: {table_metadata.enrichment_retry_count})")
            logger.info(f"  Relationships: {table_metadata.relationship_detection_status.value} (retry: {table_metadata.relationship_retry_count})")
            logger.info(f"  Neptune: {table_metadata.neptune_import_status.value} (retry: {table_metadata.neptune_retry_count})")

            # Process table
            results = process_table(table_metadata)

            # Update statistics
            if results['enrichment'] is not None:
                stats['enrichment_processed'] += 1
                if results['enrichment']:
                    stats['enrichment_success'] += 1
                else:
                    stats['enrichment_failed'] += 1

            if results['relationships'] is not None:
                stats['relationships_processed'] += 1
                if results['relationships']:
                    stats['relationships_success'] += 1
                else:
                    stats['relationships_failed'] += 1

            if results['neptune'] is not None:
                stats['neptune_processed'] += 1
                if results['neptune']:
                    stats['neptune_success'] += 1
                else:
                    stats['neptune_failed'] += 1

        # Summary
        logger.info("\n" + "=" * 80)
        logger.info("WORKER RUN SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total tables scanned: {stats['total_tables']}")
        logger.info(f"\nEnrichment:")
        logger.info(f"  Processed: {stats['enrichment_processed']}")
        logger.info(f"  Succeeded: {stats['enrichment_success']}")
        logger.info(f"  Failed: {stats['enrichment_failed']}")
        logger.info(f"\nRelationships:")
        logger.info(f"  Processed: {stats['relationships_processed']}")
        logger.info(f"  Succeeded: {stats['relationships_success']}")
        logger.info(f"  Failed: {stats['relationships_failed']}")
        logger.info(f"\nNeptune Import:")
        logger.info(f"  Processed: {stats['neptune_processed']}")
        logger.info(f"  Succeeded: {stats['neptune_success']}")
        logger.info(f"  Failed: {stats['neptune_failed']}")

        logger.info("\n✅ Worker run completed")

    except Exception as e:
        logger.error(f"Fatal error in worker: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n\nWorker interrupted by user (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)
