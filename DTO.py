from pydantic import BaseModel
from datetime import datetime

class CustomBaseModel(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

class LoginDTO(CustomBaseModel):
    email: str
    password: str
    
    
class OffenseCreationDTO(CustomBaseModel):
    vehicleNumber: str
    timestamp: datetime  # ISO format string
    type: str  # 'motorcycle', 'car', 'auto', 'bus', 'truck', 'van'
    mac: str  # ID of the camera that detected the offense
    offenseType: str


class CameraAddDTO(CustomBaseModel):
    uid: int
    latitude: float
    longitude: float
    address: str
    
class CameraInitDTO(CustomBaseModel):
    mac: str
 
class CameraInitResponseDTO(CustomBaseModel):
    ip: str
    port: int
    
 
 
   
class Token(CustomBaseModel):
    access_token: str
    token_type: str


class TokenData(CustomBaseModel):
    adminId: str | None = None
    
class cameraSocketData(CustomBaseModel):
    mac: str
    image: bytes
    
class RegisterDTO(CustomBaseModel):
    name: str
    email: str
    password: str
    type: str  # 'superadmin' or 'admin'
    photo: bytes | None = None
    type: str # Optional photo as bytes
    
    
class CameraCoverageDTO(CustomBaseModel):
    latitude: float
    longitude: float
    cameraId: int  # ID of the camera within the coverage area
    
class ResponseCameraDTO(CustomBaseModel):
    latitude: float
    longitude: float
    address: str
    
class OffenseSearchResponseDTO(CustomBaseModel):
    offenseId: int
    vehicleNumber: str
    image: bytes
    timestamp: str  # ISO format string
    offenseType: str
    paid: bool
    exempted: bool
    cameraData: ResponseCameraDTO
    
class CreateReviewDTO(CustomBaseModel):
    offenseId: int
    reviewStatus: str
    reviewComments: str
    
class ReviewRequestDTO(CustomBaseModel):
    offenseId: int



class GetReviewsDTO(CustomBaseModel):
    reviewNumber: int
    offenseType: str
    reviewImage: bytes
    vehicleNumber: str
    

class ReviewResponseDTO(CustomBaseModel):
    reviewNumber: int
    reviewStatus: str
    reviewComments: str
    
class CreateReviewResponseDTO(CustomBaseModel):
    reviewNumber: int
    reviewStatus: str
    reviewComments: str
    vehicleNumber: str
    
class GetReviewOpenDTO(CustomBaseModel):
    reviewNumber: int
   
    vehicleNumber: str
    offenseType: str
    reviewStatus: str
    reviewComments: str
    offense: OffenseSearchResponseDTO

class ReviewStatusUpdateDTO(CustomBaseModel):
    reviewNumber: int
    reviewStatus: str
    reviewComments: str
    
class CameraCoverageSecondDTO(CustomBaseModel):
    latitude: float
    longitude: float
    cameraId: int  # ID of the camera within the coverage area
    
class PaymentStartDTO(CustomBaseModel):
    offenseId: int  # Optional callback URL for payment status updates
    
class PaymentInitDTO(CustomBaseModel):
    orderId: str | None = None  # Optional order ID for existing payments
    offenseId: int
    apiKey: str
    amount: int  # Amount in smallest currency unit (e.g., paise for INR)
    receipt: str | None = None  # Optional receipt identifier
    callbackurl: str | None = None# Optional callback URL for payment status updates
    
class RazorpayResponseDTO(CustomBaseModel):
    razorpay_payment_id: str
    razorpay_order_id: str
    razorpay_signature: str
    
    
class PaymentStatusBulkDTO(CustomBaseModel):
    orderNumber: int
    orderId: str  # Unique identifier for the order
    paymentId: str | None = None  # Unique identifier for the payment
    offenseId: int  # ID of the offense associated with the payment
    amount: int  # Amount in smallest currency unit (e.g., paise for INR)
    paymentStatus: str 
    paymentTimestamp: str 
    paymentMethod: str | None = None  # e.g., 'credit_card', 'debit_card', 'net_banking'
