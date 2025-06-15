from fastapi import APIRouter, Depends, status, HTTPException, Cookie
from database import get_session
from sqlmodel import Session
from DTO import GetReviewsDTO, TokenData, GetReviewOpenDTO, ReviewStatusUpdateDTO
from oauth2 import get_current_user
from repo import hrrepo



router = APIRouter(
    tags=["verification"],
    prefix="/verification",
)

@router.get("/availablereviews", status_code=status.HTTP_200_OK)
async def available_reviews(
    session: Session = Depends(get_session),
    current_user: TokenData= Depends(get_current_user),
    admintype: str = Cookie(None, alias="type")):
    """Get available reviews for the reviewer.
    This endpoint is accessible only to users with the 'reviewer' role.
    """
    if admintype != "reviewer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource."
        )
    return await hrrepo.get_available_reviews(session)

@router.get("/review/{reviewId}", status_code=status.HTTP_200_OK)
async def get_review(
    reviewId: int,
    session: Session = Depends(get_session),
    current_user: TokenData = Depends(get_current_user),
    admintype: str = Cookie(None, alias="type")) -> GetReviewOpenDTO:
    """Get a specific review by its ID.
    This endpoint is accessible only to users with the 'reviewer' role.
    """
    if admintype != "reviewer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource."
        )
    return hrrepo.get_review_by_number(reviewId, session)

@router.post("/reviewmodify", status_code=status.HTTP_200_OK)
async def modify_review(
    review: ReviewStatusUpdateDTO,
    session: Session = Depends(get_session),
    current_user: TokenData = Depends(get_current_user),
    admintype: str = Cookie(None, alias="type")) -> dict:
    """Allow a review to be processed.
    This endpoint is accessible only to users with the 'reviewer' role.
    """
    if admintype != "reviewer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource."
        )
    hrrepo.modify_review(current_user,review, session)
    return {"message": "Review modified successfully"}


@router.get("/getallpayments", status_code=status.HTTP_200_OK)
async def get_all_payments(
    session: Session = Depends(get_session),
    current_user: TokenData = Depends(get_current_user),
    admintype: str = Cookie(None, alias="type")) -> list:
    """Get all payments made by the user.
    This endpoint is accessible only to users with the 'reviewer' role.
    """
    if admintype != "reviewer":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource."
        )
    return hrrepo.get_all_payments( session)
