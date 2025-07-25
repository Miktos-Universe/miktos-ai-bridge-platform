#!/usr/bin/env python3
"""
Direct Blender Testing Script
Bypasses the complex NLP pipeline to directly test Blender integration
"""

import asyncio
import sys
import yaml
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from agent.blender_bridge import BlenderBridge, BlenderOperation, ExecutionPlan
from skills.skill_manager import SkillManager


async def test_blender_creation():
    """Test direct object creation in Blender"""
    
    print("🎯 Starting Direct Blender Integration Test...")
    
    # Load config
    with open("config.yaml", "r") as f:
        config = yaml.safe_load(f)
    
    # Initialize components
    print("📡 Initializing Blender Bridge...")
    blender_bridge = BlenderBridge(config)
    
    print("🛠️ Initializing Skill Manager...")
    skill_manager = SkillManager(config)
    
    try:
        # Connect to Blender
        print("� Connecting to Blender...")
        if not await blender_bridge.connect():
            print("❌ Failed to connect to Blender. Make sure Blender is running!")
            return
        
        print("✅ Connected to Blender!")
        
        # Test 1: Create a Sphere
        print("\n� Test 1: Creating a Sphere...")
        sphere_op = BlenderOperation(
            operation_type="create",
            target="sphere",
            parameters={"radius": 1.0, "location": [0, 0, 0]}
        )
        plan = ExecutionPlan(
            operations=[sphere_op],
            dependencies={},
            rollback_plan=[],
            skills_used=["create_sphere"],
            estimated_time=1.0
        )
        result = await blender_bridge.execute_plan(plan)
        print(f"Sphere Result: {result.success} - {result.message}")
        
        # Test 2: Create a Cube
        print("\n🟦 Test 2: Creating a Cube...")
        cube_op = BlenderOperation(
            operation_type="create",
            target="cube",
            parameters={"size": 2.0, "location": [3, 0, 0]}
        )
        plan = ExecutionPlan(
            operations=[cube_op],
            dependencies={},
            rollback_plan=[],
            skills_used=["create_cube"],
            estimated_time=1.0
        )
        result = await blender_bridge.execute_plan(plan)
        print(f"Cube Result: {result.success} - {result.message}")
        
        print("\n✅ Direct Blender testing completed!")
        print("📖 Check Blender - you should see new objects!")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await blender_bridge.disconnect()


if __name__ == "__main__":
    asyncio.run(test_blender_creation())
