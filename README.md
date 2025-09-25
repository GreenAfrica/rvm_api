# GreenAfrica RVM API - Reverse Vending Machine System

A computer vision-powered Reverse Vending Machine (RVM) API that automatically detects bottle insertions, manages a point-based reward system, and provides real-time monitoring capabilities.

## Features

- **🎥 Computer Vision Detection**: Real-time motion detection using OpenCV to identify bottle insertions
- **🎯 ROI-Based Monitoring**: Configurable circular region of interest for precise detection
- **⭐ Point Reward System**: Automatic point allocation for accepted bottles
- **🔗 QR Code Generation**: Unique QR codes generated for each accepted bottle
- **⚡ Real-time Updates**: WebSocket support for live status broadcasting
- **🛠️ Debug Tools**: Live camera feed, binary mask visualization, and configuration tools
- **🔧 Configurable Parameters**: Adjustable detection thresholds and camera settings

## Technology Stack

- **FastAPI** - Modern, fast web framework for building APIs
- **OpenCV** - Computer vision library for motion detection and image processing
- **WebSockets** - Real-time bidirectional communication
- **Pydantic** - Data validation using Python type annotations
- **NumPy** - Numerical computing for image processing
- **QR Code** - QR code generation for bottle tracking

## Installation

### Prerequisites

- Python 3.8+
- USB camera or compatible video capture device
- OpenCV-compatible camera drivers

### Setup

1. **Clone the repository:**

   ```bash
   git clone <repository-url>
   cd rvm_api
   ```

2. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Connect your camera** and ensure it's detected by your system

4. **Configure camera settings** (optional):
   Edit `app/settings.py` to match your camera setup and detection requirements.

## Quick Start

1. **Start the server:**

   ```bash
   python main.py
   ```

   Or using uvicorn directly:

   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Access the API:**

   - API Documentation: http://localhost:8000/docs
   - Camera Feed: http://localhost:8000/frame.jpg
   - Status: http://localhost:8000/status

3. **Test bottle detection:**
   - View the camera overlay: http://localhost:8000/frame/overlay.jpg
   - Insert a bottle into the detection area
   - Check status updates via WebSocket or REST API

## API Documentation

### Status Endpoints

#### `GET /status`

Get current RVM status including points, last event, and system message.

**Response:**

```json
{
  "message": "Ready",
  "points": 5,
  "last_event": "14:30:25",
  "last_code": "A1B2C3D4"
}
```

#### `POST /reset`

Reset the system state (points, message, events) back to initial values.

**Response:**

```json
{
  "ok": true,
  "message": "State reset",
  "points": 0
}
```

### Control Endpoints

#### `POST /event/accept`

Manually trigger a bottle acceptance event.

**Response:**

```json
{
  "ok": true,
  "code": "E5F6G7H8",
  "points": 6
}
```

#### `POST /event/reject`

Manually trigger a bottle rejection event.

**Response:**

```json
{
  "ok": true
}
```

#### `GET /qr.png`

Generate QR code for the last accepted bottle or specified code.

**Parameters:**

- `code` (optional): Specific code to encode. Uses last generated code if not provided.

**Response:** PNG image with QR code

### Configuration Endpoints

#### `GET /config`

Get current detection and camera configuration.

**Response:**

```json
{
  "ROI_CX": 320,
  "ROI_CY": 165,
  "ROI_R": 55,
  "USE_MOG2": true,
  "MOTION_PIXELS_THRESHOLD": 1500,
  "CONSEC_FRAMES_REQUIRED": 5,
  "DETECT_COOLDOWN_S": 2.5,
  "DIFF_THRESH": 15,
  "BG_LEARN_RATE": 0.005,
  "IDLE_RESET_SECONDS": 10.0
}
```

#### `POST /config/roi`

Update the Region of Interest (detection area) settings.

**Request Body:**

```json
{
  "cx": 320,
  "cy": 165,
  "r": 55
}
```

#### `POST /reseed`

Force background model reseeding for improved detection accuracy.

**Response:**

```json
{
  "ok": true
}
```

### Debug Endpoints

#### `GET /frame.jpg`

Get the latest camera frame with detection overlay.

#### `GET /frame/overlay.jpg`

Get camera frame with ROI circle overlay for configuration.

#### `GET /debug/binary.jpg`

Get the binary threshold image showing detected motion areas.

### WebSocket Events

#### Connection: `ws://localhost:8000/ws`

**Event Types:**

1. **Hello Event** (on connection):

   ```json
   {
     "type": "hello",
     "points": 5,
     "message": "Ready",
     "last_code": "A1B2C3D4"
   }
   ```

2. **Accept Event**:

   ```json
   {
     "type": "accept",
     "code": "E5F6G7H8",
     "points": 6,
     "source": "auto"
   }
   ```

3. **Reject Event**:

   ```json
   {
     "type": "reject",
     "source": "manual"
   }
   ```

