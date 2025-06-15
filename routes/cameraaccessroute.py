from fastapi import APIRouter, Depends, status,WebSocket, Request, HTTPException, Cookie, WebSocketDisconnect, Response
from sqlmodel import Session
from database import get_session
from DTO import CameraAddDTO, CameraInitDTO,TokenData, CameraInitResponseDTO
from repo import cameraaccessrepo
import camsocket
import asyncio
from oauth2 import get_current_user
import processing.udpserver

router = APIRouter(
    tags=["Camera Access"],
    prefix="/cameraaccess",
)
  # Path to your auth dependency

@router.get("/getuninitcamera", status_code=status.HTTP_200_OK)
async def getUninitCamera(
    request: Request,
    session: Session = Depends(get_session),
    current_user: TokenData = Depends(get_current_user),
    admintype: str = Cookie(None, alias="type")
):
    
    # if not current_user.adminId: raise HTTPException(...)
    
   # Example of how to get type from request, if needed
    if admintype != "deployer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource."
        )
    cameradata = cameraaccessrepo.getUninitCamera(session)
    return cameradata


@router.post("/addcamera", status_code=status.HTTP_201_CREATED)
async def addCamera(
    request: CameraAddDTO,
    session: Session = Depends(get_session),
    current_user: TokenData = Depends(get_current_user),
    admintype: str = Cookie(None, alias="type")):
    
    if admintype != "deployer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource."
        )
    cameradata = cameraaccessrepo.addCamera(request, session)
    return cameradata


@router.post("/camerainit", status_code=status.HTTP_201_CREATED, response_model=CameraInitResponseDTO)
async def cameraInit(request: CameraInitDTO, response: Response, session: Session = Depends(get_session)):
    """
    Initialize a camera with the provided MAC address. If the camera already exists,
    return its existing UID. Also logs the uninitialized state unless already logged.
    """
    return cameraaccessrepo.cameraInit(request, session, response)


@router.websocket("/cameraconnect/{mac}")
async def cameraConnect(websocket: WebSocket, mac: str):
    print("Connected:", mac)
    await websocket.accept()
    try:
        flag = True
        while flag:
            # Wait for camera data
            data = await camsocket.getCameraData(mac)
            if data is None:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Camera data not available")
                flag = False
                break
            await websocket.send_text(data)  # <-- send base64 string as text
            await asyncio.sleep(1)  # Adjust interval as needed
    except WebSocketDisconnect:
        print(f"[INFO] WebSocket disconnected by client for camera {mac}.")
    except Exception as e:
        print(f"Connection cl   osed for camera {mac}: {e}")
        try:
            await websocket.close()
        except RuntimeError:
            pass  # Already closed
        
        
@router.get("/getallcameras", status_code=status.HTTP_200_OK)
async def getAllCameras(
    request: Request,
    session: Session = Depends(get_session),
    current_user: TokenData = Depends(get_current_user),
    admintype: str = Cookie(None, alias="type")
):
    if admintype != "deployer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource."
        )
    cameradata = cameraaccessrepo.getAllCameras(session)
    return cameradata

@router.get("/getcamera/{uid}", status_code=status.HTTP_200_OK)
async def getCamera(
    request: Request,
    uid: int,
    session: Session = Depends(get_session),
    current_user: TokenData = Depends(get_current_user),
    admintype: str = Cookie(None, alias="type")
):
    if admintype != "deployer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource."
        )
    cameradata = cameraaccessrepo.getCamera(uid, session)
    if not cameradata:
        raise HTTPException(status_code=404, detail="Camera not found")
    return cameradata


@router.get("/clearcameraset", status_code=status.HTTP_200_OK)
async def clearCameraSet(
    request: Request,
    session: Session = Depends(get_session),
    current_user: TokenData = Depends(get_current_user),
    admintype: str = Cookie(None, alias="type")
):
    if admintype != "deployer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource."
        )
    processing.udpserver.clear_camera_sets()
    return {"message": "Camera sets cleared successfully."}
