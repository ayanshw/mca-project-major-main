import openlocationcode.openlocationcode
from database import dep
from models import CameraId,CameraUninit,CameraInfo
from fastapi import HTTPException, status
from DTO import CameraAddDTO, CameraInitDTO, CameraInitResponseDTO
from sqlmodel import select
import datetime
import os,socket,requests
from dotenv import load_dotenv
from sqlalchemy.exc import IntegrityError

load_dotenv()

def getIP():
    ip= "0.0.0.0"
    
    if ip != "0.0.0.0":
        return ip
    # Determine whether to return public or private IP based on environment variable
    
    IP_TYPE = os.getenv("IP_TYPE", "PRIVATE")  # 'public' or 'private'
    if IP_TYPE == "PUBLIC":
        try:
            response = requests.get('https://api.ipify.org?format=json')
            return response.json()['ip']
        
        except requests.RequestException:
            return 'Unable to retrieve public IP'
    elif IP_TYPE == "PRIVATE":
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # Doesn't have to be reachable — just used to get the right interface
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'  # Fallback to localhost
        finally:
            s.close()
        return IP

    else:
        raise ValueError("Invalid IP_TYPE. Use 'public' or 'private'.")

from fastapi import Response


def cameraInit(cameradata: CameraInitDTO, session: dep, response: Response) -> CameraInitResponseDTO:
    # Normalize MAC
    normalized_mac = cameradata.mac.strip().replace(":", "-").lower()

    # Check if camera exists
    statement = select(CameraId).where(CameraId.mac == normalized_mac)
    camera = session.exec(statement).first()

    if not camera:
        try:
            camera = CameraId(mac=normalized_mac)
            session.add(camera)
            session.commit()
            session.refresh(camera)
        except IntegrityError:
            session.rollback()
            response.status_code = status.HTTP_200_OK
            # Another thread inserted it — refetch
            statement = select(CameraId).where(CameraId.mac == normalized_mac)
            camera = session.exec(statement).first()
    else:
        # Camera already exists
        response.status_code = status.HTTP_200_OK

    # 🔒 Log uninit only if not already there
    uninit_exists = session.exec(
        select(CameraUninit).where(CameraUninit.uid == camera.uid)
    ).first()

    if not uninit_exists:
        try:
            camera_uninit = CameraUninit(
                uid=camera.uid, mac=camera.mac, timestamp=datetime.datetime.now()
            )
            session.add(camera_uninit)
            session.commit()
        except IntegrityError:
            session.rollback()
    else:
        # Already exists — optional: update timestamp
        pass

    return CameraInitResponseDTO(
        ip=getIP(),
        port=os.getenv("UDP_PORT", "8008")
    )

    
    
def addCamera(cameradata: CameraAddDTO, session: dep):
    statement = select(CameraId).where(CameraId.uid == cameradata.uid)
    camera = session.exec(statement).first()
    if not camera:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera doesn't exist") 
    
    statement = select(CameraInfo).where(CameraInfo.uid == cameradata.uid)
    existing_camera_info = session.exec(statement).first()
    if existing_camera_info:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Camera is already initialized")
    
    
    code = openlocationcode.openlocationcode.encode(cameradata.latitude, cameradata.longitude)
    CameraInfoObj = CameraInfo(
        uid=camera.uid,
        latitude=cameradata.latitude,
        longitude=cameradata.longitude,
        address=cameradata.address,
        plus_code=code
    )
    session.add(CameraInfoObj)
    session.commit()
    session.refresh(CameraInfoObj)
    
    # Remove the camera from CameraUninit
    statement = select(CameraUninit).where(CameraUninit.uid == camera.uid)
    cameraUninit = session.exec(statement).first()
    if cameraUninit:
        session.delete(cameraUninit)
        session.commit()
    
    # Return the newly added CameraInfo
    cameradataout = session.exec(select(CameraInfo).where(CameraInfo.uid == camera.uid)).first()
    return cameradataout


def getUninitCamera(session: dep):
    statement=select(CameraUninit)
    cameraUninit=session.exec(statement).all()
    if not cameraUninit:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail="No uninitialized cameras found")
    else:
        return cameraUninit
    
def checkCameraInit(mac: str, session: dep):
    try:
        statement = select(CameraId).where(CameraId.mac == mac)
        camera = session.exec(statement).first()
        if camera:
            statement=select(CameraUninit).where(CameraUninit.uid == camera.uid)
            cameraUninit = session.exec(statement).first()
            if cameraUninit:
                return False  # Camera is uninitialized
            else:
                return True  # Camera is initialized
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")   
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error checking camera initialization: {str(e)}")
    

def getAllCameras(session: dep):

    statement = select(CameraInfo, CameraId).join(CameraId, CameraInfo.uid == CameraId.uid, isouter=True)
    cameras = session.exec(statement).all()
    if not cameras:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT, detail="No cameras found")
    # Convert each tuple to a dict
    result = []
    for cam_info, cam_id in cameras:
        result.append({
            "camera_info": cam_info.model_dump() if hasattr(cam_info, "model_dump") else cam_info.dict(),
            "camera_id": cam_id.model_dump() if hasattr(cam_id, "model_dump") else cam_id.dict() if cam_id else None
        })
    return result
    
    
    

def getCamera(uid: int, session: dep):
    try:
        statement = select(CameraInfo, CameraId).where(CameraInfo.uid == uid).join(CameraId, CameraInfo.uid == CameraId.uid, isouter=True)
        camera = session.exec(statement).first()
        if not camera:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camera not found")
        # Convert to dict
        return {
            "camera_info": camera[0].model_dump() if hasattr(camera[0], "model_dump") else camera[0].dict(),
            "camera_id": camera[1].model_dump() if hasattr(camera[1], "model_dump") else camera[1].dict() if camera[1] else None
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error retrieving camera: {str(e)}")