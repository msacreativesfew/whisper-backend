# Whisper Video Call with Local Object Detection

## Overview

Advanced video call feature that combines real-time object detection with intelligent voice responses. **Completely FREE** - all object detection runs locally on your device using YOLOv8.

### Key Features

✅ **Real-time Object Detection** - See what the AI sees  
✅ **Front/Back Camera Switching** - Toggle between device cameras  
✅ **Smart Memory** - Learns custom labels for objects you identify  
✅ **Zero API Cost** - Detection runs 100% locally  
✅ **Persistent Learning** - Remembers object labels across sessions  
✅ **Intelligent Summaries** - Natural language descriptions ready for Whisper to speak  

---

## Architecture

### How It Works (Completely Free)

```
┌─────────────────────────────────────────────────────────────┐
│ Your Device                                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Camera → YOLOv8 (Local)  → Detected Objects              │
│           (No API calls)    ↓                              │
│                        Create Summary                      │
│                            ↓                              │
│                        "I see a laptop,                   │
│                         keyboard, and                     │
│                         water bottle"                     │
│                            ↓                              │
│                    Send to Groq (OPTIONAL)                │
│                    Get intelligent response               │
│                            ↓                              │
│                    Whisper speaks reply                   │
│                                                           │
│  Memory Database (Local or Cloud)                         │
│  - "laptop" → "My MacBook Pro"                            │
│  - "water bottle" → "Blue Hydro Flask"                    │
│                                                           │
└─────────────────────────────────────────────────────────────┘
```

### Cost Comparison

| Operation | Cost | Our Solution |
|-----------|------|--------------|
| Object Detection (per frame) | $0.01-0.10 | **FREE** (local) |
| Memory/Learning | N/A | **FREE** (database) |
| Optional Groq Response | $0.0001-0.0005 | **Optional** |
| **Total per video session** | $5-50 | **Free to $0.01** |

---

## Installation

### 1. Install Dependencies

```bash
cd /vercel/share/v0-project
pip install opencv-python ultralytics
```

### 2. Download YOLOv8 Model

The model auto-downloads on first use (~100MB). Choose your speed/accuracy tradeoff:

```python
# In object_detection.py, change model_size:
model_size = "nano"    # 3.2M - Fastest (30+ FPS) - RECOMMENDED
model_size = "small"   # 11.2M - Balanced
model_size = "medium"  # 25.9M - Better accuracy
model_size = "large"   # 43.7M - Best accuracy (~5 FPS)
```

### 3. Update Database

```bash
python
>>> from models import init_db
>>> init_db()
# Creates tables: detection_history, user_detection_memory
```

---

## API Endpoints

### Start Video Call

```http
POST /video/start
Content-Type: application/json

{
  "user_id": "user_123",
  "session_id": "optional-custom-id",
  "camera": "front"  # or "back"
}

Response:
{
  "session_id": "session_abc123",
  "status": "active",
  "message": "Video call started - object detection ready",
  "camera": "front"
}
```

### Run Object Detection

```http
POST /video/detect/{session_id}?duration=5
Response:
{
  "session_id": "session_abc123",
  "summary": "I see a laptop, keyboard, mouse, and water bottle",
  "detected_objects": {
    "laptop": [
      {"label": "laptop", "confidence": 0.95, "bbox": [10, 20, 200, 300], ...}
    ],
    "keyboard": [
      {"label": "keyboard", "confidence": 0.92, "bbox": [210, 310, 400, 400], ...}
    ]
  },
  "total_detections": 4,
  "camera_used": "front",
  "processing_time": 5.23,
  "saved": true
}
```

### Switch Camera

```http
POST /video/switch-camera
{
  "session_id": "session_abc123",
  "user_id": "user_123"
}

Response:
{
  "success": true,
  "camera": "back",
  "message": "Switched to back camera"
}
```

### Remember an Object

User says: "That's my MacBook Pro"

```http
POST /video/remember-object
{
  "user_id": "user_123",
  "object_label": "laptop",
  "user_name": "My MacBook Pro",
  "custom_info": "silver 16-inch M3 Max"
}

Response:
{
  "success": true,
  "message": "Remembered: laptop as 'My MacBook Pro'"
}
```

Next time Whisper detects a laptop, it will say: **"I see my MacBook Pro"**

### Get Remembered Objects

