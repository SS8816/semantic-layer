# """
# Background task for detecting relationships after metadata generation
# FIXED version with better error handling
# """

# import asyncio
# from typing import Any, Dict, List

# from app.services.dynamodb import dynamodb_service
# from app.services.dynamodb_relationships import relationships_service
# from app.services.relationship_detector import relationship_detector
# from app.utils.logger import app_logger as logger


# async def detect_and_store_relationships(
#     table_identifier: str, catalog: str, schema: str, table_name: str
# ) -> Dict[str, Any]:
#     """
#     Background task to detect relationships and store in DynamoDB
#     """
#     try:
#         logger.info(f"🔍 Starting relationship detection for {table_identifier}")

#         # Give DynamoDB a moment to propagate the metadata
#         await asyncio.sleep(3)

#         # Step 1: Get metadata for the new table (ALL columns)
#         full_table_name = f"{catalog}.{schema}.{table_name}"
#         new_table_metadata_raw = dynamodb_service.get_all_columns_for_table(
#             full_table_name
#         )

#         if not new_table_metadata_raw:
#             logger.warning(f"No metadata found for {full_table_name}")
#             return {
#                 "status": "skipped",
#                 "reason": "no_metadata",
#                 "relationships_found": 0,
#             }

#         # Convert to dictionaries
#         new_table_metadata = []
#         for col in new_table_metadata_raw:
#             if hasattr(col, "dict"):
#                 new_table_metadata.append(col.dict())
#             elif isinstance(col, dict):
#                 new_table_metadata.append(col)

#         logger.info(f"Loaded metadata for new table: {len(new_table_metadata)} columns")

#         # Step 2: Get all existing tables from DynamoDB
#         all_table_identifiers = dynamodb_service.get_all_table_identifiers()

#         # Exclude the new table itself
#         existing_table_identifiers = [
#             tid for tid in all_table_identifiers if tid != full_table_name
#         ]

#         if not existing_table_identifiers:
#             logger.info(
#                 f"No existing tables to compare against, skipping relationship detection"
#             )
#             return {
#                 "status": "skipped",
#                 "reason": "no_existing_tables",
#                 "relationships_found": 0,
#             }

#         logger.info(
#             f"Found {len(existing_table_identifiers)} existing tables to compare"
#         )

#         # Step 3: Load metadata for all existing tables
#         existing_tables_metadata = {}

#         for existing_table_id in existing_table_identifiers:
#             try:
#                 columns = dynamodb_service.get_all_columns_for_table(existing_table_id)
#                 if columns and len(columns) > 0:
#                     # Convert ColumnMetadata objects to dictionaries
#                     columns_as_dicts = []
#                     for col in columns:
#                         if hasattr(col, "dict"):
#                             # Pydantic model - convert to dict
#                             columns_as_dicts.append(col.dict())
#                         elif isinstance(col, dict):
#                             # Already a dict
#                             columns_as_dicts.append(col)
#                         else:
#                             logger.warning(f"Unknown column type: {type(col)}")
#                             continue

#                     existing_tables_metadata[existing_table_id] = columns_as_dicts
#                     logger.debug(
#                         f"  Loaded {len(columns)} columns from {existing_table_id}"
#                     )
#                 else:
#                     logger.debug(f"  Skipping {existing_table_id} - no columns found")
#             except Exception as e:
#                 logger.warning(f"  Failed to load columns for {existing_table_id}: {e}")
#                 continue

#         if not existing_tables_metadata:
#             logger.warning("No existing tables with valid metadata found")
#             return {
#                 "status": "skipped",
#                 "reason": "no_valid_existing_tables",
#                 "relationships_found": 0,
#             }

#         logger.info(
#             f"Loaded metadata for {len(existing_tables_metadata)} existing tables"
#         )

#         # Step 4: Detect relationships using GPT-4o
#         try:
#             relationships = await relationship_detector.find_relationships(
#                 new_table_name=full_table_name,
#                 new_table_metadata=new_table_metadata,
#                 existing_tables_metadata=existing_tables_metadata,
#                 confidence_threshold=0.6,
#             )
#         except Exception as e:
#             logger.error(f"Failed during relationship detection: {e}", exc_info=True)
#             return {
#                 "status": "error",
#                 "table": full_table_name,
#                 "error": f"Relationship detection failed: {str(e)}",
#                 "relationships_found": 0,
#             }

#         # Step 5: Store relationships in DynamoDB
#         if relationships and len(relationships) > 0:
#             try:
#                 stored_count = relationships_service.store_relationships_batch(
#                     relationships
#                 )
#                 logger.info(
#                     f"✅ Stored {stored_count} relationships for {full_table_name}"
#                 )

