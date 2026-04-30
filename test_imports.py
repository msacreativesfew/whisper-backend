
import sys
import os

print("Testing imports...")
try:
    import cv2
    print("OpenCV imported")
except Exception as e:
    print(f"OpenCV failed: {e}")

try:
    import numpy as np
    print("NumPy imported")
except Exception as e:
    print(f"NumPy failed: {e}")

try:
    from i18n import i18n_router, init_translator
    print("i18n imported")
    init_translator("en")
    print("Translator initialized")
except Exception as e:
    print(f"i18n failed: {e}")

try:
    from advanced_features_api import router as advanced_features_router
    print("Advanced features imported")
except Exception as e:
    print(f"Advanced features failed: {e}")

try:
    from video_call_api import router as video_call_router
    print("Video call API imported")
except Exception as e:
    print(f"Video call API failed: {e}")

print("Import test complete!")
