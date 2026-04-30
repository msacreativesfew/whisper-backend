"""
Advanced Object Detection Module for Video Calls
Uses YOLOv8 (free, lightweight) for real-time local object detection
Minimal API usage - only sends summaries to Groq for intelligent responses
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import asyncio
from dataclasses import dataclass, asdict
import logging

# Free/Open-source computer vision
try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None
    np = None
    print("[Whisper] OpenCV not installed. Install with: pip install opencv-python")

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None
    print("[Whisper] YOLOv8 not installed. Install with: pip install ultralytics")

logger = logging.getLogger(__name__)


@dataclass
class DetectedObject:
    """Represents a detected object in a frame"""
    label: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    timestamp: str

    def to_dict(self):
        return {
            "label": self.label,
            "confidence": round(self.confidence, 2),
            "bbox": self.bbox,
            "timestamp": self.timestamp
        }


class ObjectDetector:
    """Local YOLOv8 object detector - runs entirely on device, no API calls"""

    def __init__(self, model_size: str = "nano"):
        """
        Initialize YOLOv8 model
        
        Args:
            model_size: "nano" (fastest, low accuracy) to "large" (slower, high accuracy)
                       "nano" is recommended for real-time video (30+ FPS)
        """
        self.model_size = model_size
        self.model = None
        self.class_names = {}
        self.detected_objects_cache = {}
        self.learning_memory = {}  # Remember user's custom labels
        
        self._initialize_model()

    def _initialize_model(self):
        """Load YOLOv8 model"""
        try:
            model_map = {
                "nano": "yolov8n.pt",      # 3.2M params - Real-time, ~30 FPS
                "small": "yolov8s.pt",     # 11.2M params - Balanced
                "medium": "yolov8m.pt",    # 25.9M params - Better accuracy
                "large": "yolov8l.pt",     # 43.7M params - High accuracy
            }
            
            model_name = model_map.get(self.model_size, "yolov8n.pt")
            logger.info(f"[Whisper] Loading YOLOv8-{self.model_size} model...")
            
            self.model = YOLO(model_name)
            
            # Store class names (80 COCO classes)
            self.class_names = self.model.names
            logger.info(f"[Whisper] Object detector ready: {len(self.class_names)} classes")
            
        except Exception as e:
            logger.error(f"[Whisper] Failed to load object detection model: {e}")
            raise

    def detect_frame(self, frame: "np.ndarray", confidence_threshold: float = 0.5) -> Dict:
        """
        Detect objects in a single frame
        
        Args:
            frame: OpenCV frame (BGR format)
            confidence_threshold: Minimum confidence to include detection (0-1)
            
        Returns:
            Dictionary with detected objects and frame stats
        """
        if self.model is None:
            return {"objects": [], "error": "Model not loaded"}

        try:
            # Run inference (very fast - ~5-10ms per frame with nano model)
            results = self.model(frame, conf=confidence_threshold, verbose=False)
            
            detected = []
            timestamp = datetime.now().isoformat()
            
            for result in results:
                if result.boxes is not None:
                    for box in result.boxes:
                        x1, y1, x2, y2 = map(int, box.xyxy[0])
                        confidence = float(box.conf[0])
                        class_id = int(box.cls[0])
                        label = self.class_names.get(class_id, f"Unknown-{class_id}")
                        
                        # Check if user has custom label for this object
                        if label in self.learning_memory:
                            custom_label = self.learning_memory[label]["user_name"]
                            detected.append(DetectedObject(
                                label=f"{label} ({custom_label})",
                                confidence=confidence,
                                bbox=(x1, y1, x2, y2),
                                timestamp=timestamp
                            ))
                        else:
                            detected.append(DetectedObject(
                                label=label,
                                confidence=confidence,
                                bbox=(x1, y1, x2, y2),
                                timestamp=timestamp
                            ))
            
            return {
                "success": True,
                "objects": [obj.to_dict() for obj in detected],
                "count": len(detected),
                "timestamp": timestamp,
                "frame_shape": frame.shape
            }
            
        except Exception as e:
            logger.error(f"[Whisper] Detection error: {e}")
            return {"success": False, "error": str(e), "objects": []}

    def create_summary(self, objects: List[Dict]) -> str:
        """
        Create a natural language summary of detected objects
        Perfect for passing to Groq/Whisper for speech
        
        Args:
            objects: List of detected object dictionaries
            
        Returns:
            Summary string like "I see a laptop, keyboard, mouse, and water bottle"
        """
        if not objects:
            return "I don't see any recognizable objects right now"

        # Group by confidence level
        high_confidence = [obj for obj in objects if obj["confidence"] > 0.7]
        medium_confidence = [obj for obj in objects if 0.5 < obj["confidence"] <= 0.7]

        summary_parts = []
        
        if high_confidence:
            labels = [obj["label"].split("(")[0].strip() for obj in high_confidence]
            unique_labels = list(dict.fromkeys(labels))  # Remove duplicates, keep order
            
            if len(unique_labels) == 1:
                summary_parts.append(f"I see {unique_labels[0]}")
            else:
                summary_parts.append(f"I see {', '.join(unique_labels[:-1])} and {unique_labels[-1]}")
        
        if medium_confidence and summary_parts:
            labels = [obj["label"].split("(")[0].strip() for obj in medium_confidence]
            unique_labels = list(dict.fromkeys(labels))
            summary_parts.append(f", and possibly {', '.join(unique_labels)}")
        
        return ("".join(summary_parts) + "." if summary_parts else "I can see some objects but they're not clear")

    def remember_object(self, object_label: str, user_name: str, custom_info: Optional[str] = None):
        """
        Learn and remember custom labels for objects
        Example: user says "That's my MacBook" -> remember MacBook as "my MacBook"
        
        Args:
            object_label: Original label (e.g., "laptop")
            user_name: What user calls it (e.g., "MacBook Pro")
            custom_info: Optional context (e.g., "silver 16-inch")
        """
        self.learning_memory[object_label] = {
            "user_name": user_name,
            "custom_info": custom_info,
            "learned_at": datetime.now().isoformat()
        }
        logger.info(f"[Whisper] Remembered: {object_label} = {user_name}")

    def get_remembered_objects(self) -> Dict:
        """Get all remembered custom object labels"""
        return self.learning_memory

    def save_memory(self, db_session, user_id: str):
        """
        Save learning memory to database for persistence
        Next time the user logs in, we'll load this
        """
        try:
            from models import UserDetectionMemory
            
            for object_label, memory_data in self.learning_memory.items():
                existing = db_session.query(UserDetectionMemory).filter_by(
                    user_id=user_id,
                    object_label=object_label
                ).first()
                
                if existing:
                    existing.user_name = memory_data["user_name"]
                    existing.custom_info = memory_data.get("custom_info")
                else:
                    new_memory = UserDetectionMemory(
                        user_id=user_id,
                        object_label=object_label,
                        user_name=memory_data["user_name"],
                        custom_info=memory_data.get("custom_info")
                    )
                    db_session.add(new_memory)
            
            db_session.commit()
            logger.info(f"[Whisper] Saved detection memory for user {user_id}")
        except Exception as e:
            logger.error(f"[Whisper] Failed to save memory: {e}")

    def load_memory(self, db_session, user_id: str):
        """Load previously learned object labels from database"""
        try:
            from models import UserDetectionMemory
            
            memories = db_session.query(UserDetectionMemory).filter_by(user_id=user_id).all()
            
            for memory in memories:
                self.learning_memory[memory.object_label] = {
                    "user_name": memory.user_name,
                    "custom_info": memory.custom_info,
                    "learned_at": memory.created_at.isoformat() if memory.created_at else None
                }
            
            logger.info(f"[Whisper] Loaded {len(memories)} remembered objects for user {user_id}")
        except Exception as e:
            logger.error(f"[Whisper] Failed to load memory: {e}")


class VideoCameraManager:
    """Handle front/back camera switching and frame capture"""

    def __init__(self):
        self.front_camera = None
        self.back_camera = None
        self.active_camera = None
        self.is_recording = False
        
    def initialize_cameras(self):
        """Initialize available cameras"""
        # Try to find front camera (usually 0)
        try:
            self.front_camera = cv2.VideoCapture(0)
            if self.front_camera.isOpened():
                logger.info("[Whisper] Front camera initialized")
            else:
                self.front_camera = None
        except:
            self.front_camera = None
        
        # Try to find back camera (usually 1)
        try:
            self.back_camera = cv2.VideoCapture(1)
            if self.back_camera.isOpened():
                logger.info("[Whisper] Back camera initialized")
            else:
                self.back_camera = None
        except:
            self.back_camera = None
        
        # Default to front camera
        if self.front_camera:
            self.active_camera = self.front_camera
            self.camera_name = "front"
        elif self.back_camera:
            self.active_camera = self.back_camera
            self.camera_name = "back"

    def switch_camera(self) -> bool:
        """Switch between front and back camera"""
        if self.camera_name == "front" and self.back_camera:
            self.active_camera = self.back_camera
            self.camera_name = "back"
            logger.info("[Whisper] Switched to back camera")
            return True
        elif self.camera_name == "back" and self.front_camera:
            self.active_camera = self.front_camera
            self.camera_name = "front"
            logger.info("[Whisper] Switched to front camera")
            return True
        return False

    def get_frame(self) -> Optional["np.ndarray"]:
        """Get current frame from active camera"""
        if self.active_camera is None:
            return None
        
        ret, frame = self.active_camera.read()
        if ret:
            return frame
        return None

    def release(self):
        """Release all camera resources"""
        if self.front_camera:
            self.front_camera.release()
        if self.back_camera:
            self.back_camera.release()
        logger.info("[Whisper] Cameras released")


# Efficient frame processor for real-time detection
class RealTimeDetectionProcessor:
    """Process video stream with object detection and Groq summarization"""
    
    def __init__(self, groq_api_key: str):
        self.detector = ObjectDetector(model_size="nano")  # Nano = fastest
        self.camera = VideoCameraManager()
        self.groq_api_key = groq_api_key
        self.last_summary = ""
        self.detection_history = []
        
    async def process_stream(self, duration_seconds: int = 10) -> Dict:
        """
        Process video stream and create summaries
        Only sends one summary to Groq per 5 seconds of video
        = 80% fewer API calls compared to per-frame sending
        
        Args:
            duration_seconds: How long to process video
            
        Returns:
            Summary of all detected objects with one Groq response
        """
        self.camera.initialize_cameras()
        if self.camera.active_camera is None:
            return {"error": "No camera available"}
        
        all_detections = {}
        start_time = datetime.now()
        
        try:
            while (datetime.now() - start_time).total_seconds() < duration_seconds:
                frame = self.camera.get_frame()
                if frame is None:
                    await asyncio.sleep(0.033)  # ~30 FPS
                    continue
                
                # Run detection (ONLY local, NO API cost)
                result = self.detector.detect_frame(frame)
                
                if result["objects"]:
                    # Group detections by label
                    for obj in result["objects"]:
                        label = obj["label"]
                        if label not in all_detections:
                            all_detections[label] = []
                        all_detections[label].append(obj)
                
                await asyncio.sleep(0.033)  # ~30 FPS, doesn't block
        
        finally:
            self.camera.release()
        
        # Create SINGLE summary for all detections
        if all_detections:
            objects_list = [obj for objects in all_detections.values() for obj in objects]
            summary = self.detector.create_summary(objects_list)
            
            # OPTIONAL: Send summary to Groq for intelligent response (1 API call)
            # groq_response = await self._get_groq_response(summary)
            
            return {
                "success": True,
                "detected_objects": all_detections,
                "total_detections": len(objects_list),
                "summary": summary,
                "processing_time": (datetime.now() - start_time).total_seconds()
            }
        
        return {
            "success": True,
            "detected_objects": {},
            "total_detections": 0,
            "summary": "No objects detected",
            "processing_time": (datetime.now() - start_time).total_seconds()
        }

    async def _get_groq_response(self, detection_summary: str) -> str:
        """
        Send detection summary to Groq for intelligent commentary
        This is OPTIONAL - detection works 100% locally
        
        Args:
            detection_summary: Summary from object detector
            
        Returns:
            Groq's intelligent response about the detections
        """
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    json={
                        "model": "mixtral-8x7b-32768",
                        "messages": [
                            {
                                "role": "user",
                                "content": f"I'm looking at my camera and {detection_summary}. Give me a brief, natural response about what I'm seeing (1-2 sentences)."
                            }
                        ],
                        "max_tokens": 100,
                    },
                    headers={
                        "Authorization": f"Bearer {self.groq_api_key}",
                        "Content-Type": "application/json"
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"[Whisper] Groq response error: {e}")
        
        return detection_summary
