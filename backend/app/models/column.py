"""
Pydantic models for column metadata
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Any
from datetime import datetime


class ColumnMetadata(BaseModel):
    """Column metadata model"""
    catalog_schema_table: str  # CHANGED: now catalog.schema.table
    column_name: str
    data_type: str
    column_type: str
    semantic_type: Optional[str] = None
    aliases: List[str] = Field(default_factory=list)
    description: str = ""
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    avg_value: Optional[float] = None
    cardinality: int = 0
    null_count: int = 0
    null_percentage: float = 0.0
    sample_values: List[Any] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "catalog_schema_table": "here_explorer.explorer_datasets.navigable_road_attributes_2024",
                "column_name": "road_id",
                "data_type": "bigint",
                "column_type": "identifier",
                "semantic_type": None,
                "aliases": ["Road ID", "Road Identifier"],
                "description": "Unique identifier for each road segment",
                "min_value": 1,
                "max_value": 5000000,
                "avg_value": 2500000.5,
                "cardinality": 5000000,
                "null_count": 0,
                "null_percentage": 0.0,
                "sample_values": [1, 2, 3, 4, 5]
            }
        }


class ColumnMetadataCreate(BaseModel):
    """Model for creating column metadata"""
    column_name: str
    data_type: str
    column_type: str
    semantic_type: Optional[str] = None


class ColumnMetadataUpdate(BaseModel):
    """Model for updating column metadata"""
    aliases: Optional[List[str]] = None
    description: Optional[str] = None
    column_type: Optional[str] = None  
    semantic_type: Optional[str] = None