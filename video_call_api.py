"""
Video Call with Real-time Object Detection API
Integrated with Whisper for intelligent voice responses about detected objects
Completely free - no API cost for object detection (runs locally)
"""

import os
import json
import uuid
from datetime import datetime
from typing import Optional, Dict
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
import logging
import asyncio

from object_detection import ObjectDetector, VideoCameraManager, RealTimeDetectionProcessor
from models import get_db, DetectionHistory, UserDetectionMemory

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/video", tags=["video_calls"])


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class StartVideoCallRequest(BaseModel):
    user_id: str
    session_id: Optional[str] = None  # Will be generated if not provided
    camera: str = "front"  # "front" or "back"


class StartVideoCallResponse(BaseModel):
    session_id: str
    status: str
    message: str
    camera: str


class DetectionSummaryResponse(BaseModel):
    session_id: str
    summary: str
    detected_objects: Dict
    total_detections: int
    camera_used: str
    processing_time: float
    saved: bool


class RememberObjectRequest(BaseModel):
    user_id: str
    object_label: str  # Original detection label (e.g., "laptop")
    user_name: str  # What user calls it (e.g., "My MacBook")
    custom_info: Optional[str] = None


class GetMemorizedObjectsResponse(BaseModel):
    user_id: str
    total_remembered: int
    objects: Dict


class SwitchCameraRequest(BaseModel):
    session_id: str
    user_id: str


# ============================================================================
# GLOBAL STATE (simplified for demo - use Redis for production)
# ============================================================================

active_sessions = {}  # session_id -> {detector, camera, start_time}


# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.post("/start", response_model=StartVideoCallResponse)
async def start_video_call(request: StartVideoCallRequest):
    """
    Start a video call with object detection
    
    **COMPLETELY FREE** - Uses local YOLOv8 (no API calls)
    
    Args:
        user_id: User identifier
        session_id: Optional session ID (auto-generated if not provided)
        camera: "front" or "back"
    
    Returns:
        Session info with streaming capability
    """
    try:
        session_id = request.session_id or str(uuid.uuid4())
        
        # Initialize detector and camera (runs locally on device)
        detector = ObjectDetector(model_size="nano")  # nano = fastest
        camera = VideoCameraManager()
        camera.initialize_cameras()
        
        if camera.active_camera is None:
            raise HTTPException(status_code=400, detail="No camera available")
        
        # Switch camera if requested
        if request.camera == "back" and camera.camera_name == "front":
            camera.switch_camera()
        
        # Store session
        active_sessions[session_id] = {
            "user_id": request.user_id,
            "detector": detector,
            "camera": camera,
            "start_time": datetime.now(),
            "camera_name": camera.camera_name,
        }
        
        logger.info(f"[Whisper] Started video call session {session_id} for user {request.user_id}")
        
        return StartVideoCallResponse(
            session_id=session_id,
            status="active",
            message="Video call started - object detection ready",
            camera=camera.camera_name
        )
    
    except Exception as e:
        logger.error(f"[Whisper] Video call start error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect/{session_id}", response_model=DetectionSummaryResponse)
