# 🌟 Getting Started - Miktos AI Bridge Platform

Welcome to Miktos AI Bridge Platform! This guide will help you create your first 3D models and understand the platform's capabilities.

## Your First Command

After [installation](INSTALLATION.md), start with this simple command:

```bash
python main.py --interactive
```

You'll see:

```text
🚀 Miktos AI Bridge Platform v1.0.0
Agent: Ready for your commands
Type 'help' for commands or 'quit' to exit

miktos> 
```

## Basic Commands

### 1. Create Your First Object

```bash
miktos> create cube
```

**What happens:**

- Blender opens (if not already running)
- A new cube is added to the scene
- The viewer shows a live preview
- Success confirmation appears

### 2. Add Materials

```bash
miktos> add material metallic to cube
```

**Materials available:**

- `metallic` - Shiny metal surface
- `glass` - Transparent glass
- `plastic` - Colorful plastic
- `wood` - Natural wood texture
- `stone` - Rock surface

### 3. Modify Objects

```bash
miktos> scale cube 2x
miktos> rotate cube 45 degrees on Z axis
miktos> move cube up 3 units
```

### 4. Create Complex Scenes

```bash
miktos> create sphere at position 3,0,0
miktos> create cylinder with height 5
miktos> add light above all objects
```

## Understanding the Interface

### The Agent

The **Agent** is your AI assistant that:

- Understands natural language commands
- Converts them to precise 3D operations
- Manages your modeling session
- Learns from your workflow patterns

### The Viewer

The **Real-time Viewer** provides:

- Live 3D preview (no need to switch to Blender)
- WebGL-based rendering
- Automatic camera positioning
- Scene updates in real-time

### Skills System

**Skills** are expert-level functions that:

- Handle complex modeling operations
- Provide intelligent defaults
- Validate parameters automatically
- Can be combined for advanced workflows

## 10-Minute Tutorial

Let's build a simple architectural scene:

### Step 1: Create the Base

```bash
miktos> create plane with size 10x10
miktos> add material concrete to plane
```

### Step 2: Add Walls

```bash
miktos> create cube with dimensions 8,0.2,3 at position 0,4,1.5
miktos> duplicate last object and move to position 0,-4,1.5
miktos> create cube with dimensions 0.2,8,3 at position 4,0,1.5
miktos> create cube with dimensions 0.2,8,3 at position -4,0,1.5
```

### Step 3: Add a Roof

```bash
miktos> create cube with dimensions 8.5,8.5,0.2 at position 0,0,3.2
miktos> add material wood to last object
```

### Step 4: Add Windows

```bash
miktos> create cube with dimensions 1,0.1,1 at position 0,4.1,2
miktos> add material glass to last object
miktos> duplicate and move to position 0,-4.1,2
```

### Step 5: Add Lighting

```bash
miktos> add sun light from direction 45,30,60
miktos> set environment HDRI to studio
```

### Step 6: Final Touches

```bash
miktos> add camera at position 10,10,5 looking at origin
miktos> render preview
```

## Natural Language Examples

The platform understands various ways to express the same command:

### Creating Objects

- `"create a red cube"`
- `"make a cube and color it red"`
- `"add cube, make it red"`
- `"new red cube please"`

### Positioning

- `"move the cube to position 5,0,0"`
- `"place cube at coordinates 5,0,0"`
- `"put the cube at x=5"`
- `"cube goes to 5 on x axis"`

### Materials and Colors

- `"make it metallic"`
- `"apply metal material"`
- `"give it a shiny metal look"`
- `"make it look like steel"`

## Command Categories

### Object Creation

```bash
create cube/sphere/cylinder/plane/torus
make [object] with [properties]
add [object] at [position]
new [object] [size] [material]
```

### Transformations

```bash
move/translate [object] to [position]
rotate [object] [angle] degrees [axis]
scale [object] [factor]
resize [object] to [dimensions]
```

### Materials & Textures

```bash
add material [type] to [object]
color [object] [color]
make [object] [material-type]
apply [texture] to [object]
```

