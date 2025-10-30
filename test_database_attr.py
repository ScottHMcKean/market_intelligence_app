"""Test script to verify database attribute is available."""

import sys

# Check databricks-sdk version
try:
    import databricks.sdk
    from databricks.sdk import WorkspaceClient
    
    print("=" * 60)
    print("Databricks SDK Database Attribute Test")
    print("=" * 60)
    
    # Try to get version
    try:
        version = getattr(databricks.sdk, '__version__', 'unknown')
        print(f"✓ databricks-sdk version: {version}")
    except:
        print("⚠ Could not determine databricks-sdk version")
    
    # Test WorkspaceClient instantiation
    try:
        client = WorkspaceClient()
        print("✓ WorkspaceClient instantiated successfully")
    except Exception as e:
        print(f"✗ Failed to instantiate WorkspaceClient: {e}")
        sys.exit(1)
    
    # Check for database attribute
    if hasattr(client, 'database'):
        print(f"✓ WorkspaceClient.database attribute exists")
        print(f"  Type: {type(client.database).__name__}")
        
        # List available methods
        methods = [m for m in dir(client.database) if not m.startswith('_')]
        print(f"  Available methods: {', '.join(methods[:5])}...")
    else:
        print("✗ WorkspaceClient.database attribute NOT FOUND")
        print("  This requires databricks-sdk>=0.40.0")
        print("  Please upgrade: pip install --upgrade 'databricks-sdk>=0.40.0'")
        sys.exit(1)
    
    print("=" * 60)
    print("✅ All checks passed!")
    print("=" * 60)
    
except ImportError as e:
    print(f"✗ Failed to import databricks-sdk: {e}")
    print("  Please install: pip install 'databricks-sdk>=0.40.0'")
    sys.exit(1)
except Exception as e:
    print(f"✗ Unexpected error: {e}")
    sys.exit(1)

