"""
Simple Neptune Analytics connection test script

This tests basic connectivity to Neptune Analytics before running the full test.
"""

from app.services import neptune_service
from app.utils.logger import app_logger as logger

def test_connection():
    """Test basic Neptune Analytics connection"""

    print("=" * 80)
    print("NEPTUNE ANALYTICS CONNECTION TEST")
    print("=" * 80)
    print()
    print(f"Endpoint: {neptune_service.endpoint}")
    print(f"Port: {neptune_service.port}")
    print(f"Base URL: {neptune_service.base_url}")
    print(f"Neptune Host: {neptune_service.neptune_host}")
    print()

    try:
        print("🔌 Testing connection with simple query...")

        # Simple query to test connection
        query = "RETURN 1 as test"

        result = neptune_service.execute_query(query)

        print(f"✅ Connection successful!")
        print(f"   Query result: {result}")
        print()
        print("=" * 80)
        print("✅ Neptune Analytics is ready to use!")
        print("=" * 80)

    except Exception as e:
        print(f"❌ Connection failed!")
        print(f"   Error: {e}")
        print()
        print("Troubleshooting:")
        print("  1. Check AWS credentials are configured:")
        print("     - Run: gimme-aws-creds")
        print("     - Verify you're in the correct AWS account")
        print("  2. Verify Neptune Analytics endpoint is correct")
        print("  3. Check network connectivity to 10.96.112.27")
        print()

        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_connection()
