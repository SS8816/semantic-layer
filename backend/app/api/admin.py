# """
# Admin API endpoints for metadata generation and management
# """
# from fastapi import APIRouter, HTTPException, BackgroundTasks, Body, Query
# from typing import Optional
# import uuid
# from app.models import (
#     GenerateMetadataRequest, GenerateMetadataResponse, ErrorResponse
# )
# from app.services.metadata_generator import metadata_generator
# from app.services.starburst import starburst_service
# from app.utils.logger import app_logger as logger

# router = APIRouter(prefix="/api/admin", tags=["admin"])


# # In-memory task tracking (for production, use Redis or database)
# tasks = {}


# def run_metadata_generation(
#     task_id: str,
#     table_name: Optional[str],
#     catalog: str,
#     schema: str,
#     force_refresh: bool
# ):
#     """
#     Background task to run metadata generation

#     Args:
#         task_id: Unique task identifier
#         table_name: Name of specific table or None for all tables
#         catalog: Catalog name
#         schema: Schema name
#         force_refresh: Force regeneration even if metadata exists
#     """
#     try:
#         logger.info(f"[Task {task_id}] Starting metadata generation for {catalog}.{schema}")
#         tasks[task_id] = {"status": "running", "progress": 0}

#         if table_name:
#             # Generate for single table
#             success = metadata_generator.generate_metadata_for_table(
#                 table_name=table_name,
#                 catalog=catalog,
#                 schema=schema,
#                 force_refresh=force_refresh
#             )

#             if success:
#                 tasks[task_id] = {"status": "completed", "progress": 100}
#                 logger.info(f"[Task {task_id}] Completed successfully")
#             else:
#                 tasks[task_id] = {"status": "failed", "progress": 0, "error": "Generation failed"}
#                 logger.error(f"[Task {task_id}] Failed")

#         else:
#             # Generate for all tables in catalog.schema
#             try:
#                 tables_data = starburst_service.get_tables_in_catalog(catalog, schema)
#                 all_tables = [t['name'] for t in tables_data]
#             except Exception as e:
#                 tasks[task_id] = {"status": "failed", "progress": 0, "error": f"Failed to get tables: {str(e)}"}
#                 return

#             results = metadata_generator.generate_metadata_for_all_tables(
#                 table_names=all_tables,
#                 catalog=catalog,
#                 schema=schema,
#                 force_refresh=force_refresh
#             )

#             success_count = sum(1 for v in results.values() if v)
#             tasks[task_id] = {
#                 "status": "completed",
#                 "progress": 100,
#                 "total": len(results),
#                 "successful": success_count,
#                 "failed": len(results) - success_count
#             }
#             logger.info(f"[Task {task_id}] Completed: {success_count}/{len(results)} successful")

#     except Exception as e:
#         logger.error(f"[Task {task_id}] Error: {e}", exc_info=True)
#         tasks[task_id] = {"status": "failed", "progress": 0, "error": str(e)}


# @router.post(
#     "/generate-metadata",
#     response_model=GenerateMetadataResponse,
#     responses={500: {"model": ErrorResponse}}
# )
# async def generate_metadata(
#     background_tasks: BackgroundTasks,
#     request: GenerateMetadataRequest = Body(...),
#     catalog: str = Query(default="here_explorer", description="Catalog name"),  # CHANGED default
#     schema: str = Query(default="explorer_datasets", description="Schema name")  # CHANGED default
# ):
#     """
#     Generate metadata for tables (single table or all tables in catalog.schema)

#     This is a long-running operation that runs in the background.
#     Use the returned task_id to check progress.

#     Args:
#         background_tasks: FastAPI background tasks
#         request: GenerateMetadataRequest specifying table and options
#         catalog: Catalog name (default: here_explorer)
#         schema: Schema name (default: explorer_datasets)

#     Returns:
#         GenerateMetadataResponse with task ID for tracking
#     """
#     try:
#         # Generate unique task ID
#         task_id = str(uuid.uuid4())

#         if request.table_name:
#             logger.info(f"Queuing metadata generation for {catalog}.{schema}.{request.table_name}")
#             message = f"Metadata generation started for table '{request.table_name}'"
#             tables_to_process = 1
#         else:
#             try:
#                 tables_data = starburst_service.get_tables_in_catalog(catalog, schema)
#                 table_count = len(tables_data)
#             except Exception as e:
#                 raise HTTPException(status_code=500, detail=f"Failed to get tables: {str(e)}")

#             logger.info(f"Queuing metadata generation for all {table_count} tables in {catalog}.{schema}")
#             message = f"Metadata generation started for {table_count} tables in {catalog}.{schema}"
#             tables_to_process = table_count

#         # Add to background tasks
#         background_tasks.add_task(
#             run_metadata_generation,
#             task_id=task_id,
#             table_name=request.table_name,
#             catalog=catalog,
#             schema=schema,
#             force_refresh=request.force_refresh
#         )

#         # Initialize task status
#         tasks[task_id] = {"status": "queued", "progress": 0}

#         return GenerateMetadataResponse(
#             status="started",
#             message=message,
#             task_id=task_id,
#             tables_to_process=tables_to_process
#         )

#     except Exception as e:
#         logger.error(f"Error queuing metadata generation: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# @router.get(
#     "/task-status/{task_id}",
#     responses={404: {"model": ErrorResponse}}
# )
# async def get_task_status(task_id: str):
#     """
#     Get status of a metadata generation task

#     Args:
#         task_id: Task identifier returned from generate-metadata endpoint

#     Returns:
#         Task status information
#     """
#     if task_id not in tasks:
#         raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

#     return tasks[task_id]

