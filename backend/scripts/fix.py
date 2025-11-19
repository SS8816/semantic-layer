#!/usr/bin/env python3
"""
Fix DDL files - Add CREATE TABLE headers if missing
"""
import os
import sys
import re

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config import settings

def fix_ddl_file(file_path, table_name):
    """Add CREATE TABLE header if missing"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if already has CREATE TABLE
    if 'CREATE' in content.upper():
        print(f"✓ {table_name} - Already has CREATE TABLE")
        return False
    
    # Add CREATE EXTERNAL TABLE header
    fixed_content = f"CREATE EXTERNAL TABLE {table_name} (\n{content}\n)"
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print(f"✓ {table_name} - Added CREATE TABLE header")
    return True

def main():
    schema_dir = settings.schema_files_path
    
    if not os.path.exists(schema_dir):
        print(f"Error: Schema directory not found: {schema_dir}")
        return 1
    
    files = [f for f in os.listdir(schema_dir) if f.endswith('.sql')]
    print(f"Found {len(files)} DDL files\n")
    
    fixed_count = 0
    for filename in files:
        table_name = filename.replace('.sql', '')
        file_path = os.path.join(schema_dir, filename)
        
        if fix_ddl_file(file_path, table_name):
            fixed_count += 1
    
    print(f"\nFixed {fixed_count} files")
    return 0

if __name__ == "__main__":
    sys.exit(main())