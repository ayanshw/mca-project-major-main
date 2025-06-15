from DTO import cameraSocketData
import time
import cv2
import numpy as np
import base64
import asyncio
# This module handles camera data management for uninitialized cameras.

uninitialized_cameras = []

def addCameraData(camera_data: cameraSocketData):
    print(f"[INFO] Adding camera data for MAC: {camera_data.mac}")
    mac_lower = camera_data.mac.lower()
    if not any(cam.mac.lower() == mac_lower for cam in uninitialized_cameras):
        uninitialized_cameras.append(camera_data)
        print(f"[INFO] Camera {camera_data.mac} added to uninitialized cameras.")
    else:
        print(f"[INFO] Camera {camera_data.mac} already exists in uninitialized cameras, updating image.")
        for cam in uninitialized_cameras:
            if cam.mac.lower() == mac_lower:
                cam.image = camera_data.image
                break
    
async def getCameraData(mac):
    mac_lower = mac.lower()
    for camera in uninitialized_cameras:
        if camera.mac.lower() == mac_lower:
            return processCameraImage(camera.image)
    return None  # No camera found

        
def processCameraImage(image_data:bytes):
    # Decode base64 to bytes, then to NumPy array
    try:
        #decoded_bytes = base64.b64decode(image_data)
        image_np = np.frombuffer(image_data, np.uint8)
        image_cv = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

        if image_cv is None:
            print("[ERROR] Failed to decode image")
            return None

        # Encode back to JPEG to send as bytes
        success, encoded_img = cv2.imencode(".jpg", image_cv)
        if not success:
            print("[ERROR] Failed to encode image")
            return None

        # Encode JPEG bytes to base64 string
        base64_img = base64.b64encode(encoded_img.tobytes()).decode('utf-8')
        return base64_img

    except Exception as e:
        print(f"[ERROR] Image processing failed: {e}")
        return None