"""
Admin API endpoints for metadata generation and management
"""

import uuid
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Body, HTTPException, Query, Request

from app.models import ErrorResponse, GenerateMetadataRequest, GenerateMetadataResponse
from app.services.metadata_generator import metadata_generator
from app.services.starburst import starburst_service
from app.utils.logger import app_logger as logger

router = APIRouter(prefix="/api/admin", tags=["admin"])


# In-memory task tracking (for production, use Redis or database)
tasks = {}


def run_metadata_generation(
    task_id: str,
    table_name: Optional[str],
    catalog: str,
    schema: str,
    force_refresh: bool,
    username: Optional[str] = None,
    password: Optional[str] = None,
):
    """
    Background task to run metadata generation

    Args:
        task_id: Unique task identifier
        table_name: Name of specific table or None for all tables
        catalog: Catalog name
        schema: Schema name
        force_refresh: Force regeneration even if metadata exists
        username/password: Optional credentials from request.state (so background trino calls run as the user)
    """
    try:
        logger.info(
            f"[Task {task_id}] Starting metadata generation for {catalog}.{schema} (user={username})"
        )
        tasks[task_id] = {"status": "running", "progress": 0}

        if table_name:
            # Generate for single table
            success = metadata_generator.generate_metadata_for_table(
                table_name=table_name,
                catalog=catalog,
                schema=schema,
                force_refresh=force_refresh,
            )

            if success:
                tasks[task_id] = {"status": "completed", "progress": 100}
                logger.info(f"[Task {task_id}] Completed successfully")
            else:
                tasks[task_id] = {
                    "status": "failed",
                    "progress": 0,
                    "error": "Generation failed",
                }
                logger.error(f"[Task {task_id}] Failed")

        else:
            # Generate for all tables in catalog.schema
            try:
                # Pass username/password so Starburst calls run as the logged-in user
                tables_data = starburst_service.get_tables_in_catalog(
                    catalog, schema, username=username, password=password
                )
                all_tables = [t["name"] for t in tables_data]
            except Exception as e:
                tasks[task_id] = {
                    "status": "failed",
                    "progress": 0,
                    "error": f"Failed to get tables: {str(e)}",
                }
                logger.error(
                    f"[Task {task_id}] Failed to list tables: {e}", exc_info=True
                )
                return

            results = metadata_generator.generate_metadata_for_all_tables(
                table_names=all_tables,
                catalog=catalog,
                schema=schema,
                force_refresh=force_refresh,
            )

            success_count = sum(1 for v in results.values() if v)
            tasks[task_id] = {
                "status": "completed",
                "progress": 100,
                "total": len(results),
                "successful": success_count,
                "failed": len(results) - success_count,
            }
            logger.info(
                f"[Task {task_id}] Completed: {success_count}/{len(results)} successful"
            )

    except Exception as e:
        logger.error(f"[Task {task_id}] Error: {e}", exc_info=True)
        tasks[task_id] = {"status": "failed", "progress": 0, "error": str(e)}


@router.post(
    "/generate-metadata",
    response_model=GenerateMetadataResponse,
    responses={500: {"model": ErrorResponse}},
)
async def generate_metadata(
    background_tasks: BackgroundTasks,
    request_body: GenerateMetadataRequest = Body(...),
    request: Request = None,
    catalog: str = Query(
        default="here_explorer", description="Catalog name"
    ),  # CHANGED default
    schema: str = Query(
        default="explorer_datasets", description="Schema name"
    ),  # CHANGED default
):
    """
    Generate metadata for tables (single table or all tables in catalog.schema)

    This is a long-running operation that runs in the background.
    Use the returned task_id to check progress.
    """
    try:
        # Extract credentials injected by middleware
        username = getattr(request.state, "username", None) if request else None
        password = getattr(request.state, "password", None) if request else None

        # Generate unique task ID
        task_id = str(uuid.uuid4())

        if request_body.table_name:
            logger.info(
                f"Queuing metadata generation for {catalog}.{schema}.{request_body.table_name} (user={username})"
            )
            message = (
                f"Metadata generation started for table '{request_body.table_name}'"
            )
            tables_to_process = 1
        else:
            try:
                # Pass credentials so Starburst lists using the logged-in user
                tables_data = starburst_service.get_tables_in_catalog(
                    catalog, schema, username=username, password=password
                )
                table_count = len(tables_data)
            except Exception as e:
                logger.error(
                    f"Failed to list tables for {catalog}.{schema} (user={username}): {e}",
                    exc_info=True,
                )
                raise HTTPException(
                    status_code=500, detail=f"Failed to get tables: {str(e)}"
                )

            logger.info(
                f"Queuing metadata generation for all {table_count} tables in {catalog}.{schema} (user={username})"
            )
            message = f"Metadata generation started for {table_count} tables in {catalog}.{schema}"
            tables_to_process = table_count

        # Add to background tasks and pass username/password so the background job runs as the user
        background_tasks.add_task(
            run_metadata_generation,
            task_id=task_id,
            table_name=request_body.table_name,
            catalog=catalog,
            schema=schema,
            force_refresh=request_body.force_refresh,
            username=username,
            password=password,
        )

        # Initialize task status
        tasks[task_id] = {"status": "queued", "progress": 0}

        return GenerateMetadataResponse(
            status="started",
            message=message,
            task_id=task_id,
            tables_to_process=tables_to_process,
        )

    except Exception as e:
        logger.error(f"Error queuing metadata generation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/task-status/{task_id}", responses={404: {"model": ErrorResponse}})
async def get_task_status(task_id: str):
    """
    Get status of a metadata generation task
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    return tasks[task_id]
