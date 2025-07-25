
"""
Miktos Advanced Blender Integration Test Script

This script demonstrates advanced 3D scene creation capabilities through the Miktos system.
It creates professional 3D scenes with advanced materials, lighting, and composition.

NOTE: This script is designed to run inside Blender's Python environment.
The 'bpy' module is Blender's built-in Python API and is only available when 
running within Blender itself.
"""

import bpy  # type: ignore  # Blender Python API - only available in Blender

print("🎯 Miktos Advanced Integration Test")
print("=====================================")

# Clear scene
print("🧹 Clearing scene...")
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False, confirm=False)

# Create sphere with advanced material
print("🔵 Creating metallic sphere...")
bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0))
sphere = bpy.context.active_object
sphere.name = "MiktosTestSphere"

# Create cube with subdivision
print("🟦 Creating subdivided cube...")
bpy.ops.mesh.primitive_cube_add(size=2, location=(3, 0, 0))
cube = bpy.context.active_object
cube.name = "MiktosTestCube"

# Add subdivision surface modifier
subsurf = cube.modifiers.new(name="SubSurf", type='SUBSURF')
subsurf.levels = 2

# Create cylinder with array modifier
print("🔶 Creating cylinder with array...")
bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=2, location=(-3, 0, 0))
cylinder = bpy.context.active_object
cylinder.name = "MiktosTestCylinder"

# Add array modifier
array = cylinder.modifiers.new(name="Array", type='ARRAY')
array.count = 3
array.relative_offset_displace[0] = 1.5

# Create advanced metallic material
print("🎨 Creating advanced materials...")
metal_material = bpy.data.materials.new(name="MiktosAdvancedMetal")
metal_material.use_nodes = True
metal_nodes = metal_material.node_tree.nodes
metal_principled = metal_nodes.get("Principled BSDF")

if metal_principled:
    metal_principled.inputs["Metallic"].default_value = 1.0
    metal_principled.inputs["Roughness"].default_value = 0.1
    metal_principled.inputs["Base Color"].default_value = (0.9, 0.7, 0.3, 1.0)  # Gold
    metal_principled.inputs["IOR"].default_value = 1.5

# Create glass material
glass_material = bpy.data.materials.new(name="MiktosGlass")
glass_material.use_nodes = True
glass_nodes = glass_material.node_tree.nodes
glass_principled = glass_nodes.get("Principled BSDF")

if glass_principled:
    glass_principled.inputs["Transmission"].default_value = 1.0
    glass_principled.inputs["Roughness"].default_value = 0.0
    glass_principled.inputs["IOR"].default_value = 1.45
    glass_principled.inputs["Alpha"].default_value = 0.1

# Apply materials
sphere.data.materials.append(metal_material)
cube.data.materials.append(glass_material)

# Create professional three-point lighting
print("💡 Setting up three-point lighting...")

# Key light (main light)
bpy.ops.object.light_add(type='SUN', location=(5, 5, 10))
key_light = bpy.context.active_object
key_light.name = "KeyLight"
key_light.data.energy = 5.0
key_light.rotation_euler = (0.7, 0, 0.8)

# Fill light (softer, from opposite side)
bpy.ops.object.light_add(type='AREA', location=(-3, 3, 5))
fill_light = bpy.context.active_object
fill_light.name = "FillLight"
fill_light.data.energy = 2.0
fill_light.data.size = 3.0

# Rim light (back light for edge definition)
bpy.ops.object.light_add(type='SPOT', location=(0, -5, 8))
rim_light = bpy.context.active_object
rim_light.name = "RimLight"
rim_light.data.energy = 3.0
rim_light.data.spot_size = 1.2

# Set up camera for good composition
print("📷 Positioning camera...")
camera = bpy.data.objects.get("Camera")
if camera:
    camera.location = (7, -7, 5)
    camera.rotation_euler = (1.1, 0, 0.785)

# Switch to rendered viewport shading for immediate preview
print("🖼️ Switching to rendered view...")
for area in bpy.context.screen.areas:
    if area.type == 'VIEW_3D':
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                space.shading.type = 'RENDERED'

print("\n✅ Miktos Advanced Test Complete!")
print("🎨 Created:")
print("   • Golden metallic sphere")
print("   • Glass cube with subdivision")
print("   • Cylinder array")
print("   • Professional 3-point lighting")
print("   • Optimal camera positioning")
print("🎬 Switched to rendered viewport - you should see a cinematic result!")
