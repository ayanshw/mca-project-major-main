from fastapi import Request, Cookie, Depends, APIRouter
from database import get_session
from sqlmodel import Session

from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse
from oauth2 import get_current_user
from DTO import TokenData


router = APIRouter(
    tags=["Static Routes"],
)


templates = Jinja2Templates(directory="static/templates")

@router.get("/", response_class=HTMLResponse) 
async def root():
    return FileResponse("static/index.html")  # Serve the index.html file directly

@router.get("/dashboard/")
async def dashboardfunc(
    request: Request, # Placeholder for request object if needed in the future
     current_user: TokenData= Depends(get_current_user), # Ensure user is authenticated before accessing dashboard
    adminType=Cookie(None, alias="type")
):
    if adminType == "reviewer":
        return FileResponse("static/LoginVerifier.html")
    elif adminType == "deployer":
        return FileResponse("static/LoginDeployer.html")
    return FileResponse("static/error.html")

@router.get("/register/")
async def registerfunc():
    return FileResponse("static/Register.html") 


@router.get("/viewcoverage/", response_class=HTMLResponse)
async def viewcoveragefunc(
    request: Request,
    session: Session = Depends(get_session),
   
):
   return FileResponse("static/viewcoverage.html")  # Serve the viewcoverage.html file directly
    
@router.get("/viewallcameras/", response_class=HTMLResponse)
async def viewallcamerasfunc(
    request: Request,
     current_user: TokenData= Depends(get_current_user), # Ensure user is authenticated before accessing dashboard
    adminType=Cookie(None, alias="type")
):
    if adminType =="deployer":
        return FileResponse("static/LoginDeployer_ShowCameras.html")
    else:
        return FileResponse("static/error.html")
    
    
@router.get("/camera/{uid}/", response_class=HTMLResponse)
async def viewcamera(
    request: Request,
    uid: int,
    current_user: TokenData = Depends(get_current_user),  # Ensure user is authenticated
    session: Session = Depends(get_session),
    adminType: str = Cookie(None, alias="type")
):
    if adminType != "deployer":
        return FileResponse("static/error.html")
    return FileResponse("static/showcamera.html")

@router.get("/getreview/{reviewNumber}/", response_class=FileResponse)
async def view_review(
    request: Request,
    reviewNumber: int,
    current_user: TokenData = Depends(get_current_user),  # Ensure user is authenticated
    session: Session = Depends(get_session),
    adminType: str = Cookie(None, alias="type")
):
    if adminType != "reviewer":
        return FileResponse("static/error.html")
    return FileResponse("static/LoginVerifier_ViewOffense.html")

@router.get("/search/{vehicle_num}/", response_class=HTMLResponse)
async def search_vehicle(
    request: Request,
    vehicle_num: str):
    # This function will handle the search functionality
    return FileResponse("static/search_offense.html")


@router.get("/addcameraform/", response_class=FileResponse)
async def add_camera_form(
    request: Request,
    uid: int,
    mac: str,
    current_user: TokenData = Depends(get_current_user),  # Ensure user is authenticated
    session: Session = Depends(get_session),
    adminType: str = Cookie(None, alias="type")
):
    if adminType != "deployer":
        return FileResponse("static/error.html")
    return FileResponse("static/addcamera.html")


@router.get("/allpaymentinfo/")
async def all_payment_info(
    request: Request,
    current_user: TokenData = Depends(get_current_user),  # Ensure user is authenticated
    session: Session = Depends(get_session),
    adminType: str = Cookie(None, alias="type")
):
    if adminType != "reviewer":
        return FileResponse("static/error.html")
    return FileResponse("static/paymenttable.html")

