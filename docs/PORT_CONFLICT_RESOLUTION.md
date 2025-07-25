# Port Conflict Resolution System

## Overview

The Miktos Real-Time Viewer now includes a robust port conflict resolution system that automatically handles port allocation conflicts and enables multiple viewer instances to run simultaneously without interference.

## Features

### 1. Dynamic Port Allocation

- **Smart Port Detection**: Automatically detects which ports are in use before allocation
- **Alternative Port Search**: If preferred ports are unavailable, searches through predefined ranges and dynamic ranges
- **Process Information**: Identifies which processes are using specific ports for debugging

### 2. Conflict Prevention

- **Port Tracking**: Tracks allocated ports to prevent conflicts during rapid instance creation
- **Unique Allocation**: Ensures each viewer instance gets unique HTTP and WebSocket ports
- **Graceful Degradation**: Falls back to alternative ports when conflicts occur

### 3. Proper Cleanup

- **Port Release**: Automatically releases ports when viewer instances are stopped
- **Resource Management**: Prevents port leaks and stale allocations
- **Restart Capability**: Supports restarting with new port allocations

## Usage

### Basic Configuration

```python
# Default configuration (will auto-allocate if ports are in use)
config = {
    'port': 8080,           # Preferred HTTP port
    'websocket': {
        'port': 8081        # Preferred WebSocket port
    }
}

viewer = RealTimeViewer(config)
await viewer.start()
```

### Port Information

```python
# Get current port allocation
port_info = viewer.get_port_info()
print(f"HTTP: {port_info['http_url']}")
print(f"WebSocket: {port_info['websocket_url']}")
```

### Multiple Instances

```python
# Create multiple viewer instances - each gets unique ports
viewers = []
for i in range(3):
    viewer = RealTimeViewer(config)
    await viewer.start()
    viewers.append(viewer)
    
    port_info = viewer.get_port_info()
    print(f"Instance {i+1}: HTTP={port_info['http_port']}, WS={port_info['websocket_port']}")
```

## Port Allocation Strategy

### 1. Preferred Ports

The system first tries to use the configured preferred ports:

- HTTP: 8080 (default)
- WebSocket: 8081 (default)

### 2. Fallback Ranges

If preferred ports are unavailable, it tries these predefined ranges:

- HTTP Ports: [8080, 8090, 8100, 8110, 8120]
- WebSocket Ports: [8081, 8091, 8101, 8111, 8121]

### 3. Dynamic Range

If all predefined ports are unavailable, searches dynamically:

- Range: preferred_port ± 100
- Avoids system ports (< 1024)
- Avoids reserved ports (3000, 5000, 8000, 8888, 9000)

## Error Handling

### Port Conflicts

```log
2025-07-23 23:45:30,555 - RealTimeViewer - WARNING - Preferred port 8080 is in use, searching for alternative
2025-07-23 23:45:30,556 - RealTimeViewer - INFO - Found available port 8090
2025-07-23 23:45:30,556 - RealTimeViewer - INFO - Allocated port pair: HTTP=8090, WebSocket=8091
```

### No Available Ports

If no ports are available in the search range:

```text
RuntimeError: No available ports found near 8080
```

### Server Startup Failures

The system includes retry logic with automatic port reallocation:

- Maximum 3 retry attempts
- Automatic port switching on conflicts
- Graceful error reporting

## Debugging

### Check Current Port Usage

```bash
# Check what's using specific ports
lsof -i :8080
lsof -i :8081

# Check all ports in range
lsof -i :8080-8120
```

### Port Manager Direct Usage

```python
from viewer.port_manager import PortManager

port_manager = PortManager()

# Check port availability
available = port_manager.is_port_available(8080)

# Get port information
info = port_manager.get_port_info(8080)

# Find available port
port = port_manager.find_available_port(8080)

# Allocate port pair
http_port, ws_port = port_manager.allocate_port_pair(8080, 8081)
```

## Configuration Options

### Environment Variables

```bash
# Override default ports
export MIKTOS_HTTP_PORT=9080
export MIKTOS_WS_PORT=9081
```

### Config File

```yaml
# config.yaml
viewer:
  port: 8080
  websocket:
    port: 8081
  port_allocation:
    retry_attempts: 3
    search_range: 100
    reserved_ports: [3000, 5000, 8000]
```

## Testing

Run the comprehensive port conflict test:

```bash
cd viewer/
python test_port_comprehensive.py
```

Expected output:

- ✅ Port conflict detection
- ✅ Alternative port allocation  
- ✅ Multiple instance handling
- ✅ Unique port assignments

## Troubleshooting

### Common Issues

1. **"Address already in use" errors**
   - **Solution**: The system now handles this automatically
   - **Check**: Verify the port manager is properly initialized

2. **Multiple instances using same ports**
   - **Solution**: Fixed in the improved allocation system
   - **Check**: Ensure you're using the latest viewer code

3. **Ports not released after shutdown**
   - **Solution**: The stop() method now properly releases ports
   - **Manual cleanup**: Use `port_manager.release_port_pair(http, ws)`

### Performance Considerations

- Port checking involves network operations and may add 100-500ms to startup
- Use cached port information when possible
- Consider pre-allocating ports for high-frequency restarts

## Migration from Previous Version

If you have existing viewer instances using fixed ports:

1. **Update imports** (automatic with new code)
2. **No configuration changes needed** - existing configs work
3. **Benefits automatically applied** - conflict resolution is automatic
4. **Multiple instances now supported** - previously would fail

## Related Files

- `viewer/port_manager.py` - Core port management logic
- `viewer/real_time_viewer.py` - Updated viewer with port resolution
- `viewer/test_port_comprehensive.py` - Comprehensive test suite
- `docs/INSTALLATION.md` - Updated installation instructions
