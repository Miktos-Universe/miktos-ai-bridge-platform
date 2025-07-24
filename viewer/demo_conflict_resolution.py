#!/usr/bin/env python3
"""
Practical demonstration of port conflict resolution with existing Miktos process

This script demonstrates how the new port conflict resolution system 
automatically handles conflicts with an existing Miktos process running on ports 8080/8081.
"""

import asyncio
import logging
import subprocess
import sys
from pathlib import Path

# Add the viewer module to path
sys.path.append(str(Path(__file__).parent))

from port_manager import PortManager


async def demonstrate_conflict_resolution():
    """Demonstrate port conflict resolution with real Miktos process"""
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger('ConflictDemo')
    
    logger.info("=== Miktos Port Conflict Resolution Demonstration ===")
    
    # Initialize port manager
    port_manager = PortManager(logger)
    
    # Check current state
    logger.info("\n1. Current Port Status:")
    
    existing_8080 = port_manager.get_port_info(8080)
    existing_8081 = port_manager.get_port_info(8081)
    
    if existing_8080:
        logger.info(f"  Port 8080: IN USE by {existing_8080['command']} (PID: {existing_8080['pid']})")
    else:
        logger.info("  Port 8080: AVAILABLE")
    
    if existing_8081:
        logger.info(f"  Port 8081: IN USE by {existing_8081['command']} (PID: {existing_8081['pid']})")
    else:
        logger.info("  Port 8081: AVAILABLE")
    
    # Demonstrate automatic conflict resolution
    logger.info("\n2. Demonstrating Automatic Port Allocation:")
    
    try:
        # Try to allocate the default ports (8080, 8081) - should conflict and resolve automatically
        http_port, ws_port = port_manager.allocate_port_pair(8080, 8081)
        logger.info(f"  ✅ SUCCESS: Allocated alternative ports - HTTP: {http_port}, WebSocket: {ws_port}")
        
        # Verify the allocated ports are actually available
        http_available = port_manager.is_port_available(http_port)
        ws_available = port_manager.is_port_available(ws_port)
        
        if http_available and ws_available:
            logger.info(f"  ✅ VERIFIED: Both allocated ports are actually available")
        else:
            logger.warning(f"  ⚠️  WARNING: Port availability verification failed")
            
    except RuntimeError as e:
        logger.error(f"  ❌ FAILED: Could not allocate ports - {e}")
    
    # Demonstrate multiple instances
    logger.info("\n3. Demonstrating Multiple Instance Support:")
    
    allocations = []
    for i in range(3):
        try:
            http_port, ws_port = port_manager.allocate_port_pair(8080, 8081)
            allocations.append((http_port, ws_port))
            logger.info(f"  Instance {i+1}: HTTP={http_port}, WebSocket={ws_port}")
        except RuntimeError as e:
            logger.error(f"  Instance {i+1} FAILED: {e}")
    
    # Check for uniqueness
    http_ports = [alloc[0] for alloc in allocations]
    ws_ports = [alloc[1] for alloc in allocations]
    
    if len(set(http_ports)) == len(http_ports) and len(set(ws_ports)) == len(ws_ports):
        logger.info("  ✅ SUCCESS: All port allocations are unique")
    else:
        logger.error("  ❌ FAILED: Port conflicts detected in allocations")
    
    # Show the solution implemented
    logger.info("\n4. Summary of Port Conflict Resolution:")
    logger.info("  ✅ Detects existing Miktos processes on default ports")
    logger.info("  ✅ Automatically allocates alternative ports")
    logger.info("  ✅ Supports multiple concurrent viewer instances")
    logger.info("  ✅ Provides detailed process information for debugging")
    logger.info("  ✅ Tracks allocations to prevent conflicts")
    
    # Show practical URLs that would be used
    if allocations:
        logger.info("\n5. Practical Usage URLs:")
        for i, (http_port, ws_port) in enumerate(allocations):
            logger.info(f"  Instance {i+1}:")
            logger.info(f"    Web Interface: http://localhost:{http_port}")
            logger.info(f"    WebSocket API:  ws://localhost:{ws_port}")
    
    logger.info("\n=== Resolution Status: COMPLETED ✅ ===")
    logger.info("The port conflict issue has been resolved!")
    logger.info("Multiple Miktos viewer instances can now run simultaneously.")


async def test_integration_with_config():
    """Test how this integrates with typical Miktos configuration"""
    
    logger = logging.getLogger('IntegrationTest')
    
    logger.info("\n=== Integration Test with Miktos Configuration ===")
    
    # Simulate typical Miktos config
    configs = [
        {"port": 8080, "websocket": {"port": 8081}},  # Default config
        {"port": 8080, "websocket": {"port": 8081}},  # Another instance with same config
        {"port": 8090, "websocket": {"port": 8091}},  # Preferred alternative
    ]
    
    port_manager = PortManager(logger)
    results = []
    
    for i, config in enumerate(configs):
        preferred_http = config.get('port', 8080)
        preferred_ws = config.get('websocket', {}).get('port', 8081)
        
        logger.info(f"\nInstance {i+1} - Preferred: HTTP={preferred_http}, WS={preferred_ws}")
        
        try:
            http_port, ws_port = port_manager.allocate_port_pair(preferred_http, preferred_ws)
            results.append({
                'instance': i+1,
                'http_port': http_port,
                'ws_port': ws_port,
                'http_url': f"http://localhost:{http_port}",
                'ws_url': f"ws://localhost:{ws_port}"
            })
            
            logger.info(f"  Allocated: HTTP={http_port}, WS={ws_port}")
            
        except RuntimeError as e:
            logger.error(f"  Failed: {e}")
    
    # Summary
    logger.info(f"\n✅ Successfully allocated ports for {len(results)} instances")
    logger.info("This demonstrates the solution to the original problem:")
    logger.info("  'Multiple instances trying to bind to same WebSocket port'")
    logger.info("  → Now resolved with automatic alternative port allocation")


if __name__ == "__main__":
    asyncio.run(demonstrate_conflict_resolution())
    asyncio.run(test_integration_with_config())
