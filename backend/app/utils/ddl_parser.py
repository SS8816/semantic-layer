"""
DDL Parser - Extract schema information from SQL DDL files
"""
import re
import sqlparse
from typing import List, Dict, Tuple
from app.utils.logger import app_logger as logger


def parse_ddl_file(file_path: str) -> Dict[str, str]:
    """
    Parse a DDL file and extract column names and data types
    
    Args:
        file_path: Path to the DDL SQL file
        
    Returns:
        Dictionary mapping column names to data types
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            ddl_content = f.read()
        
        return parse_ddl_string(ddl_content)
    
    except FileNotFoundError:
        logger.error(f"DDL file not found: {file_path}")
        return {}
    except Exception as e:
        logger.error(f"Error parsing DDL file {file_path}: {e}")
        return {}


def parse_ddl_string(ddl_content: str) -> Dict[str, str]:
    """
    Parse DDL string and extract column definitions
    
    Args:
        ddl_content: DDL SQL string
        
    Returns:
        Dictionary mapping column names to data types
    """
    columns = {}
    
    try:
        # Parse SQL using sqlparse
        parsed = sqlparse.parse(ddl_content)
        
        if not parsed:
            logger.warning("No SQL statements found in DDL")
            return columns
        
        # Get the first statement (assuming single CREATE TABLE statement)
        statement = parsed[0]
        
        # Extract CREATE TABLE content
        tokens = statement.tokens
        
        # Find the column definitions (inside parentheses)
        column_defs = None
        for token in tokens:
            if isinstance(token, sqlparse.sql.Parenthesis):
                column_defs = token
                break
        
        if not column_defs:
            logger.warning("No column definitions found in DDL")
            return columns
        
        # Parse individual column definitions
        column_text = str(column_defs).strip('()')
        
        # Split by commas (but respect nested parentheses and commas in types)
        column_lines = split_column_definitions(column_text)
        
        for line in column_lines:
            line = line.strip()
            if not line or line.upper().startswith(('PRIMARY', 'FOREIGN', 'CONSTRAINT', 'UNIQUE', 'CHECK', 'INDEX')):
                continue
            
            # Extract column name and type
            column_info = parse_column_definition(line)
            if column_info:
                col_name, col_type = column_info
                columns[col_name] = col_type
        
        logger.info(f"Parsed {len(columns)} columns from DDL")
        return columns
    
    except Exception as e:
        logger.error(f"Error parsing DDL string: {e}")
        return columns


def split_column_definitions(text: str) -> List[str]:
    """
    Split column definitions by comma, respecting nested parentheses
    
    Args:
        text: Column definitions text
        
    Returns:
        List of column definition strings
    """
    definitions = []
    current = []
    paren_depth = 0
    
    for char in text:
        if char == '(':
            paren_depth += 1
            current.append(char)
        elif char == ')':
            paren_depth -= 1
            current.append(char)
        elif char == ',' and paren_depth == 0:
            definitions.append(''.join(current))
            current = []
        else:
            current.append(char)
    
    # Add the last definition
    if current:
        definitions.append(''.join(current))
    
    return definitions


def parse_column_definition(definition: str) -> Tuple[str, str] | None:
    """
    Parse a single column definition to extract name and type
    
    Args:
        definition: Column definition string (e.g., "road_id BIGINT NOT NULL")
        
    Returns:
        Tuple of (column_name, data_type) or None if parsing fails
    """
    try:
        # Remove leading/trailing whitespace
        definition = definition.strip()
        
        # Split by whitespace
        parts = definition.split()
        
        if len(parts) < 2:
            return None
        
        # First part is column name (remove backticks, quotes)
        column_name = parts[0].strip('`"\'')
        
        # Second part is data type (may include size/precision)
        data_type = parts[1].upper()
        
        # Handle types with parameters like VARCHAR(255), DECIMAL(10,2)
        if '(' in definition:
            # Extract the full type including parameters
            match = re.search(r'\b(\w+\s*\([^)]+\))', definition, re.IGNORECASE)
            if match:
                data_type = match.group(1).upper()
        
        # Normalize common type names
        data_type = normalize_data_type(data_type)
        
        return (column_name, data_type)
    
    except Exception as e:
        logger.debug(f"Could not parse column definition '{definition}': {e}")
        return None


def normalize_data_type(data_type: str) -> str:
    """
    Normalize data type names to standard format
    
    Args:
        data_type: Original data type string
        
    Returns:
        Normalized data type string
    """
    data_type = data_type.upper().strip()
    
    # Map common variations to standard types
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
    
    # Check for exact match first
    if data_type in type_mappings:
        return type_mappings[data_type]
    
    # Check for base type (before parentheses)
    base_type = data_type.split('(')[0].strip()
    if base_type in type_mappings:
        # Preserve parameters
        if '(' in data_type:
            params = data_type[data_type.index('('):]
            return type_mappings[base_type] + params
        return type_mappings[base_type]
    
    return data_type


def get_table_name_from_ddl(file_path: str) -> str | None:
    """
    Extract table name from DDL file
    
    Args:
        file_path: Path to DDL file
        
    Returns:
        Table name or None if not found
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            ddl_content = f.read()
        
        # Look for CREATE TABLE statement
        match = re.search(r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`"\']?(\w+)[`"\']?', 
                         ddl_content, re.IGNORECASE)
        
        if match:
            return match.group(1)
        
        return None
    
    except Exception as e:
        logger.error(f"Error extracting table name from {file_path}: {e}")
        return None