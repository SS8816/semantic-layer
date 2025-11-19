#!/usr/bin/env python3
"""
Initial setup script - Generate metadata for tables

Usage:
    python scripts/initial_setup.py                                    # Generate for all tables
    python scripts/initial_setup.py --table TABLE_NAME                 # Generate for specific table
    python scripts/initial_setup.py --table TABLE_NAME --force         # Force regeneration
    python scripts/initial_setup.py --catalog here_explorer --schema silverstone   # Different catalog/schema
"""

import argparse
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.dynamodb_relationships import relationships_service
from app.services.metadata_generator import metadata_generator
from app.services.starburst import starburst_service
from app.utils.logger import app_logger as logger


def main():
    """Main function for initial setup"""
    parser = argparse.ArgumentParser(description="Generate metadata for tables")
    parser.add_argument("--table", type=str, help="Specific table name to process")
    parser.add_argument(
        "--catalog",
        type=str,
        default="here_explorer",  # CHANGED default
        help="Catalog name (default: here_explorer)",
    )
    parser.add_argument(
        "--schema",
        type=str,
        default="explorer_datasets",  # CHANGED default
        help="Schema name (default: explorer_datasets)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force regeneration even if metadata already exists",
    )
    parser.add_argument(
        "--list-catalogs",
        action="store_true",
        help="List all available catalogs and exit",
    )
    parser.add_argument(
        "--list-schemas",
        action="store_true",
        help="List all schemas in catalog and exit",
    )
    parser.add_argument(
        "--list-tables",
        action="store_true",
        help="List all tables in catalog.schema and exit",
    )

    args = parser.parse_args()

    # List catalogs if requested
    if args.list_catalogs:
        try:
            catalogs = starburst_service.get_catalogs()
            logger.info(f"Found {len(catalogs)} catalogs:")
            for catalog in catalogs:
                print(f"  - {catalog}")
            return 0
        except Exception as e:
            logger.error(f"Failed to list catalogs: {e}")
            return 1

    # List schemas if requested
    if args.list_schemas:
        try:
            schemas = starburst_service.get_schemas_in_catalog(args.catalog)
            logger.info(f"Found {len(schemas)} schemas in {args.catalog}:")
            for schema in schemas:
                print(f"  - {schema}")
            return 0
        except Exception as e:
            logger.error(f"Failed to list schemas: {e}")
            return 1

    # List tables if requested
    if args.list_tables:
        try:
            tables = starburst_service.get_tables_in_catalog(args.catalog, args.schema)
            logger.info(f"Found {len(tables)} tables in {args.catalog}.{args.schema}:")
            for table in tables:
                print(f"  - {table['name']}")
            return 0
        except Exception as e:
            logger.error(f"Failed to list tables: {e}")
            return 1

    logger.info("=" * 70)
    logger.info("METADATA EXPLORER - INITIAL SETUP")
    logger.info("=" * 70)
    logger.info(f"Catalog: {args.catalog}")
    logger.info(f"Schema: {args.schema}")
    logger.info("=" * 70)

    try:
        if args.table:
            # Generate for specific table
            logger.info(
                f"Generating metadata for table: {args.catalog}.{args.schema}.{args.table}"
            )
            logger.info(f"Force refresh: {args.force}")

            success = metadata_generator.generate_metadata_for_table(
                table_name=args.table,
                catalog=args.catalog,
                schema=args.schema,
                force_refresh=args.force,
            )

            if success:
                logger.info(f"✅ Successfully generated metadata for {args.table}")
                return 0
            else:
                logger.error(f"❌ Failed to generate metadata for {args.table}")
                return 1

        else:
            # Generate for all tables in catalog.schema
            try:
                all_tables_data = starburst_service.get_tables_in_catalog(
                    args.catalog, args.schema
                )
                all_tables = [t["name"] for t in all_tables_data]
            except Exception as e:
                logger.error(
                    f"Failed to get tables from {args.catalog}.{args.schema}: {e}"
                )
                return 1

            logger.info(
                f"Found {len(all_tables)} tables in {args.catalog}.{args.schema}"
            )
            logger.info(f"Force refresh: {args.force}")
            logger.info("")

            confirmation = input(
                f"Proceed with metadata generation for {len(all_tables)} tables? (yes/no): "
            )
            if confirmation.lower() not in ["yes", "y"]:
                logger.info("Operation cancelled by user")
                return 0

            logger.info("")
            logger.info("Starting metadata generation...")
            logger.info("")

            results = metadata_generator.generate_metadata_for_all_tables(
                table_names=all_tables,
                catalog=args.catalog,
                schema=args.schema,
                force_refresh=args.force,
            )

            # Show final summary
            success_count = sum(1 for v in results.values() if v)
            failed_tables = [table for table, success in results.items() if not success]

            logger.info("")
            logger.info("=" * 70)
            logger.info("FINAL SUMMARY")
            logger.info("=" * 70)
            logger.info(f"Catalog.Schema: {args.catalog}.{args.schema}")
            logger.info(f"Total tables: {len(results)}")
            logger.info(f"Successful: {success_count}")
            logger.info(f"Failed: {len(results) - success_count}")

            if failed_tables:
                logger.warning("")
                logger.warning(f"Failed tables ({len(failed_tables)}):")
                for table in failed_tables[:10]:  # Show first 10
                    logger.warning(f"  - {table}")
                if len(failed_tables) > 10:
                    logger.warning(f"  ... and {len(failed_tables) - 10} more")

            logger.info("=" * 70)

            return 0 if success_count == len(results) else 1

    except KeyboardInterrupt:
        logger.warning("\nOperation interrupted by user")
        return 130

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
