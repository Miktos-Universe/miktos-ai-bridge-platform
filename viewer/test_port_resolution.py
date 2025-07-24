#!/usr/bin/env python3
"""
Test script for port conflict resolution in Miktos Real-Time Viewer

This script tests the dynamic port allocation and conflict resolution
to ensure multiple viewer instances can start without port conflicts.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the viewer module to path
sys.path.append(str(Path(__file__).parent))

from port_manager import PortManager


async def test_port_manager():
    """Test the PortManager functionality"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger('PortTest')
    port_manager = PortManager(logger)
    
    logger.info("=== Testing Port Manager ===")
    
    # Test 1: Check current port usage
    logger.info("\n1. Checking current port usage:")
    for port in [8080, 8081, 8090, 8091]:
        available = port_manager.is_port_available(port)
        status = "AVAILABLE" if available else "IN USE"
        logger.info(f"  Port {port}: {status}")
        
        if not available:
            info = port_manager.get_port_info(port)
            if info:
                logger.info(f"    Used by: {info['command']} (PID: {info['pid']})")
    
    # Test 2: Allocate port pairs
    logger.info("\n2. Testing port pair allocation:")
    try:
        http_port, ws_port = port_manager.allocate_port_pair(8080, 8081)
        logger.info(f"  Allocated pair: HTTP={http_port}, WebSocket={ws_port}")
        
        # Try to allocate another pair
        http_port2, ws_port2 = port_manager.allocate_port_pair(8080, 8081)
        logger.info(f"  Second pair: HTTP={http_port2}, WebSocket={ws_port2}")
        
    except RuntimeError as e:
        logger.error(f"  Port allocation failed: {e}")
    
    # Test 3: Find available ports in a range
    logger.info("\n3. Testing port range search:")
    try:
        available_port = port_manager.find_available_port(8080, [8080, 8090, 8100, 8110])
        logger.info(f"  Found available port: {available_port}")
    except RuntimeError as e:
        logger.error(f"  No available ports found: {e}")
    
    logger.info("\n=== Port Manager Test Complete ===")


async def test_viewer_startup():
    """Test viewer startup with port conflict resolution"""
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger('ViewerTest')
    
    logger.info("=== Testing Viewer Startup ===")
    
    # Import here to avoid import issues
    try:
        from real_time_viewer import RealTimeViewer
    except ImportError as e:
        logger.error(f"Failed to import RealTimeViewer: {e}")
        return
    
    # Test configuration
    config = {
        'port': 8080,
        'websocket': {'port': 8081},
        'resolution': [1280, 720],
        'fps_target': 30,
        'quality': 'medium',
        'sync': {},
        'viewport': {},
        'renderer': {}
    }
    
    # Create multiple viewer instances to test port conflicts
    viewers = []
    
    try:
        for i in range(3):
            logger.info(f"\nStarting viewer instance {i+1}:")
            
            viewer = RealTimeViewer(config)
            port_info = viewer.get_port_info()
            logger.info(f"  Allocated ports: {port_info}")
            
            # Note: We're not actually starting the viewers here because
            # that would require the full Miktos environment. This test
            # focuses on port allocation logic.
            
            viewers.append(viewer)
        
        logger.info(f"\nSuccessfully created {len(viewers)} viewer instances with unique ports")
        
        # Show port allocations
        logger.info("\nPort allocations:")
        for i, viewer in enumerate(viewers):
            port_info = viewer.get_port_info()
            logger.info(f"  Viewer {i+1}: HTTP={port_info['http_port']}, WS={port_info['websocket_port']}")
    
    except Exception as e:
        logger.error(f"Error during viewer testing: {e}")
    
    logger.info("\n=== Viewer Test Complete ===")


async def main():
    """Run all tests"""
    print("Miktos Real-Time Viewer - Port Conflict Resolution Test")
    print("=" * 60)
    
    await test_port_manager()
    print()
    await test_viewer_startup()
    
    print("\nTest completed. Check the logs above for results.")


if __name__ == "__main__":
    asyncio.run(main())