4. **Ping Event** (keepalive):
   ```json
   {
     "type": "ping"
   }
   ```

## Configuration

### Camera Settings (`app/settings.py`)

```python
# Camera Configuration
CAM_INDEX = 0          # Camera device index
FRAME_W = 640          # Frame width
FRAME_H = 480          # Frame height

# Region of Interest (detection area)
ROI_CX = 320           # Center X coordinate
ROI_CY = 165           # Center Y coordinate
ROI_R = 55             # Radius in pixels

# Detection Parameters
USE_MOG2 = True                    # Use MOG2 background subtraction
MOTION_PIXELS_THRESHOLD = 1500     # Minimum motion pixels to trigger
CONSEC_FRAMES_REQUIRED = 5         # Consecutive frames needed for detection
DETECT_COOLDOWN_S = 2.5            # Cooldown between detections

# Background Subtraction (when USE_MOG2=False)
DIFF_THRESH = 15                   # Threshold for frame difference
BG_LEARN_RATE = 0.005             # Background learning rate
IDLE_RESET_SECONDS = 10.0         # Auto-reset background when idle

# Image Quality
JPEG_QUALITY = 80                  # JPEG compression quality for endpoints
```

## Usage Examples

### Python Client Example

```python
import requests
import websocket
import json

# Get current status
response = requests.get("http://localhost:8000/status")
status = response.json()
print(f"Points: {status['points']}, Message: {status['message']}")

# Manual bottle acceptance
response = requests.post("http://localhost:8000/event/accept")
result = response.json()
print(f"New code: {result['code']}, Total points: {result['points']}")

# WebSocket client
def on_message(ws, message):
    event = json.loads(message)
    if event["type"] == "accept":
        print(f"Bottle accepted! Code: {event['code']}")

ws = websocket.WebSocketApp("ws://localhost:8000/ws", on_message=on_message)
ws.run_forever()
```

### JavaScript/Web Client Example

```javascript
// REST API calls
async function getStatus() {
  const response = await fetch("/status");
  const status = await response.json();
  console.log(`Points: ${status.points}`);
}

async function acceptBottle() {
  const response = await fetch("/event/accept", { method: "POST" });
  const result = await response.json();
  console.log(`New code: ${result.code}`);
}

// WebSocket connection
const ws = new WebSocket("ws://localhost:8000/ws");
ws.onmessage = function (event) {
  const data = JSON.parse(event.data);
  if (data.type === "accept") {
    console.log(`Bottle accepted! Points: ${data.points}`);
  }
};
```

## Architecture

The system consists of several key components:

### Core Components

- **`main.py`** - FastAPI application entry point
- **`app/factory.py`** - Global singletons and dependency injection
- **`app/models.py`** - Data models and shared state management
- **`app/settings.py`** - Configuration management

### Detection System

- **`app/camera.py`** - Camera initialization and parameter control
- **`app/detector.py`** - Background motion detection thread
- **`app/events.py`** - Event handling and WebSocket broadcasting

### API Layer

- **`app/router.py`** - REST API endpoints
- **`app/ws.py`** - WebSocket connection management

### Detection Algorithm

1. **Background Modeling**: Either MOG2 or simple frame differencing
2. **ROI Filtering**: Motion detection limited to circular region
3. **Noise Reduction**: Morphological operations to clean detection mask
4. **Temporal Filtering**: Requires sustained motion over multiple frames
5. **Cooldown Management**: Prevents duplicate detections
6. **Auto-Reset**: Automatic background reseeding during idle periods

## Development

### Running in Development Mode

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Debug Workflow

1. **Camera Setup**: Use `/frame/overlay.jpg` to verify ROI positioning
2. **Detection Tuning**: Monitor `/debug/binary.jpg` to see motion detection
3. **Parameter Adjustment**: Use `/config` endpoints to fine-tune thresholds
4. **Live Monitoring**: Connect to WebSocket for real-time event streams

### Common Issues

**Camera Not Detected:**

- Check `CAM_INDEX` setting
- Verify camera permissions and drivers
- Try different camera indices (0, 1, 2, etc.)

**False Positives:**

- Increase `MOTION_PIXELS_THRESHOLD`
- Increase `CONSEC_FRAMES_REQUIRED`
- Adjust `DETECT_COOLDOWN_S`
- Fine-tune ROI position and size

**False Negatives:**

- Decrease `MOTION_PIXELS_THRESHOLD`
- Decrease `CONSEC_FRAMES_REQUIRED`
- Check lighting conditions
- Consider switching between MOG2 and frame differencing

**Background Issues:**

- Use `/reseed` endpoint to reset background
- Adjust `BG_LEARN_RATE` for dynamic environments
- Check `IDLE_RESET_SECONDS` for automatic reseeding

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Support

For issues and questions:

- Check the debug endpoints for system diagnostics
- Review configuration settings
- Monitor WebSocket events for real-time debugging
- Examine camera feed and binary detection images
