from fastapi import APIRouter, Depends, UploadFile, status, Response,Form
from fastapi.responses import RedirectResponse
from sqlmodel import Session
from database import get_session
from DTO import LoginDTO, RegisterDTO,RazorpayResponseDTO, CameraCoverageDTO, OffenseSearchResponseDTO, ReviewRequestDTO
from repo import indexrepo

router = APIRouter(
    tags=["Index"],
)

@router.get("/{id}", status_code=status.HTTP_200_OK)
async def search_vehicle(id: str, session: Session = Depends(get_session)) -> list[OffenseSearchResponseDTO]:
    return indexrepo.searchVehicle(id.upper(),session)
    

@router.post("/registerendpoint", status_code=status.HTTP_201_CREATED)
async def register(
    email: str,
    name: str,
    password: str,
    photo: UploadFile = None,
    session: Session = Depends(get_session),
    type: str = "deployer"  # Default type is 'deployer', can be changed to 'reviewer' if needed

):
    request = RegisterDTO(
        name=name,
        type=type,
        email=email,
        password=password,
        photo=photo.file.read() if photo else None
    )
    return indexrepo.register(request, session)


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(request: LoginDTO, response: Response, session: Session = Depends(get_session)):
    admin_id = indexrepo.login(request, session, response)
    return admin_id



@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    response.delete_cookie("type")
    return {"message": "Logged out"}


@router.post("/getcameracoveragemap", status_code=status.HTTP_200_OK)
async def get_camera_coverage(session: Session = Depends(get_session)) -> list[CameraCoverageDTO]:
    """
    Get camera coverage data.
    """
    return indexrepo.get_camera_coverage(session)

@router.post("/createreview", status_code=status.HTTP_201_CREATED)
async def create_review(
    request: ReviewRequestDTO,
    session: Session = Depends(get_session)
):
    """
    Create a new review for an offense.
    """
    return indexrepo.create_review(request, session)

@router.get("/checkemail/{email}", status_code=status.HTTP_200_OK)
async def check_email(email: str, session: Session = Depends(get_session)):
    """
    Check if an email is already registered.
    """
    return indexrepo.check_email(email, session)


@router.post("/initpayment", status_code=status.HTTP_201_CREATED)
async def init_payment(
    offense_id: int,
    session: Session = Depends(get_session)
):
    """
    Initialize payment for an offense.
    """
    return indexrepo.init_payment(offense_id, session)

@router.post("/getpaymentstatus", status_code=status.HTTP_200_OK, response_class=RedirectResponse)
async def get_payment_status(
    razorpay_payment_id: str = Form(...),
    razorpay_order_id: str = Form(...),
    razorpay_signature: str = Form(...),
    session: Session = Depends(get_session)
):
    """
    Get the payment status for a specific order.
    """
    out = indexrepo.get_payment_status(
        razorpay_payment_id=razorpay_payment_id,
        razorpay_order_id=razorpay_order_id,
        razorpay_signature=razorpay_signature,
        session=session
    )
    if out:
        return RedirectResponse(
            url="/search/{}".format(out["vehicleNumber"]),
            status_code=status.HTTP_303_SEE_OTHER
        )
    else:
        return RedirectResponse(
            url="/error",
            status_code=status.HTTP_303_SEE_OTHER
        )

@router.get("/getpaymentdata/{offense_id}", status_code=status.HTTP_200_OK)
async def get_payment_data(offense_id: int, session: Session = Depends(get_session)):
    """
    Get payment data for a specific offense.
    """
    return indexrepo.get_payment_data(offense_id, session)


@router.get("/getcomments/{offense_id}", status_code=status.HTTP_200_OK)
async def get_comments(offense_id: int, session: Session = Depends(get_session)):
    """
    Get comments for a specific offense.
    """
    return indexrepo.get_comments(offense_id, session)