### Scene Management

```bash
duplicate [object]
delete/remove [object]
hide/show [object]
group [objects]
```

### Lighting & Camera

```bash
add light [type] at [position]
create camera at [position] looking at [target]
set environment [hdri/color]
adjust lighting [parameters]
```

### Rendering

```bash
render preview/final
set render quality [low/medium/high]
export as [format]
save scene as [name]
```

## Advanced Features

### Batch Operations

```bash
miktos> select all cubes
miktos> apply metallic material to selection
miktos> scale selection 1.5x
```

### Variables and Memory

```bash
miktos> set cube_size to 2.5
miktos> create cube with size {cube_size}
miktos> remember this as "building_block"
```

### Conditional Logic

```bash
miktos> if object count > 10 then optimize scene
miktos> create cube unless cube exists
miktos> while material is loading wait
```

### Scripting

```bash
miktos> repeat 5 times: create cube at random position
miktos> for each object in scene: add material metallic
miktos> loop: create sphere, move up 2, until height > 20
```

## Understanding Responses

### Success Responses

```text
✓ Created cube "Cube.001" at origin
✓ Applied metallic material
✓ Scene updated in viewer
```

### Informational Responses

```text
ℹ Current scene: 5 objects, 3 materials, 1 light
ℹ Viewer running at http://localhost:8080
ℹ Blender memory usage: 245MB
```

### Error Handling

```text
⚠ Warning: Object name already exists, using "Cube.002"
✗ Error: Invalid position coordinates
? Suggestion: Try "move cube to 5,0,0" instead
```

## Session Management

### Save Your Work

```bash
miktos> save scene as "my_project"
miktos> export as blend file
miktos> backup current session
```

### Load Previous Work

```bash
miktos> load scene "my_project"
miktos> import blend file "path/to/file.blend"
miktos> restore last session
```

### Session Info

```bash
miktos> status              # Current scene information
miktos> history             # Command history
miktos> undo                # Undo last command
miktos> redo                # Redo last undone command
```

## Tips for Success

### 1. Be Descriptive

- Instead of: `"create object"`
- Use: `"create metallic cube with size 2x2x2"`

### 2. Use Relative References

- `"the last object"`
- `"all cubes"`
- `"the selected object"`
- `"objects with metallic material"`

### 3. Combine Operations

- `"create cube, scale 2x, add metallic material, move to 5,0,0"`

### 4. Ask for Help

```bash
miktos> help materials      # List available materials
miktos> help create         # Object creation options
miktos> help commands       # All available commands
miktos> explain last error  # Get detailed error explanation
```

### 5. Use the Viewer

- Keep the viewer open at <http://localhost:8080>
- It updates automatically as you work
- Use it to verify your commands
- Perfect for quick previews

## What's Next?

1. **Explore Skills**: Learn about the [Skills System](SKILLS.md)
2. **Advanced Modeling**: Try [Complex Operations](ADVANCED.md)
3. **Automation**: Set up [Workflow Automation](AUTOMATION.md)
4. **Custom Development**: Create [Custom Skills](SKILLS_DEVELOPMENT.md)

## Common Questions

**Q: How do I see what objects are in my scene?**
A: Use `status` or `list objects`

**Q: Can I undo mistakes?**
A: Yes! Use `undo` or `Ctrl+Z`

**Q: How do I clear everything?**
A: Use `clear scene` or `delete all objects`

**Q: Where are my saved files?**
A: Check `~/miktos_projects/` or use `show save location`

**Q: The viewer isn't updating?**
A: Try `refresh viewer` or restart with `miktos> restart viewer`

## Support

- Type `help` in the interactive mode
- Visit our [Documentation](https://docs.miktos.ai)
- Join the [Community Discord](https://discord.gg/miktos)
- Report issues on [GitHub](https://github.com/Miktos-Universe/miktos-workflows/issues)

---

**Ready to create amazing 3D content?** 🎨

Start with simple commands and gradually explore the platform's powerful features!
