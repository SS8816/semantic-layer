"""
Schema comparison service for detecting changes between stored and current schemas
"""
from typing import Dict, Tuple
from app.models import SchemaChange
from app.utils.logger import app_logger as logger


class SchemaComparator:
    """Service for comparing table schemas to detect changes"""
    
    @staticmethod
    def compare_schemas(
        current_schema: Dict[str, str],
        stored_schema: Dict[str, str]
    ) -> Tuple[bool, SchemaChange | None]:
        """
        Compare current schema with stored schema
        
        Args:
            current_schema: Current schema from Starburst {column_name: data_type}
            stored_schema: Stored schema from DynamoDB {column_name: data_type}
            
        Returns:
            Tuple of (has_changes: bool, schema_changes: SchemaChange | None)
        """
        try:
            current_cols = set(current_schema.keys())
            stored_cols = set(stored_schema.keys())
            
            # Detect new columns
            new_columns = list(current_cols - stored_cols)
            
            # Detect removed columns
            removed_columns = list(stored_cols - current_cols)
            
            # Detect type changes in common columns
            type_changes = []
            common_cols = current_cols & stored_cols
            
            for col in common_cols:
                current_type = current_schema[col].upper()
                stored_type = stored_schema[col].upper()
                
                # Normalize types for comparison
                current_type_normalized = SchemaComparator._normalize_type(current_type)
                stored_type_normalized = SchemaComparator._normalize_type(stored_type)
                
                if current_type_normalized != stored_type_normalized:
                    type_changes.append({
                        "column": col,
                        "old_type": stored_type,
                        "new_type": current_type
                    })
            
            # Check if there are any changes
            has_changes = bool(new_columns or removed_columns or type_changes)
            
            if has_changes:
                schema_change = SchemaChange(
                    new_columns=sorted(new_columns),
                    removed_columns=sorted(removed_columns),
                    type_changes=type_changes
                )
                
                logger.info(f"Schema changes detected: {len(new_columns)} new, "
                          f"{len(removed_columns)} removed, {len(type_changes)} type changes")
                
                return True, schema_change
            
            logger.debug("No schema changes detected")
            return False, None
        
        except Exception as e:
            logger.error(f"Error comparing schemas: {e}")
            return False, None
    
    @staticmethod
    def _normalize_type(data_type: str) -> str:
        """
        Normalize data type for comparison
        
        Args:
            data_type: Original data type string
            
        Returns:
            Normalized data type string
        """
        data_type = data_type.upper().strip()
        
        # Remove parameters for comparison (e.g., VARCHAR(255) -> VARCHAR)
        base_type = data_type.split('(')[0].strip()
        
        # Map common type variations
        type_mappings = {
            'INT': 'INTEGER',
            'INT2': 'SMALLINT',
            'INT4': 'INTEGER',
            'INT8': 'BIGINT',
            'FLOAT4': 'REAL',
            'FLOAT8': 'DOUBLE',
            'BOOL': 'BOOLEAN',
            'CHARACTER VARYING': 'VARCHAR',
            'CHARACTER': 'CHAR',
        }
        
        return type_mappings.get(base_type, base_type)
    
    @staticmethod
    def get_schema_from_column_metadata(column_metadata_list) -> Dict[str, str]:
        """
        Extract schema dictionary from column metadata list
        
        Args:
            column_metadata_list: List of ColumnMetadata objects
            
        Returns:
            Dictionary mapping column names to data types
        """
        return {
            col.column_name: col.data_type 
            for col in column_metadata_list
        }


# Global schema comparator instance
schema_comparator = SchemaComparator()