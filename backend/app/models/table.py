"""
Pydantic models for table metadata
"""
from pydantic import BaseModel, Field
from typing import Dict, Optional, List
from datetime import datetime
from enum import Enum


class SchemaStatus(str, Enum):
    """Schema status enum"""
    CURRENT = "CURRENT"
    SCHEMA_CHANGED = "SCHEMA_CHANGED"


class RelationshipDetectionStatus(str, Enum):
    """Relationship detection status enum"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class SchemaChange(BaseModel):
    """Schema change details"""
    new_columns: List[str] = Field(default_factory=list)
    removed_columns: List[str] = Field(default_factory=list)
    type_changes: List[Dict[str, str]] = Field(default_factory=list)


class TableMetadata(BaseModel):
    """Table metadata model"""
    catalog_schema_table: str  # CHANGED: now catalog.schema.table
    last_updated: datetime
    row_count: int = 0
    column_count: int = 0
    schema_status: SchemaStatus = SchemaStatus.CURRENT
    schema_change_detected_at: Optional[datetime] = None
    schema_changes: Optional[SchemaChange] = None
    relationship_detection_status: RelationshipDetectionStatus = RelationshipDetectionStatus.NOT_STARTED
    
    class Config:
        json_schema_extra = {
            "example": {
                "catalog_schema_table": "here_explorer.explorer_datasets.navigable_road_attributes_2024",
                "last_updated": "2025-10-29T10:30:00Z",
                "row_count": 1500000,
                "column_count": 25,
                "schema_status": "CURRENT",
                "schema_change_detected_at": None,
                "schema_changes": None
            }
        }


class TableSummary(BaseModel):
    """Summary information about a table"""
    name: str  # Just the table name for display
    catalog_schema_table: str  # Full catalog.schema.table identifier
    schema_status: SchemaStatus
    last_updated: datetime
    row_count: int
    column_count: int = 0
    relationship_detection_status: RelationshipDetectionStatus = RelationshipDetectionStatus.NOT_STARTED
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "navigable_road_attributes_2024",
                "catalog_schema_table": "here_explorer.explorer_datasets.navigable_road_attributes_2024",
                "schema_status": "CURRENT",
                "last_updated": "2025-10-29T10:30:00Z",
                "row_count": 1500000,
                "column_count": 25
            }
        }


class TableWithColumns(BaseModel):
    """Complete table metadata with all column metadata"""
    catalog_schema_table: str  # CHANGED
    last_updated: datetime
    row_count: int
    column_count: int = 0
    schema_status: SchemaStatus
    schema_changes: Optional[SchemaChange] = None
    relationship_detection_status: RelationshipDetectionStatus = RelationshipDetectionStatus.NOT_STARTED
    columns: Dict[str, dict]  # column_name -> column metadata dict
    
    class Config:
        json_schema_extra = {
            "example": {
                "catalog_schema_table": "here_explorer.explorer_datasets.navigable_road_attributes_2024",
                "last_updated": "2025-10-29T10:30:00Z",
                "row_count": 1500000,
                "column_count": 25,
                "schema_status": "CURRENT",
                "schema_changes": None,
                "columns": {
                    "road_id": {
                        "data_type": "bigint",
                        "column_type": "identifier",
                        "semantic_type": None,
                        "aliases": ["Road ID"],
                        "description": "Unique identifier",
                        "min_value": 1,
                        "max_value": 5000000
                    }
                }
            }
        }