```http
GET /video/remembered-objects/user_123

Response:
{
  "user_id": "user_123",
  "total_remembered": 3,
  "objects": {
    "laptop": {
      "user_name": "My MacBook Pro",
      "custom_info": "silver 16-inch M3 Max",
      "learned_at": "2024-01-15T10:30:00"
    },
    "water_bottle": {
      "user_name": "Blue Hydro Flask",
      "custom_info": "32oz",
      "learned_at": "2024-01-15T11:15:00"
    }
  }
}
```

### Get Detection History

```http
GET /video/detection-history/user_123?limit=10

Response:
{
  "user_id": "user_123",
  "total_history": 8,
  "history": [
    {
      "session_id": "session_abc123",
      "summary": "I see a laptop, keyboard, and water bottle",
      "total_detections": 3,
      "camera_used": "front",
      "processing_time": 5.23,
      "created_at": "2024-01-15T10:30:00"
    }
  ]
}
```

### End Video Call

```http
POST /video/end/session_abc123

Response:
{
  "success": true,
  "session_id": "session_abc123",
  "duration": 45.67,
  "message": "Video call ended successfully"
}
```

---

## What Objects Can It Detect?

YOLOv8 detects **80 common objects** (COCO dataset):

**People & Animals:**
person, dog, cat, horse, cow, elephant, bear, zebra, giraffe, etc.

**Vehicles:**
car, motorcycle, bicycle, bus, truck, airplane, boat, etc.

**Indoor Objects:**
laptop, keyboard, mouse, monitor, phone, chair, desk, backpack, book, bottle, cup, fork, knife, spoon, bowl, etc.

**Outdoor Objects:**
tree, flower, plant, grass, building, bench, traffic light, stop sign, etc.

**Sports:**
frisbee, skateboard, tennis racket, baseball bat, etc.

---

## Usage Examples

### Example 1: Morning Briefing

```python
# User has video call active
response = await client.post("/video/detect/session_123?duration=5")
# Result: "I see your laptop, coffee cup, and desk lamp"

# System speaks this summary to user
await whisper.speak(response["summary"])

# Optional: Get intelligent commentary
groq_response = await groq.generate(f"User is looking at: {response['summary']}. Suggest 3 productivity tips related to their workspace in 1 sentence.")
# Groq: "Great setup! Consider adding a monitor arm for better ergonomics, good lighting with the lamp, and keep your workspace organized with the desk space available."

await whisper.speak(groq_response)
```

### Example 2: Product Documentation

```python
# User shows new headphones to camera
response = await client.post("/video/detect/session_123?duration=3")
# Result: "I see headphones"

# User teaches AI
await client.post("/video/remember-object", {
  "user_id": "user_123",
  "object_label": "headphones",
  "user_name": "Sony WH-1000XM5 Headphones",
  "custom_info": "Noise-canceling, wireless, black"
})

# Next time user points headphones at camera
response = await client.post("/video/detect/session_123?duration=3")
# Result: "I see Sony WH-1000XM5 Headphones (Noise-canceling, wireless, black)"
```

### Example 3: Room Inventory

```python
# Scan office for inventory
response = await client.post("/video/detect/session_123?duration=10")
# Result: "I see 2 laptops, 3 monitors, 1 keyboard, 1 mouse, 2 chairs, and 1 desk"

# Save to database automatically
# Next session, retrieve history
history = await client.get("/video/detection-history/user_123")
# See trend of what's in the room over time
```

---

## Performance & Optimization

### Speed Benchmarks (per frame)

| Model | Size | Speed | FPS | Accuracy |
|-------|------|-------|-----|----------|
| nano | 3.2M | 5-10ms | **30+ FPS** | Good |
| small | 11.2M | 10-20ms | 20-30 FPS | Better |
| medium | 25.9M | 20-40ms | 10-20 FPS | Great |
| large | 43.7M | 40-80ms | 5-10 FPS | Excellent |

### Optimizations Built-In

✅ **Frame skipping** - Process 1 frame per 33ms (30 FPS)  
✅ **Async processing** - Non-blocking detection  
✅ **Confidence filtering** - Only show detections >50% confident  
✅ **Memory deduplication** - Group same objects together  
✅ **Local-first** - Zero network latency for detection  

---

## Integration with Groq (Optional)

For intelligent commentary about what you're seeing:

