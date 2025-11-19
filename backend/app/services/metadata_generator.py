"""
Main metadata generation service - orchestrates all metadata generation tasks
"""

from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd

from app.config import settings
from app.models import ColumnMetadata, SchemaStatus, TableMetadata
from app.services.alias_generator import alias_generator
from app.services.column_type_detector import column_type_detector
from app.services.dynamodb import dynamodb_service
from app.services.geographic_detector import geographic_detector
from app.services.relationship_tasks import start_relationship_detection_task
from app.services.starburst import starburst_service
from app.utils.logger import app_logger as logger


class MetadataGenerator:
    """Service for generating complete metadata for tables"""

    def __init__(self):
        """Initialize metadata generator"""
        self.starburst = starburst_service
        self.dynamodb = dynamodb_service
        self.geo_detector = geographic_detector
        self.col_type_detector = column_type_detector
        self.alias_gen = alias_generator

    def generate_metadata_for_table(
        self,
        table_name: str,
        catalog: str = "here_explorer",
        schema: str = "explorer_datasets",
        force_refresh: bool = False,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> bool:
        """
        Generate complete metadata for a single table

        Args:
            table_name: Name of the table
            catalog: Catalog name (default: here_explorer)
            schema: Schema name (default: explorer_datasets)
            force_refresh: Force regeneration even if metadata exists

        Returns:
            True if successful, False otherwise
        """
        try:
            # CHANGED: Full 3-part key
            catalog_schema_table = f"{catalog}.{schema}.{table_name}"
            logger.info(f"Starting metadata generation for: {catalog_schema_table}")

            # Check if metadata already exists
            if not force_refresh:
                existing_metadata = self.dynamodb.get_table_metadata(
                    catalog_schema_table
                )
                if existing_metadata:
                    logger.info(
                        f"Metadata already exists for {catalog_schema_table}. Use force_refresh=True to regenerate."
                    )
                    return True

            # Step 1: Get schema from Starburst (always use live schema)
            logger.info(
                f"Fetching schema from Starburst for {catalog}.{schema}.{table_name}"
            )
            table_schema = self.starburst.get_table_schema_with_catalog(
                catalog, schema, table_name, username, password
            )

            if not table_schema:
                logger.error(
                    f"Could not get schema for {catalog}.{schema}.{table_name}"
                )
                return False

            logger.info(f"Schema loaded: {len(table_schema)} columns")

            # Step 2: Get row count
            row_count = self.starburst.get_row_count_with_catalog(
                catalog, schema, table_name, username, password
            )
            logger.info(f"Row count: {row_count}")

            # Step 3: Get column statistics
            stats = self.starburst.get_column_statistics_with_catalog(
                catalog, schema, table_name, table_schema, username, password
            )
            logger.info(f"Retrieved statistics for {len(stats)} columns")

            # Step 4: Get sample data
            sample_df = self.starburst.get_sample_data_with_catalog(
                catalog,
                schema,
                table_name,
                limit=1000,
                username=username,
                password=password,
            )

            # Check if sample data was retrieved
            if sample_df is None or sample_df.empty:
                logger.warning(
                    f"No sample data available for {catalog}.{schema}.{table_name}, continuing with empty samples"
                )
                sample_df = pd.DataFrame()

            logger.info(f"Retrieved sample data: {len(sample_df)} rows")

            # Step 5: Process each column
            for column_name, data_type in table_schema.items():
                logger.debug(f"Processing column: {column_name}")

                # Get statistics for this column
                col_stats = stats.get(column_name, {})
                cardinality = col_stats.get("cardinality", 0)

                # Get sample values from DataFrame
                if column_name in sample_df.columns:
                    sample_values = sample_df[column_name].dropna().head(10).tolist()
                else:
                    sample_values = []

                # DETECT COLUMN TYPE (dimension/measure/identifier/timestamp/detail)
                column_type = self.col_type_detector.detect_column_type(
                    column_name=column_name,
                    data_type=data_type,
                    cardinality=cardinality,
                    row_count=row_count,
                )

                # DETECT SEMANTIC TYPE (country/state/city/latitude/longitude or None)
                semantic_type = self.geo_detector.detect_semantic_type(
                    column_name=column_name,
                    data_type=data_type,
                    sample_values=sample_values,
                    min_value=col_stats.get("min_value"),
                    max_value=col_stats.get("max_value"),
                    cardinality=cardinality,
                )

                # Generate table context
                table_context = (
                    f"contains {row_count:,} rows of {table_name.replace('_', ' ')}"
                )

                # Generate aliases
                aliases = self.alias_gen.generate_aliases(
                    column_name=column_name,
                    data_type=data_type,
                    sample_values=sample_values[:10] if sample_values else None,
                    tags=[semantic_type] if semantic_type else [],
                    table_context=table_context,
                )

                # Generate description
                description = self.alias_gen.generate_description(
                    column_name=column_name,
                    data_type=data_type,
                    sample_values=sample_values[:10] if sample_values else None,
                    tags=[semantic_type] if semantic_type else [],
                    min_value=col_stats.get("min_value"),
                    max_value=col_stats.get("max_value"),
                    cardinality=cardinality,
                    table_context=table_context,
                )

                # Create ColumnMetadata object
                column_metadata = ColumnMetadata(
                    catalog_schema_table=catalog_schema_table,  # CHANGED
                    column_name=column_name,
                    data_type=data_type,
                    column_type=column_type,
                    semantic_type=semantic_type,
                    aliases=aliases,
                    description=description,
                    min_value=col_stats.get("min_value"),
                    max_value=col_stats.get("max_value"),
                    avg_value=col_stats.get("avg_value"),
                    cardinality=cardinality,
                    null_count=col_stats.get("null_count", 0),
                    null_percentage=col_stats.get("null_percentage", 0.0),
                    sample_values=sample_values,
                )

                # Save column metadata to DynamoDB
                logger.info(f"About to save column {column_name}")
                self.dynamodb.save_column_metadata(column_metadata)
                logger.info(f"Saved column {column_name}")

            # Step 6: Save table-level metadata
            table_metadata = TableMetadata(
                catalog_schema_table=catalog_schema_table,  # CHANGED
                last_updated=datetime.now(),
                row_count=row_count,
                column_count=len(table_schema),
                schema_status=SchemaStatus.CURRENT,
                schema_change_detected_at=None,
                schema_changes=None,
            )

            self.dynamodb.save_table_metadata(table_metadata)

            logger.info(
                f"✅ Successfully generated metadata for: {catalog_schema_table}"
            )

            # Start relationship detection in background
            table_identifier = f"{catalog}#{schema}#{table_name}"
            start_relationship_detection_task(
                table_identifier=table_identifier,
                catalog=catalog,
                schema=schema,
                table_name=table_name,
            )

            return True

        except Exception as e:
            logger.error(
                f"❌ Failed to generate metadata for {catalog}.{schema}.{table_name}: {e}",
                exc_info=True,
            )
            return False

    def generate_metadata_for_all_tables(
        self,
        table_names: List[str] = None,
        catalog: str = "here_explorer",
        schema: str = "explorer_datasets",
        force_refresh: bool = False,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> Dict[str, bool]:
        """
        Generate metadata for multiple tables

        Args:
            table_names: List of table names
            catalog: Catalog name
            schema: Schema name
            force_refresh: Force regeneration even if metadata exists

        Returns:
            Dictionary mapping table names to success status
        """
        if table_names is None:
            logger.error("No table names provided")
            return {}

        logger.info(f"Processing {len(table_names)} tables from {catalog}.{schema}")

        results = {}

        for i, table_name in enumerate(table_names, 1):
            logger.info(f"[{i}/{len(table_names)}] Processing table: {table_name}")

            try:
                success = self.generate_metadata_for_table(
                    table_name=table_name,
                    catalog=catalog,
                    schema=schema,
                    force_refresh=force_refresh,
                    username=username,
                    password=password,
                )
                results[table_name] = success

                if success:
                    logger.info(f"✅ [{i}/{len(table_names)}] Success: {table_name}")
                else:
                    logger.warning(f"⚠️ [{i}/{len(table_names)}] Failed: {table_name}")

            except Exception as e:
                logger.error(
                    f"❌ [{i}/{len(table_names)}] Error processing {table_name}: {e}"
                )
                results[table_name] = False

        # Summary
        success_count = sum(1 for v in results.values() if v)
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Metadata generation complete:")
        logger.info(f"  Total tables: {len(results)}")
        logger.info(f"  Successful: {success_count}")
        logger.info(f"  Failed: {len(results) - success_count}")
        logger.info(f"{'=' * 60}\n")

        return results

    def refresh_metadata_for_table(
        self,
        catalog_schema_table: str,
        catalog: str = "here_explorer",
        schema: str = "explorer_datasets",
        username: Optional[str] = None,
        password: Optional[str] = None,
    ) -> bool:
        """
        Refresh metadata for a table (regenerate)

        Args:
            catalog_schema_table: Full catalog.schema.table identifier
            catalog: Catalog name
            schema: Schema name

        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract table name from catalog_schema_table (last part)
            parts = catalog_schema_table.split(".")
            table_name = parts[-1] if len(parts) > 0 else catalog_schema_table

            logger.info(f"Refreshing metadata for: {catalog_schema_table}")

            # Delete existing column metadata
            self.dynamodb.delete_all_columns_for_table(catalog_schema_table)

            # Regenerate metadata
            success = self.generate_metadata_for_table(
                table_name=table_name,
                catalog=catalog,
                schema=schema,
                force_refresh=True,
                username=username,
                password=password,
            )

            if success:
                logger.info(
                    f" Successfully refreshed metadata for {catalog_schema_table}"
                )

            return success

        except Exception as e:
            logger.error(f" Failed to refresh metadata for {catalog_schema_table}: {e}")
            return False


# Global metadata generator instance
metadata_generator = MetadataGenerator()
