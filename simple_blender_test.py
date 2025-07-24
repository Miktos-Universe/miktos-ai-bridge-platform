#!/usr/bin/env python3
"""
Simple Blender Skills Test
Tests individual skills directly without the complex agent system
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

# Import Blender Python API if available
try:
    import bpy  # type: ignore  # Blender Python API - only available in Blender
    print("✅ Running inside Blender - Direct API access available")
    BLENDER_MODE = True
except ImportError:
    print("📡 Running outside Blender - Will use socket communication")
    BLENDER_MODE = False


def test_basic_shapes():
    """Test creating basic shapes in Blender"""
    
    if not BLENDER_MODE:
        print("❌ This test requires running inside Blender")
        print("💡 To run this test:")
        print("   1. Open Blender")
        print("   2. Go to Scripting workspace")
        print("   3. Open this file and run it")
        return False
    
    print("🎯 Testing Basic Shape Creation...")
    
    # Clear existing mesh objects
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False, confirm=False)
    
    # Test 1: Create Sphere
    print("🔵 Creating Sphere...")
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0))
    sphere = bpy.context.active_object
    sphere.name = "TestSphere"
    print(f"✅ Created sphere: {sphere.name}")
    
    # Test 2: Create Cube
    print("🟦 Creating Cube...")
    bpy.ops.mesh.primitive_cube_add(size=2, location=(3, 0, 0))
    cube = bpy.context.active_object
    cube.name = "TestCube"
    print(f"✅ Created cube: {cube.name}")
    
    # Test 3: Create Cylinder
    print("🔶 Creating Cylinder...")
    bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(-3, 0, 0))
    cylinder = bpy.context.active_object
    cylinder.name = "TestCylinder"
    print(f"✅ Created cylinder: {cylinder.name}")
    
    # Test 4: Create a material
    print("🎨 Creating Metal Material...")
    material = bpy.data.materials.new(name="TestMetal")
    material.use_nodes = True
    
    # Get the principled BSDF node
    if material.node_tree:
        principled = material.node_tree.nodes.get("Principled BSDF")
        if principled:
            principled.inputs["Metallic"].default_value = 1.0
            principled.inputs["Roughness"].default_value = 0.2
            principled.inputs["Base Color"].default_value = (0.8, 0.8, 0.9, 1.0)
    
    # Apply material to sphere
    if sphere.data.materials:
        sphere.data.materials[0] = material
    else:
        sphere.data.materials.append(material)
    
    print(f"✅ Created and applied material: {material.name}")
    
    # Test 5: Set up basic lighting
    print("💡 Setting up lighting...")
    
    # Add a key light
    bpy.ops.object.light_add(type='SUN', location=(5, 5, 10))
    key_light = bpy.context.active_object
    key_light.name = "KeyLight"
    key_light.data.energy = 3.0
    
    print(f"✅ Added key light: {key_light.name}")
    
    print("\n🎉 All tests completed successfully!")
    print("📖 You should now see:")
    print("   • A metallic sphere at (0, 0, 0)")
    print("   • A cube at (3, 0, 0)")
    print("   • A cylinder at (-3, 0, 0)")
    print("   • Professional lighting setup")
    
    return True


def test_via_external_script():
    """Instructions for testing via external script"""
    
    script_content = '''
import bpy

# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False, confirm=False)

# Create sphere
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0))
sphere = bpy.context.active_object
sphere.name = "MiktosTestSphere"

# Create cube  
bpy.ops.mesh.primitive_cube_add(size=2, location=(3, 0, 0))
cube = bpy.context.active_object
cube.name = "MiktosTestCube"

# Create cylinder
bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2, location=(-3, 0, 0))
cylinder = bpy.context.active_object
cylinder.name = "MiktosTestCylinder"

# Create metallic material
material = bpy.data.materials.new(name="MiktosTestMetal")
material.use_nodes = True
principled = material.node_tree.nodes.get("Principled BSDF")
if principled:
    principled.inputs["Metallic"].default_value = 1.0
    principled.inputs["Roughness"].default_value = 0.2
    principled.inputs["Base Color"].default_value = (0.8, 0.8, 0.9, 1.0)

# Apply to sphere
sphere.data.materials.append(material)

# Add lighting
bpy.ops.object.light_add(type='SUN', location=(5, 5, 10))
bpy.context.active_object.data.energy = 3.0

print("✅ Miktos test objects created successfully!")
'''
    
    # Write the script to a temp file
    script_path = Path(__file__).parent / "blender_test_script.py"
    with open(script_path, "w") as f:
        f.write(script_content)
    
    print("📝 Created Blender test script:")
    print(f"   {script_path}")
    print("\n💡 To test Blender integration:")
    print("   1. Open Blender")
    print("   2. Go to Scripting workspace")
    print("   3. Open the file: blender_test_script.py")
    print("   4. Click 'Run Script'")
    print("\n🎯 Expected result:")
    print("   • Scene will be cleared")
    print("   • 3 objects will be created (sphere, cube, cylinder)")
    print("   • Metallic material will be applied to sphere")
    print("   • Lighting will be set up")


if __name__ == "__main__":
    if BLENDER_MODE:
        test_basic_shapes()
    else:
        test_via_external_script()