```python
# In advanced_features_api.py or your integration code
async def get_smart_commentary(detection_summary: str) -> str:
    """Send detection to Groq for intelligent response"""
    response = await groq_client.chat.completions.create(
        model="mixtral-8x7b-32768",
        messages=[{
            "role": "user",
            "content": f"User is seeing this: {detection_summary}. Provide a brief, natural response about what they're looking at (1-2 sentences)."
        }],
        max_tokens=100
    )
    return response.choices[0].message.content

# Usage
summary = detection_response["summary"]  # "I see a laptop and coffee cup"
commentary = await get_smart_commentary(summary)
# Groq: "Looks like you're settled in for a productive work session with your coffee - nice setup!"
```

---

## Database Schema

### DetectionHistory Table
```sql
CREATE TABLE detection_history (
  id VARCHAR PRIMARY KEY,
  user_id VARCHAR NOT NULL,
  session_id VARCHAR NOT NULL,
  detected_objects TEXT,  -- JSON of all detections
  summary VARCHAR,        -- Natural language summary
  total_detections INTEGER,
  processing_time FLOAT,
  camera_used VARCHAR,    -- "front" or "back"
  created_at DATETIME
);
```

### UserDetectionMemory Table
```sql
CREATE TABLE user_detection_memory (
  id VARCHAR PRIMARY KEY,
  user_id VARCHAR NOT NULL,
  object_label VARCHAR NOT NULL,    -- "laptop", "headphones", etc
  user_name VARCHAR NOT NULL,       -- "My MacBook Pro"
  custom_info VARCHAR,              -- "silver 16-inch M3 Max"
  created_at DATETIME,
  updated_at DATETIME,
  UNIQUE(user_id, object_label)
);
```

---

## Troubleshooting

### No camera available
```
Error: HTTPException 400 - No camera available
```
**Solution:** Check if camera is connected and not in use by another app

### Detection is slow
```
FPS is too low - taking 100ms+ per frame
```
**Solution:** Switch to smaller model
```python
detector = ObjectDetector(model_size="nano")  # Much faster
```

### Memory not persisting
```
Objects remembered but not showing next session
```
**Solution:** Ensure database is initialized and user_id is consistent
```python
from models import init_db
init_db()  # Create tables
```

### High CPU usage
**Solution:** Reduce processing duration or switch to nano model

---

## Advanced Customization

### Custom Object Labels

```python
# Add custom labels beyond COCO 80 objects
detector = ObjectDetector()
detector.remember_object(
    object_label="person",
    user_name="John",
    custom_info="wearing blue shirt"
)

# Now detections will show: "person (John in blue shirt)"
```

### Confidence Threshold

```python
# Only show high-confidence detections
result = detector.detect_frame(frame, confidence_threshold=0.8)

# threshold options:
# 0.5 - Default, good balance
# 0.7 - Higher confidence, fewer false positives
# 0.9 - Very strict, might miss some objects
```

### Custom Summary Format

```python
# Extend ObjectDetector class
class CustomDetector(ObjectDetector):
    def create_summary(self, objects):
        if not objects:
            return "Scene is empty"
        
        # Custom format: "Detected: laptop (95%), keyboard (92%)"
        parts = [f"{obj['label']} ({int(obj['confidence']*100)}%)" for obj in objects]
        return "Detected: " + ", ".join(parts)
```

---

## Future Enhancements

🔄 **Real-time video streaming** - Live feed to web UI  
🔄 **Object tracking** - Follow objects across frames  
🔄 **Action detection** - Recognize activities (typing, reading, etc)  
🔄 **Face recognition** - Identify known people (optional, privacy-aware)  
🔄 **Multi-camera fusion** - Combine data from multiple cameras  
🔄 **3D bounding boxes** - Depth-aware detection  

---

## Cost Analysis

### Traditional Approach (AWS Rekognition)
- 0.1 per 1000 images = **$30/day** for 300 5-second video sessions

### Our Solution
- YOLOv8: **$0** (local)
- Optional Groq commentary: **$0.0001 per call** = $0.03/day max
- Database storage: **Free tier available**
- **Total: 99.9% cost reduction**

---

## License & Attribution

YOLOv8 is released under AGPL license for academic use, and commercial license available from Ultralytics.

For production use:
- Check Ultralytics licensing for your use case
- Consider model licensing implications
- Review privacy implications of object detection

---

## Support & Questions

For issues or questions:
1. Check troubleshooting section above
2. Review API endpoint examples
3. Check console logs for detailed error messages
4. Ensure camera permissions are granted

**Remember: All object detection runs locally on your device = ZERO API COST!**
