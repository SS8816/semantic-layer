"""
Models package exports
"""
from app.models.table import (
    TableMetadata,
    TableSummary,
    TableWithColumns,
    SchemaStatus,
    SchemaChange
)
from app.models.column import (
    ColumnMetadata,
    ColumnMetadataCreate,
    ColumnMetadataUpdate
)
from app.models.api import (
    TablesResponse,
    TableDataResponse,
    GenerateMetadataRequest,
    GenerateMetadataResponse,
    RefreshMetadataResponse,
    UpdateAliasRequest,
    UpdateAliasResponse,
    UpdateColumnMetadataRequest,  # NEW - ADD THIS
    UpdateColumnMetadataResponse,  # NEW - ADD THIS
    CatalogsResponse,  # NEW - ADD THIS
    TablesInCatalogResponse,  # NEW - ADD THIS
    ErrorResponse
)

__all__ = [
    # Table models
    "TableMetadata",
    "TableSummary",
    "TableWithColumns",
    "SchemaStatus",
    "SchemaChange",
    # Column models
    "ColumnMetadata",
    "ColumnMetadataCreate",
    "ColumnMetadataUpdate",
    # API models
    "TablesResponse",
    "TableDataResponse",
    "GenerateMetadataRequest",
    "GenerateMetadataResponse",
    "RefreshMetadataResponse",
    "UpdateAliasRequest",
    "UpdateAliasResponse",
    "UpdateColumnMetadataRequest",  # NEW
    "UpdateColumnMetadataResponse",  # NEW
    "CatalogsResponse",  # NEW
    "TablesInCatalogResponse",  # NEW
    "ErrorResponse",
]