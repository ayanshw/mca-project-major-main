from sqlmodel import Session, select
from models import ReviewTable, OffenseHistory, CameraInfo,PaymentTable
from fastapi import HTTPException
from DTO import GetReviewsDTO, GetReviewOpenDTO, OffenseSearchResponseDTO, ResponseCameraDTO, ReviewStatusUpdateDTO, PaymentStatusBulkDTO
import base64

async def get_available_reviews(session: Session) -> list[GetReviewsDTO]:
    statement = select(ReviewTable).where(ReviewTable.reviewStatus == "pending")
    # Fetch all reviews with status 'pending'
    reviews = session.exec(statement).all()
    if not reviews:
        raise HTTPException(status_code=204, detail="No pending reviews found")
    else:
        result = []
        for review in reviews:
            # Convert each ReviewTable instance to GetReviewsDTO
            statement = select(OffenseHistory.vehicleNumber, OffenseHistory.offenseType, OffenseHistory.image).where(OffenseHistory.offenseId == review.offenseId)
            vehicle_number, offense_type, image  = session.exec(statement).first()
            # Encode image if it's bytes
            if isinstance(image, bytes):
                image = base64.b64encode(image).decode('utf-8')
            result.append(
                GetReviewsDTO(
                    reviewNumber=review.reviewNumber,
                    reviewImage= image,
                    vehicleNumber=vehicle_number,
                    offenseType=offense_type
                )
            )
        # Return a list of GetReviewsDTO instances
        return result
    

def get_review_by_number(review_number: int, session: Session) -> GetReviewsDTO:
    statement = select(ReviewTable).where(ReviewTable.reviewNumber == review_number)
    review = session.exec(statement).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    # Fetch the corresponding offense details
    statement = select(OffenseHistory).where(OffenseHistory.offenseId == review.offenseId)
    offense = session.exec(statement).first()

    if not offense:
        raise HTTPException(status_code=404, detail="Offense not found")

    # Fetch the corresponding camera details
    statement = select(CameraInfo).where(CameraInfo.uid == offense.uid)
    camera = session.exec(statement).first()

    imageB64 = offense.image
    if isinstance(imageB64, bytes):
        imageB64 = base64.b64encode(imageB64).decode('utf-8')

    return GetReviewOpenDTO(
        reviewNumber=review.reviewNumber,
        vehicleNumber=offense.vehicleNumber,
        offenseType=offense.offenseType,
        reviewStatus=review.reviewStatus,
        reviewComments=review.reviewComments,
        offense= OffenseSearchResponseDTO(
            offenseId=offense.offenseId,
            vehicleNumber=offense.vehicleNumber,
            image=imageB64,
            timestamp=offense.timestamp.isoformat(),  # Convert datetime to ISO format string
            offenseType=offense.offenseType,
            paid=offense.paid,
            exempted=offense.exempted,
            cameraData=ResponseCameraDTO(
                latitude=camera.latitude,
                longitude=camera.longitude,
                address=camera.address
            )
        )
    )

def modify_review(current_user,review: ReviewStatusUpdateDTO, session: Session) -> None:
    statement = select(ReviewTable).where(ReviewTable.reviewNumber == review.reviewNumber)
    existing_review = session.exec(statement).first()

    if not existing_review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    # Update the review status and comments
    if review.reviewStatus:
        if review.reviewStatus not in ["approved", "rejected"]:
            raise HTTPException(status_code=400, detail="Invalid review status")
        existing_review.reviewStatus = review.reviewStatus

    if review.reviewComments:
        existing_review.reviewComments = review.reviewComments
    existing_review.adminId = current_user.adminId  # Set the reviewer ID to the current user's ID

    session.add(existing_review)
    session.commit()
    session.refresh(existing_review)
    statement = select(OffenseHistory).where(OffenseHistory.offenseId == existing_review.offenseId)
    offense = session.exec(statement).first()
    if not offense:
        raise HTTPException(status_code=404, detail="Offense not found")
    # Update the offense status based on the review status
    if existing_review.reviewStatus == "approved":
        offense.paid = True
        offense.exempted = True
    elif existing_review.reviewStatus == "rejected":
        offense.paid = False
        offense.exempted = False
    
    session.add(offense)
    session.commit()
    session.refresh(offense)
    
    
def get_all_payments(session: Session) -> list[PaymentTable]:
    statement = select(PaymentTable)
    payments = session.exec(statement).all()
    
    if not payments:
        raise HTTPException(status_code=204, detail="No payments found")
    
    result = []
    for payment in payments:
        result.append(
            PaymentStatusBulkDTO(
                orderNumber=payment.orderNumber,
                orderId=payment.orderId,
                paymentId=payment.paymentId,
                offenseId=payment.offenseId,
                amount=payment.amount if hasattr(payment, 'amount') else None,  # Handle optional amount field
                paymentMethod= payment.paymentMethod if hasattr(payment, 'paymentMethod') else None,
                paymentStatus=payment.paymentStatus if hasattr(payment, 'paymentStatus') else None,
                paymentTimestamp=payment.paymentTimestamp.isoformat() if hasattr(payment, 'paymentTimestamp') else None  # Convert datetime to ISO format string
            )
        )
    
    return result