#                 # Log top relationships
#                 top_relationships = sorted(
#                     relationships, key=lambda x: x["confidence"], reverse=True
#                 )[:5]
#                 for rel in top_relationships:
#                     subtype_str = (
#                         f" ({rel.get('relationship_subtype', '')})"
#                         if rel.get("relationship_subtype")
#                         else ""
#                     )
#                     logger.info(
#                         f"  📊 {rel['source_column']} → {rel['target_table']}.{rel['target_column']} "
#                         f"({rel['relationship_type']}{subtype_str}, {rel['confidence']:.2f})"
#                     )
#             except Exception as e:
#                 logger.error(f"Failed to store relationships: {e}", exc_info=True)
#                 return {
#                     "status": "error",
#                     "table": full_table_name,
#                     "error": f"Failed to store relationships: {str(e)}",
#                     "relationships_found": len(relationships),
#                 }
#         else:
#             logger.info(f"No high-confidence relationships found for {full_table_name}")

#         return {
#             "status": "success",
#             "table": full_table_name,
#             "relationships_found": len(relationships) if relationships else 0,
#             "relationships": relationships if relationships else [],
#         }

#     except Exception as e:
#         logger.error(
#             f"❌ Failed to detect relationships for {table_identifier}: {e}",
#             exc_info=True,
#         )
#         return {
#             "status": "error",
#             "table": f"{catalog}.{schema}.{table_name}",
#             "error": str(e),
#             "relationships_found": 0,
#         }


# def start_relationship_detection_task(
#     table_identifier: str, catalog: str, schema: str, table_name: str
# ):
#     """
#     Start relationship detection as a background task (non-blocking)
#     """
#     import asyncio

#     try:
#         # Get the running event loop (FastAPI's loop)
#         try:
#             loop = asyncio.get_running_loop()

#             # Create background task in FastAPI's event loop
#             loop.create_task(
#                 detect_and_store_relationships(
#                     table_identifier, catalog, schema, table_name
#                 )
#             )

#             logger.info(
#                 f"🚀 Started background relationship detection task for {table_identifier}"
#             )

#         except RuntimeError:
#             # No event loop running - create one
#             logger.warning("No running event loop, creating new one")
#             asyncio.run(
#                 detect_and_store_relationships(
#                     table_identifier, catalog, schema, table_name
#                 )
#             )

#     except Exception as e:
#         logger.error(f"Failed to start relationship detection task: {e}", exc_info=True)


"""
Background task for detecting relationships after metadata generation
FIXED version with better error handling
"""

import asyncio
from typing import Any, Dict, List

from app.models import RelationshipDetectionStatus
from app.services.dynamodb import dynamodb_service
from app.services.dynamodb_relationships import relationships_service
from app.services.relationship_detector import relationship_detector
from app.utils.logger import app_logger as logger