async def run_detection(
    session_id: str,
    duration: int = 5,  # Process 5 seconds of video
    db = Depends(get_db)
):
    """
    Run object detection for the video call session
    
    **ZERO API COST** - All processing happens locally on your device
    
    Args:
        session_id: Active video call session
        duration: How many seconds to process (default 5)
    
    Returns:
        Summary of detected objects ready for Whisper to speak
    """
    try:
        session = active_sessions.get(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        user_id = session["user_id"]
        detector = session["detector"]
        camera = session["camera"]
        
        # Load user's remembered objects (personalization)
        try:
            memories = db.query(UserDetectionMemory).filter_by(user_id=user_id).all()
            for memory in memories:
                detector.learning_memory[memory.object_label] = {
                    "user_name": memory.user_name,
                    "custom_info": memory.custom_info,
                    "learned_at": memory.created_at.isoformat()
                }
        except:
            pass  # Continue without memory if DB fails
        
        # Process video stream (runs entirely locally)
        all_detections = {}
        start_time = datetime.now()
        frame_count = 0
        
        try:
            while (datetime.now() - start_time).total_seconds() < duration:
                frame = camera.get_frame()
                if frame is None:
                    await asyncio.sleep(0.033)
                    continue
                
                # Detect objects in frame (YOLOv8 inference - NO API CALLS)
                result = detector.detect_frame(frame)
                
                if result["objects"]:
                    for obj in result["objects"]:
                        label = obj["label"]
                        if label not in all_detections:
                            all_detections[label] = []
                        all_detections[label].append(obj)
                
                frame_count += 1
                await asyncio.sleep(0.033)  # ~30 FPS
        
        finally:
            camera.release()
        
        # Create natural language summary
        if all_detections:
            objects_list = [obj for objects in all_detections.values() for obj in objects]
            summary = detector.create_summary(objects_list)
            total_detections = len(objects_list)
        else:
            summary = "I don't see any recognizable objects right now"
            objects_list = []
            total_detections = 0
        
        # Save to database for history
        processing_time = (datetime.now() - start_time).total_seconds()
        try:
            detection_record = DetectionHistory(
                user_id=user_id,
                session_id=session_id,
                detected_objects=json.dumps(all_detections),
                summary=summary,
                total_detections=total_detections,
                processing_time=processing_time,
                camera_used=camera.camera_name
            )
            db.add(detection_record)
            db.commit()
            saved = True
        except Exception as e:
            logger.warning(f"[Whisper] Failed to save detection history: {e}")
            saved = False
        
        logger.info(f"[Whisper] Detection complete: {total_detections} objects in {processing_time:.2f}s")
        
        return DetectionSummaryResponse(
            session_id=session_id,
            summary=summary,  # Ready for Whisper to speak!
            detected_objects=all_detections,
            total_detections=total_detections,
            camera_used=camera.camera_name,
            processing_time=processing_time,
            saved=saved
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Whisper] Detection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/switch-camera")
async def switch_camera(request: SwitchCameraRequest):
    """
    Switch between front and back camera during video call
    
    Args:
        session_id: Active video call session
        user_id: User identifier (for verification)
    
    Returns:
        New camera status
    """
    try:
        session = active_sessions.get(request.session_id)
        if not session or session["user_id"] != request.user_id:
            raise HTTPException(status_code=404, detail="Session not found or unauthorized")
        
        camera = session["camera"]
        success = camera.switch_camera()
        
        if success:
            session["camera_name"] = camera.camera_name
            return {
                "success": True,
                "camera": camera.camera_name,
                "message": f"Switched to {camera.camera_name} camera"
            }
        else:
            return {
                "success": False,
                "message": "Could not switch camera - other camera not available"
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Whisper] Camera switch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/remember-object")
async def remember_object(request: RememberObjectRequest, db = Depends(get_db)):
    """
    Remember a custom label for detected objects
    
    User says: "That's my MacBook"
    Whisper remembers: laptop -> "My MacBook"
    
    Next time Whisper detects a laptop, it says:
    "I see my MacBook" instead of just "laptop"
    
    **Completely free** - Just database storage
    
    Args:
        user_id: User identifier
        object_label: Original label (e.g., "laptop")
        user_name: Custom name (e.g., "My MacBook Pro")
        custom_info: Extra context (e.g., "silver 16-inch")
    
    Returns:
        Confirmation of saved memory
    """
    try:
        # Check if already exists
        existing = db.query(UserDetectionMemory).filter_by(
            user_id=request.user_id,
            object_label=request.object_label
        ).first()
        
        if existing:
            # Update
            existing.user_name = request.user_name
            existing.custom_info = request.custom_info
            existing.updated_at = datetime.utcnow()
        else:
            # Create new
            memory = UserDetectionMemory(
                user_id=request.user_id,
                object_label=request.object_label,
                user_name=request.user_name,
                custom_info=request.custom_info
            )
            db.add(memory)
        
        db.commit()
        
        logger.info(f"[Whisper] Remembered for {request.user_id}: {request.object_label} = {request.user_name}")
        
        return {
            "success": True,
            "message": f"Remembered: {request.object_label} as '{request.user_name}'",
            "object_label": request.object_label,
            "user_name": request.user_name
        }
    
    except Exception as e:
        logger.error(f"[Whisper] Remember object error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/remembered-objects/{user_id}", response_model=GetMemorizedObjectsResponse)
async def get_remembered_objects(user_id: str, db = Depends(get_db)):
    """
    Get all objects the user has customized labels for
    
    Returns all the memories so they persist across sessions
    
    Args:
        user_id: User identifier
    
    Returns:
        List of all remembered objects
    """
    try:
        memories = db.query(UserDetectionMemory).filter_by(user_id=user_id).all()
        
        objects = {
            memory.object_label: {
                "user_name": memory.user_name,
                "custom_info": memory.custom_info,
                "learned_at": memory.created_at.isoformat()
            }
            for memory in memories
        }
        
        return GetMemorizedObjectsResponse(
            user_id=user_id,
            total_remembered=len(objects),
            objects=objects
        )
    
    except Exception as e:
        logger.error(f"[Whisper] Get remembered objects error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/end/{session_id}")
async def end_video_call(session_id: str):
    """
    End the video call and clean up resources
    
    Args:
        session_id: Active video call session
    
    Returns:
        Session summary
    """
    try:
        session = active_sessions.pop(session_id, None)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Release camera
        session["camera"].release()
        
        duration = (datetime.now() - session["start_time"]).total_seconds()
        
        logger.info(f"[Whisper] Ended video call session {session_id} (duration: {duration:.1f}s)")
        
        return {
            "success": True,
            "session_id": session_id,
            "duration": duration,
            "message": "Video call ended successfully"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Whisper] End video call error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/detection-history/{user_id}")
async def get_detection_history(user_id: str, limit: int = 10, db = Depends(get_db)):
    """
    Get user's detection history from past video calls
    
    Returns recent detections so you can see what you've been identifying
    
    Args:
        user_id: User identifier
        limit: Number of recent detections to return
    
    Returns:
        List of past detections
    """
    try:
        history = db.query(DetectionHistory).filter_by(
            user_id=user_id
        ).order_by(DetectionHistory.created_at.desc()).limit(limit).all()
        
        return {
            "user_id": user_id,
            "total_history": len(history),
            "history": [
                {
                    "session_id": h.session_id,
                    "summary": h.summary,
                    "total_detections": h.total_detections,
                    "camera_used": h.camera_used,
                    "processing_time": h.processing_time,
                    "created_at": h.created_at.isoformat()
                }
                for h in history
            ]
        }
    
    except Exception as e:
        logger.error(f"[Whisper] Get detection history error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
