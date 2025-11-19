#!/usr/bin/env python3
"""
Test configuration and connectivity
"""
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config import settings, get_all_table_names
from app.services.starburst import starburst_service
from app.services.dynamodb import dynamodb_service
from app.utils.logger import app_logger as logger

def test_configuration():
    """Test if configuration is loaded correctly"""
    print("=" * 60)
    print("TESTING CONFIGURATION")
    print("=" * 60)
    
    print(f"✓ Starburst Host: {settings.starburst_host}")
    print(f"✓ Starburst Catalog: {settings.starburst_catalog}")
    print(f"✓ Starburst Schema: {settings.starburst_schema}")
    print(f"✓ AWS Region: {settings.aws_region}")
    print(f"✓ Schema Files Path: {settings.schema_files_path}")
    
    tables = get_all_table_names()
    print(f"✓ Found {len(tables)} DDL files")
    
    if tables:
        print(f"  First 5 tables: {tables[:5]}")
    
    print()

def test_starburst_connection():
    """Test Starburst connection"""
    print("=" * 60)
    print("TESTING STARBURST CONNECTION")
    print("=" * 60)
    
    try:
        # Try a simple query
        result = starburst_service.execute_query("SELECT 1 as test")
        if result and result[0][0] == 1:
            print("✓ Starburst connection successful!")
            return True
        else:
            print("✗ Starburst connection failed - unexpected result")
            return False
    except Exception as e:
        print(f"✗ Starburst connection failed: {e}")
        return False

def test_table_exists(table_name):
    """Test if a specific table exists"""
    print(f"\nChecking if table '{table_name}' exists...")
    
    try:
        exists = starburst_service.table_exists(table_name)
        if exists:
            print(f"✓ Table '{table_name}' exists in Starburst")
            return True
        else:
            print(f"✗ Table '{table_name}' does NOT exist in Starburst")
            print(f"  Make sure the table name matches exactly")
            return False
    except Exception as e:
        print(f"✗ Error checking table: {e}")
        return False

def test_table_schema(table_name):
    """Test getting table schema"""
    print(f"\nGetting schema for table '{table_name}'...")
    
    try:
        schema = starburst_service.get_table_schema(table_name)
        if schema:
            print(f"✓ Retrieved schema: {len(schema)} columns")
            print(f"  First 5 columns: {list(schema.keys())[:5]}")
            return True
        else:
            print(f"✗ Could not retrieve schema")
            return False
    except Exception as e:
        print(f"✗ Error getting schema: {e}")
        return False

def test_dynamodb_connection():
    """Test DynamoDB connection"""
    print("\n" + "=" * 60)
    print("TESTING DYNAMODB CONNECTION")
    print("=" * 60)
    
    try:
        # Try to access the table metadata table
        response = dynamodb_service.table_metadata_table.table_status
        print(f"✓ DynamoDB connection successful!")
        print(f"  Table: {settings.dynamodb_table_metadata_table}")
        print(f"  Status: {response}")
        return True
    except Exception as e:
        print(f"✗ DynamoDB connection failed: {e}")
        print(f"  Make sure DynamoDB tables are created")
        print(f"  Table names: {settings.dynamodb_table_metadata_table}, {settings.dynamodb_column_metadata_table}")
        return False

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("METADATA EXPLORER - CONFIGURATION TEST")
    print("=" * 60)
    print()
    
    # Test 1: Configuration
    test_configuration()
    
    # Test 2: Starburst
    starburst_ok = test_starburst_connection()
    
    if starburst_ok:
        # Test 3: Check a specific table
        tables = get_all_table_names()
        if tables:
            test_table = tables[0]  # Test the first table
            print(f"\nTesting with table: {test_table}")
            test_table_exists(test_table)
            test_table_schema(test_table)
    
    # Test 4: DynamoDB
    dynamodb_ok = test_dynamodb_connection()
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Starburst: {'✓ OK' if starburst_ok else '✗ FAILED'}")
    print(f"DynamoDB: {'✓ OK' if dynamodb_ok else '✗ FAILED'}")
    print()
    
    if starburst_ok and dynamodb_ok:
        print("✓ All tests passed! Ready to generate metadata.")
        return 0
    else:
        print("✗ Some tests failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())