#!/usr/bin/env python3
"""
Test script to verify Neo4j connectivity from within Docker container.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from neo4j import GraphDatabase
    from neo4j.exceptions import ServiceUnavailable, AuthError
except ImportError:
    print("❌ Neo4j driver not available")
    sys.exit(1)

def test_neo4j_connection():
    """Test Neo4j connection with proper error handling."""
    
    # Get connection details from environment
    neo4j_uri = os.getenv("NEO4J_URI", "neo4j://host.docker.internal:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "test_password")
    
    print(f"🔗 Testing Neo4j connection...")
    print(f"   URI: {neo4j_uri}")
    print(f"   User: {neo4j_user}")
    print(f"   Password: {'*' * len(neo4j_password)}")
    
    try:
        # Create driver
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        
        # Test connectivity
        driver.verify_connectivity()
        
        # Test a simple query
        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            record = result.single()
            if record and record["test"] == 1:
                print("✅ Neo4j connection successful!")
                print("   Connection verified and query executed successfully")
            else:
                print("⚠️  Connection established but query failed")
                
        driver.close()
        return True
        
    except AuthError as e:
        print(f"❌ Neo4j authentication failed: {e}")
        print("   💡 Check your NEO4J_PASSWORD environment variable")
        return False
        
    except ServiceUnavailable as e:
        print(f"❌ Neo4j service unavailable: {e}")
        print("   💡 Ensure Neo4j is running and accessible")
        print("   💡 For Docker: Make sure Neo4j is running on host.docker.internal:7687")
        return False
        
    except Exception as e:
        print(f"❌ Neo4j connection failed: {e}")
        return False

if __name__ == "__main__":
    success = test_neo4j_connection()
    sys.exit(0 if success else 1)
