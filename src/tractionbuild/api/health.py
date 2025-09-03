"""
Health check and connection validation module for tractionbuild.
Provides connection checking, connection info, and health check functionality.
"""

import asyncio
import os
from typing import Dict, Any, Optional
from neo4j import GraphDatabase, AsyncGraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError, ClientError
import logging

logger = logging.getLogger(__name__)

# Configuration constants
DEFAULT_POOL_SIZE = 10
DEFAULT_TIMEOUT = 30
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_RETRY_DELAY = 1.0

async def check_connection() -> bool:
    """
    Check if Neo4j connection is available.
    
    Returns:
        bool: True if connection is successful, False otherwise
    """
    neo4j_uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "")
    
    if not neo4j_password:
        logger.warning("No Neo4j password provided")
        return False
    
    try:
        # Try to create a connection
        driver = AsyncGraphDatabase.driver(
            neo4j_uri,
            auth=(neo4j_user, neo4j_password),
            max_connection_pool_size=DEFAULT_POOL_SIZE,
            connection_acquisition_timeout=DEFAULT_TIMEOUT
        )
        
        # Verify connection with a simple query
        async with driver.session() as session:
            result = await session.run("RETURN 1 as test")
            await result.single()
        
        await driver.close()
        logger.info("Neo4j connection check successful")
        return True
        
    except (ServiceUnavailable, AuthError, ClientError) as e:
        logger.warning(f"Neo4j connection check failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during connection check: {e}")
        return False

async def get_connection_info() -> Dict[str, Any]:
    """
    Get detailed connection information.
    
    Returns:
        Dict containing connection configuration and status
    """
    neo4j_uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "")
    
    # Check if Prometheus and OpenTelemetry are available
    prometheus_available = os.getenv("PROMETHEUS_ENABLED", "false").lower() == "true"
    opentelemetry_available = os.getenv("OTEL_ENABLED", "false").lower() == "true"
    
    return {
        "uri": neo4j_uri,
        "user": neo4j_user,
        "password_set": bool(neo4j_password),
        "pool_size": DEFAULT_POOL_SIZE,
        "timeout": DEFAULT_TIMEOUT,
        "retry_attempts": DEFAULT_RETRY_ATTEMPTS,
        "prometheus_available": prometheus_available,
        "opentelemetry_available": opentelemetry_available
    }

async def health_check() -> Dict[str, Any]:
    """
    Perform a comprehensive health check.
    
    Returns:
        Dict containing health status and connection information
    """
    try:
        # Check connection
        connection_success = await check_connection()
        
        # Test a simple query if connection is successful
        query_success = False
        error = None
        
        if connection_success:
            try:
                neo4j_uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
                neo4j_user = os.getenv("NEO4J_USER", "neo4j")
                neo4j_password = os.getenv("NEO4J_PASSWORD", "")
                
                driver = AsyncGraphDatabase.driver(
                    neo4j_uri,
                    auth=(neo4j_user, neo4j_password),
                    max_connection_pool_size=DEFAULT_POOL_SIZE,
                    connection_acquisition_timeout=DEFAULT_TIMEOUT
                )
                
                async with driver.session() as session:
                    result = await session.run("RETURN 1 as health_check")
                    await result.single()
                
                await driver.close()
                query_success = True
                
            except Exception as e:
                error = str(e)
                logger.warning(f"Health check query failed: {e}")
        
        return {
            "status": "healthy" if connection_success and query_success else "unhealthy",
            "connection_success": connection_success,
            "query_success": query_success,
            "error": error
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "error",
            "connection_success": False,
            "query_success": False,
            "error": str(e)
        }