async def detect_and_store_relationships(
    table_identifier: str, catalog: str, schema: str, table_name: str
) -> Dict[str, Any]:
    """
    Background task to detect relationships and store in DynamoDB
    """
    try:
        logger.info(f"🔍 Starting relationship detection for {table_identifier}")

        # Step 0: Update status to IN_PROGRESS
        full_table_name = f"{catalog}.{schema}.{table_name}"
        dynamodb_service.update_relationship_detection_status(
            full_table_name, RelationshipDetectionStatus.IN_PROGRESS
        )

        # Give DynamoDB a moment to propagate the metadata
        await asyncio.sleep(3)

        # Step 1: Get metadata for the new table (ALL columns)
        new_table_metadata_raw = dynamodb_service.get_all_columns_for_table(
            full_table_name
        )

        if not new_table_metadata_raw:
            logger.warning(
                f"No metadata found for {full_table_name}, skipping relationship detection"
            )
            # Reset to NOT_STARTED since we couldn't even begin
            dynamodb_service.update_relationship_detection_status(
                full_table_name, RelationshipDetectionStatus.NOT_STARTED
            )
            return {
                "status": "skipped",
                "reason": "no_metadata",
                "relationships_found": 0,
            }

        # Convert ColumnMetadata Pydantic models to dictionaries
        new_table_metadata = []
        for col in new_table_metadata_raw:
            if hasattr(col, "dict"):
                # Pydantic model - convert to dict
                new_table_metadata.append(col.dict())
            elif isinstance(col, dict):
                # Already a dict
                new_table_metadata.append(col)
            else:
                logger.warning(f"Unknown column type for new table: {type(col)}")

        logger.info(f"Loaded metadata for new table: {len(new_table_metadata)} columns")

        # Step 2: Get all existing tables from DynamoDB
        all_table_identifiers = dynamodb_service.get_all_table_identifiers()

        # Exclude the new table itself
        existing_table_identifiers = [
            tid for tid in all_table_identifiers if tid != full_table_name
        ]

        if not existing_table_identifiers:
            logger.info(
                f"No existing tables to compare against, skipping relationship detection"
            )
            return {
                "status": "skipped",
                "reason": "no_existing_tables",
                "relationships_found": 0,
            }

        logger.info(
            f"Found {len(existing_table_identifiers)} existing tables to compare"
        )

        # Step 3: Load metadata for all existing tables
        existing_tables_metadata = {}

        for existing_table_id in existing_table_identifiers:
            try:
                columns = dynamodb_service.get_all_columns_for_table(existing_table_id)
                if columns and len(columns) > 0:
                    # Convert ColumnMetadata Pydantic models to dictionaries
                    columns_as_dicts = []
                    for col in columns:
                        if hasattr(col, "dict"):
                            # Pydantic model - convert to dict
                            columns_as_dicts.append(col.dict())
                        elif isinstance(col, dict):
                            # Already a dict
                            columns_as_dicts.append(col)
                        else:
                            logger.warning(
                                f"Unknown column type for {existing_table_id}: {type(col)}"
                            )
                            continue

                    # Store with the table ID (already in catalog.schema.table format)
                    if columns_as_dicts:
                        existing_tables_metadata[existing_table_id] = columns_as_dicts
                        logger.debug(
                            f"  Loaded {len(columns_as_dicts)} columns from {existing_table_id}"
                        )
                    else:
                        logger.debug(
                            f"  Skipping {existing_table_id} - no valid columns after conversion"
                        )
                else:
                    logger.debug(f"  Skipping {existing_table_id} - no columns found")
            except Exception as e:
                logger.warning(f"  Failed to load columns for {existing_table_id}: {e}")
                continue

        if not existing_tables_metadata:
            logger.warning("No existing tables with valid metadata found")
            return {
                "status": "skipped",
                "reason": "no_valid_existing_tables",
                "relationships_found": 0,
            }

        logger.info(
            f"Loaded metadata for {len(existing_tables_metadata)} existing tables"
        )

        # Step 4: Detect relationships using GPT-4o
        try:
            relationships = await relationship_detector.find_relationships(
                new_table_name=full_table_name,
                new_table_metadata=new_table_metadata,
                existing_tables_metadata=existing_tables_metadata,
                confidence_threshold=0.6,
            )
        except Exception as e:
            logger.error(f"Failed during relationship detection: {e}", exc_info=True)
            return {
                "status": "error",
                "table": full_table_name,
                "error": f"Relationship detection failed: {str(e)}",
                "relationships_found": 0,
            }

        # Step 5: Store relationships in DynamoDB
        if relationships and len(relationships) > 0:
            try:
                stored_count = relationships_service.store_relationships_batch(
                    relationships
                )
                logger.info(
                    f"✅ Stored {stored_count} relationships for {full_table_name}"
                )

                # Log top relationships
                top_relationships = sorted(
                    relationships, key=lambda x: x["confidence"], reverse=True
                )[:5]
                for rel in top_relationships:
                    subtype_str = (
                        f" ({rel.get('relationship_subtype', '')})"
                        if rel.get("relationship_subtype")
                        else ""
                    )
                    logger.info(
                        f"   {rel['source_column']} → {rel['target_table']}.{rel['target_column']} "
                        f"({rel['relationship_type']}{subtype_str}, {rel['confidence']:.2f})"
                    )
            except Exception as e:
                logger.error(f"Failed to store relationships: {e}", exc_info=True)
                return {
                    "status": "error",
                    "table": full_table_name,
                    "error": f"Failed to store relationships: {str(e)}",
                    "relationships_found": len(relationships),
                }
        else:
            logger.info(f"No high-confidence relationships found for {full_table_name}")

        # Update status to COMPLETED
        dynamodb_service.update_relationship_detection_status(
            full_table_name, RelationshipDetectionStatus.COMPLETED
        )

        return {
            "status": "success",
            "table": full_table_name,
            "relationships_found": len(relationships) if relationships else 0,
            "relationships": relationships if relationships else [],
        }

    except Exception as e:
        logger.error(
            f"❌ Failed to detect relationships for {table_identifier}: {e}",
            exc_info=True,
        )

        # Update status to FAILED
        full_table_name = f"{catalog}.{schema}.{table_name}"
        dynamodb_service.update_relationship_detection_status(
            full_table_name, RelationshipDetectionStatus.FAILED
        )

        return {
            "status": "error",
            "table": full_table_name,
            "error": str(e),
            "relationships_found": 0,
        }


def start_relationship_detection_task(
    table_identifier: str, catalog: str, schema: str, table_name: str
):
    """
    Start relationship detection as a background task (non-blocking)
    """
    import asyncio

    try:
        # Get the running event loop (FastAPI's loop)
        try:
            loop = asyncio.get_running_loop()

            # Create background task in FastAPI's event loop
            loop.create_task(
                detect_and_store_relationships(
                    table_identifier, catalog, schema, table_name
                )
            )

            logger.info(
                f" Started background relationship detection task for {table_identifier}"
            )

        except RuntimeError:
            # No event loop running - create one
            logger.warning("No running event loop, creating new one")
            asyncio.run(
                detect_and_store_relationships(
                    table_identifier, catalog, schema, table_name
                )
            )

    except Exception as e:
        logger.error(f"Failed to start relationship detection task: {e}", exc_info=True)
