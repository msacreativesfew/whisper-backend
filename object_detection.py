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

# Lazy imports to save memory (prevents Out-of-Memory on Railway)
YOLO = None
cv2 = None
np = None

def _ensure_imports():
    global YOLO, cv2, np
    if YOLO is None:
        try:
            from ultralytics import YOLO as _YOLO
            YOLO = _YOLO
            logger.info("[Whisper] YOLOv8 imported successfully")
        except ImportError:
            logger.warning("[Whisper] YOLOv8 not installed. Install with: pip install ultralytics")
    if cv2 is None:
        try:
            import cv2 as _cv2
            import numpy as _np
            cv2 = _cv2
            np = _np
            logger.info("[Whisper] OpenCV and NumPy imported successfully")
        except ImportError:
            logger.warning("[Whisper] OpenCV/NumPy not installed.")

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
        _ensure_imports()
        self.model_size = model_size
        self.model = None
        self.class_names = {}
        self.detected_objects_cache = {}
        self.learning_memory = {}  # Remember user's custom labels
        
        if YOLO:
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
            # Don't raise, just keep self.model as None
            self.model = None

    def detect_frame(self, frame: "np.ndarray", confidence_threshold: float = 0.5) -> Dict:
        """
        Detect objects in a single frame
        """
        if self.model is None:
            return {"objects": [], "error": "Model not loaded"}

        try:
            # Run inference
            results = self.model(frame, conf=confidence_threshold, verbose=False)
            
            detected = []
            timestamp = datetime.now().isoformat()
            
            for result in results:
                boxes = result.boxes
                for box in boxes:
                    cls_id = int(box.cls[0])
                    label = self.class_names.get(cls_id, f"Object {cls_id}")
                    conf = float(box.conf[0])
                    coords = box.xyxy[0].tolist()
                    
                    obj = DetectedObject(
                        label=label,
                        confidence=conf,
                        bbox=(int(coords[0]), int(coords[1]), int(coords[2]), int(coords[3])),
                        timestamp=timestamp
                    )
                    detected.append(obj.to_dict())
            
            return {
                "objects": detected,
                "count": len(detected),
                "timestamp": timestamp
            }
        except Exception as e:
            logger.error(f"[Whisper] Detection error: {e}")
            return {"objects": [], "error": str(e)}
