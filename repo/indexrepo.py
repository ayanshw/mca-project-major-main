from database import dep
from models import OffenseHistory, AdminTable, CameraInfo, ReviewTable, PaymentTable
from fastapi import HTTPException
from DTO import LoginDTO,RazorpayResponseDTO, RegisterDTO,PaymentInitDTO, PaymentStartDTO, CameraCoverageDTO,CameraCoverageSecondDTO, OffenseSearchResponseDTO, ResponseCameraDTO,CreateReviewResponseDTO
from sqlmodel import select
import hashing
from fastapi import HTTPException, Response
from datetime import timedelta
# from datetime import timedelta
from jwt import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
import base64
import razorpayhandler
import datetime



def searchVehicle(id: str, session: dep) -> list[OffenseSearchResponseDTO]:
    offense = select(OffenseHistory).where(OffenseHistory.vehicleNumber == id)
    OffenseList = session.exec(offense).all()
    if not OffenseList:
        raise HTTPException(status_code=204, detail="Vehicle not found")
    else:
        offenselist= []
        for offense_obj in OffenseList:
            # If offense_obj is a tuple, unpack it
            if isinstance(offense_obj, tuple):
                offense_obj = offense_obj[0]
            cameradata = select(CameraInfo).where(CameraInfo.uid == offense_obj.uid)
            cameraInfo = session.exec(cameradata).first()
            if cameraInfo:
                # Encode image if it's bytes
                image_data = offense_obj.image
                if isinstance(image_data, bytes):
                    image_data = base64.b64encode(image_data).decode('utf-8')
                offenselist.append(OffenseSearchResponseDTO(
                    offenseId=offense_obj.offenseId,
                    vehicleNumber=offense_obj.vehicleNumber,
                    image=image_data,
                    timestamp=offense_obj.timestamp.isoformat(),
                    offenseType=offense_obj.offenseType,
                    paid=offense_obj.paid,
                    exempted=offense_obj.exempted,
                    cameraData=ResponseCameraDTO(
                        latitude=cameraInfo.latitude,
                        longitude=cameraInfo.longitude,
                        address=cameraInfo.address
                    )
                ))
        return offenselist

def login(request: LoginDTO, session: dep, response: Response):
    statement = select(AdminTable).where(AdminTable.email == request.email)
    admin = session.exec(statement).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    
    if not hashing.verify_password(request.password, admin.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(admin.adminId)},  # or use email
        expires_delta=access_token_expires
    )
    
    # Set the access token in an HTTP-only cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=access_token_expires.total_seconds(),
        secure=False,       # Set to True in production (HTTPS)
        samesite="lax"     # Or "strict" or "none"
    )
    response.set_cookie(
        key="type",
        value=str(admin.type),
        httponly=True,
        max_age=access_token_expires.total_seconds(),
        secure=False,       # Set to True in production (HTTPS)
        samesite="lax"     # Or "strict" or "none"
    )

    return {"message": "Login successful", "type": admin.type, "adminId": admin.adminId, "name": admin.name, "photo": admin.photo,
            "goto": "deployment" if admin.type =="deployer" else "verifier"}

def register(request: RegisterDTO, session: dep):
    # Check if the email is already registered
    statement = select(AdminTable).where(AdminTable.email == request.email)
    existing_admin = session.exec(statement).first()
    if existing_admin:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Hash the password
    hashed_password = hashing.get_password_hash(request.password)
    if not hashed_password:
        raise HTTPException(status_code=500, detail="Error hashing password")
       

    # Create a new admin record
    new_admin = AdminTable(
        name=request.name,
        email=request.email,
        password=hashed_password,
        type=request.type,
        photo=request.photo
    )
    session.add(new_admin)
    session.commit()
    session.refresh(new_admin)

    return {"message": "Registration successful"}

def get_camera_coverage(session: dep) -> list[CameraCoverageDTO]:
    """
    Get camera coverage data.
    """
    statement = select(CameraInfo.latitude, CameraInfo.longitude, CameraInfo.uid)
    camera_coverage = session.exec(statement).all()
    
    if not camera_coverage:
        raise HTTPException(status_code=404, detail="No camera coverage data found")
    
    return list(map(lambda x: CameraCoverageDTO(latitude=x[0], longitude=x[1], cameraId=x[2]), camera_coverage))


def create_review(request, session: dep)-> CreateReviewResponseDTO:
    """
    Create a new review for an offense.
    """
    statement = select(OffenseHistory).where(OffenseHistory.offenseId == request.offenseId)
    offense = session.exec(statement).first()
    
    if not offense:
        raise HTTPException(status_code=404, detail="Offense not found")
    
    # Create the review
    statement= select(ReviewTable).where(ReviewTable.offenseId == offense.offenseId)
    review = session.exec(statement).first()
    if review:
        if review.reviewStatus.lower()== "pending":
            raise HTTPException(status_code=400, detail="Review already exists for this offense")
        elif review.reviewStatus.lower()== "rejected":
            raise HTTPException(status_code=400, detail="Review already rejected for this offense")
        elif review.reviewStatus.lower()== "approved":
            raise HTTPException(status_code=400, detail="Review already approved for this offense")

    if not review:
        review = ReviewTable(
            offenseId=offense.offenseId,
            reviewStatus="pending",
            reviewComments="Waiting for review"
        )
        session.add(review)
        session.commit()
        session.refresh(review)
        offense.paid = False
        offense.exempted = True  # Calcuted as waiting for review
        session.add(offense)
        session.commit()
        session.refresh(offense)

        return CreateReviewResponseDTO(
            reviewNumber=review.reviewNumber,
            vehicleNumber=offense.vehicleNumber,
            reviewStatus=review.reviewStatus,
            reviewComments=review.reviewComments
        )
        

