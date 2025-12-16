"""
API request and response models
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Any
from app.models.table import TableSummary


class TablesResponse(BaseModel):
    """Response for GET /api/tables"""
    tables: List[TableSummary]
    total_count: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "tables": [
                    {
                        "name": "navigable_road_attributes_2024",
                        "schema_status": "CURRENT",
                        "last_updated": "2025-10-29T10:30:00Z",
                        "row_count": 1500000
                    }
                ],
                "total_count": 232
            }
        }


class TableDataResponse(BaseModel):
    """Response for GET /api/table-data/{table_name}"""
    table_name: str
    columns: List[str]
    data: List[List[Any]]
    row_count: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "table_name": "navigable_road_attributes_2024",
                "columns": ["road_id", "road_name", "country"],
                "data": [
                    [1, "Main Street", "USA"],
                    [2, "Highway 101", "USA"]
                ],
                "row_count": 2
            }
        }


class GenerateMetadataRequest(BaseModel):
    """Request for POST /api/admin/generate-metadata"""
    table_name: Optional[str] = None
    force_refresh: bool = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "table_name": "navigable_road_attributes_2024",
                "force_refresh": False
            }
        }


class GenerateMetadataResponse(BaseModel):
    """Response for POST /api/admin/generate-metadata"""
    status: str
    message: str
    task_id: Optional[str] = None
    tables_to_process: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "started",
                "message": "Metadata generation started for 232 tables",
                "task_id": "abc-123-def",
                "tables_to_process": 232
            }
        }


class RefreshMetadataResponse(BaseModel):
    """Response for POST /api/refresh-metadata/{table_name}"""
    status: str
    table_name: str
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "table_name": "navigable_road_attributes_2024",
                "message": "Metadata refreshed successfully"
            }
        }


class UpdateAliasRequest(BaseModel):
    """Request for PATCH /api/column/{table_name}/{column_name}/alias"""
    aliases: List[str] = Field(..., min_length=1)
    
    class Config:
        json_schema_extra = {
            "example": {
                "aliases": ["Road ID", "Route Identifier", "Street ID"]
            }
        }


class UpdateAliasResponse(BaseModel):
    """Response for PATCH /api/column/{table_name}/{column_name}/alias"""
    status: str
    table_name: str
    column_name: str
    aliases: List[str]
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "table_name": "navigable_road_attributes_2024",
                "column_name": "road_id",
                "aliases": ["Road ID", "Route Identifier", "Street ID"]
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    detail: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Table not found",
                "detail": "Table 'invalid_table' does not exist"
            }
        }


class UpdateColumnMetadataRequest(BaseModel):
    """Request for PATCH /api/column/{catalog_table}/{column_name}/metadata"""
    aliases: Optional[List[str]] = None
    description: Optional[str] = None
    column_type: Optional[str] = None
    semantic_type: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "aliases": ["Road ID", "Route Identifier"],
                "description": "Unique identifier for each road segment",
                "column_type": "identifier",
                "semantic_type": None
            }
        }


class UpdateColumnMetadataResponse(BaseModel):
    """Response for PATCH /api/column/{catalog_table}/{column_name}/metadata"""
    status: str
    catalog_table: str
    column_name: str
    updated_fields: List[str]

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "catalog_table": "explorer_datasets.navigable_road_attributes_2024",
                "column_name": "road_id",
                "updated_fields": ["aliases", "description"]
            }
        }


class UpdateTableConfigRequest(BaseModel):
    """Request for PATCH /api/table/{catalog}/{schema}/{table_name}/config"""
    search_mode: Optional[str] = Field(None, description="Search mode: 'analytics', 'datamining', or None")
    custom_instructions: Optional[str] = Field(None, description="Custom SQL examples and LLM usage hints")

    class Config:
        json_schema_extra = {
            "example": {
                "search_mode": "analytics",
                "custom_instructions": "Use this table for POI analysis. Always join with location_dim on location_id."
            }
        }


class UpdateTableConfigResponse(BaseModel):
    """Response for PATCH /api/table/{catalog}/{schema}/{table_name}/config"""
    status: str
    catalog_schema_table: str
    updated_fields: List[str]

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "catalog_schema_table": "here_explorer.explorer_datasets.navigable_road_attributes_2024",
                "updated_fields": ["search_mode", "custom_instructions"]
            }
        }


class CatalogsResponse(BaseModel):
    """Response for GET /api/catalogs"""
    catalogs: List[str]
    total_count: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "catalogs": ["explorer_datasets", "analytics", "raw_data"],
                "total_count": 3
            }
        }


class TablesInCatalogResponse(BaseModel):
    """Response for GET /api/catalogs/{catalog}/tables"""
    catalog: str
    schema: str
    tables: List[str]
    total_count: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "catalog": "explorer_datasets",
                "schema": "public",
                "tables": ["address_range_changes_apac", "navigable_road_attributes"],
                "total_count": 232
            }
        }