def get_camera_coverage(session: dep):
    """
    Get camera coverage data.
    """
    statement = select(CameraInfo.latitude, CameraInfo.longitude, CameraInfo.uid)
    camera_coverage = session.exec(statement).all()
    
    if not camera_coverage:
        raise HTTPException(status_code=404, detail="No camera coverage data found")

    return list(map(lambda x: CameraCoverageSecondDTO(latitude=x[0], longitude=x[1], cameraId=x[2]), camera_coverage))

def check_email(email: str, session: dep):
    """
    Check if an email is already registered.
    """
    statement = select(AdminTable).where(AdminTable.email == email)
    existing_admin = session.exec(statement).first()
    
    if existing_admin:
        raise HTTPException(status_code=400, detail="Email already registered")
    else:
        return {"message": "Email not registered"}



def init_payment(request: PaymentStartDTO, session: dep):
    statement = select(OffenseHistory).where(OffenseHistory.offenseId == request)
    offense = session.exec(statement).first()
    if not offense:
        raise HTTPException(status_code=404, detail="Offense not found")
    if offense.paid:
        raise HTTPException(status_code=400, detail="Offense already paid")
    if offense.exempted:
        raise HTTPException(status_code=400, detail="Offense exempted from payment")
    if(offense.offenseType=="road-parking"):
        amount = 1000
    elif(offense.offenseType=="no-helmet"):
        amount=5000
    
    order=razorpayhandler.create_order(amount=amount, receipt=str(offense.offenseId))
    
    # Create Razorpay order
    
        #     {
        # "id": "order_IluGWxBm9U8zJ8",
        # "entity": "order",
        # "amount": 50000,
        # "amount_paid": 0,
        # "amount_due": 50000,
        # "currency": "INR",
        # "receipt": "rcptid_11",
        # "status": "created",
        # "attempts": 0,
        # "notes": [],
        # "created_at": 1566986570
        # }
    
    if "error" in order:
        raise HTTPException(status_code=500, detail="Error creating Razorpay order")
    
    # Create payment record
    output = PaymentInitDTO(
    orderId=order["id"],  # Razorpay order ID
    apiKey=razorpayhandler.getapikey(),
    amount=order["amount"],
    offenseId=offense.offenseId,
    callbackurl="/getpaymentstatus",
    receipt=order["receipt"]
)


    new_pt= PaymentTable(
        orderId=output.orderId,
        amount=output.amount,
        offenseId=output.offenseId,
        callbackurl=output.callbackurl,
        paymentStatus= order["status"],
        paymentTimestamp= datetime.datetime.now()
    )
    session.add(new_pt)
    session.commit()
    session.refresh(new_pt)

    return output


def get_payment_status(
    razorpay_payment_id: str,
    razorpay_order_id: str,
    razorpay_signature: str,
    session: dep
):
    if razorpay_payment_id is None:
        raise HTTPException(status_code=400, detail="Invalid payment data")

    statement = select(PaymentTable).where(PaymentTable.orderId == razorpay_order_id)
    payment = session.exec(statement).first()

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    verification = razorpayhandler.verifyPaymentSignature(
        payment_id=razorpay_payment_id,
        order_id=razorpay_order_id,
        signature=razorpay_signature
    )
    if not verification:
        raise HTTPException(status_code=400, detail="Payment signature verification failed")
    # Update payment status
    
    payment_details = razorpayhandler.get_payment(payment_id=razorpay_payment_id)
    
    if payment_details["status"] == "captured":
        # Update existing payment record
        payment.paymentId = razorpay_payment_id
        payment.paymentStatus = "paid"
        payment.paymentTimestamp = datetime.datetime.now()
        payment.paymentMethod = payment_details["method"]
        session.add(payment)
        session.commit()
        session.refresh(payment)
        # Update offense status
        statement = select(OffenseHistory).where(OffenseHistory.offenseId == payment.offenseId)
        offense = session.exec(statement).first()
        if offense:
            offense.paid = True
            offense.exempted = False
            session.add(offense)
            session.commit()
            session.refresh(offense)
        return {"vehicleNumber": offense.vehicleNumber, "message": "Payment successful", "offenseId": offense.offenseId}
    
    
def get_payment_data(offense_id: int, session: dep):
    """
    Get payment data for a specific offense.
    """
    statement = select(PaymentTable).where(PaymentTable.offenseId == offense_id)
    payment = session.exec(statement).first()
    
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    return {
        "orderId": payment.orderId,
        "paymentId": payment.paymentId if payment.paymentId else None,
        "amount": payment.amount,
        "paymentStatus": payment.paymentStatus,
        "paymentTimestamp": payment.paymentTimestamp.isoformat(),
        "offenseId": payment.offenseId,
        "paymentMethod": payment.paymentMethod if hasattr(payment, 'paymentMethod') else None
    }
    
def get_comments(reviewNumber: int, session: dep):
    """
    Get review comments for a specific review number.
    """
    statement = select(ReviewTable).where(ReviewTable.offenseId == reviewNumber)
    review = session.exec(statement).first()
    
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    
    return {
        "reviewNumber": review.reviewNumber,
        "reviewStatus": review.reviewStatus,
        "reviewComments": review.reviewComments,
        "adminId": review.adminId if review.adminId else None
    }
