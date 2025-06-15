from sqlmodel import SQLModel, Field
from typing import Optional
from decimal import Decimal
from datetime import datetime
from sqlalchemy import LargeBinary, Column


class CameraId(SQLModel, table=True):
    uid: Optional[int] = Field(default=None, primary_key=True, nullable=False)
    mac: str = Field(nullable=False, unique=True)


class CameraInfo(SQLModel, table=True):
    uid: Optional[int] = Field(nullable=False, primary_key=True,foreign_key="cameraid.uid")
    latitude: Decimal = Field(default=0, max_digits=9, decimal_places=6)
    longitude: Decimal = Field(default=0, max_digits=9, decimal_places=6)
    address: str= Field(nullable=False)
    plus_code: str= Field(nullable=False)


class OffenseHistory(SQLModel, table=True):
    offenseId: Optional[int] = Field(nullable=False, primary_key=True, default=None)
    uid: int = Field(nullable=False, foreign_key="cameraid.uid")
    vehicleNumber: str = Field(nullable=False)
    image: Optional[bytes] = Field(
        default=None,
        sa_column=Column(LargeBinary(length=(2**32)-1))
    )  # LONGBLOB
    timestamp: datetime = Field(nullable=False)
    offenseType: str = Field(nullable=False)
    paid: bool = Field(default=False)
    exempted: bool = Field(default=False)


class CameraUninit(SQLModel, table=True):
    uid: int = Field(nullable=False, foreign_key="cameraid.uid", primary_key=True)
    mac: str = Field(nullable=False)
    timestamp: datetime = Field(nullable=False)


class AdminTable(SQLModel, table=True):
    adminId: Optional[int] = Field(nullable=False, primary_key=True,default=None)
    name: str = Field(nullable=False)
    email: str = Field(nullable=False)
    password: str = Field(nullable=False)
    photo: Optional[bytes] = Field(
        default=None,
        sa_column=Column(LargeBinary(length=(2**20)-1))
    )  # Store photo as bytes
    type: str = Field(nullable=False)  # 'superadmin' or 'admin'
    
    
class ReviewTable(SQLModel, table=True):
    reviewNumber: Optional[int] = Field(nullable=False, primary_key=True,default=None)
    offenseId: int = Field(nullable=False, foreign_key="offensehistory.offenseId")
    adminId: Optional[int] = Field(nullable=True, foreign_key="admintable.adminId")
    reviewStatus: str = Field(nullable=False)
    reviewComments: str = Field(nullable=False)
    
    
class PaymentTable(SQLModel, table=True):
    orderNumber: Optional[int] = Field(nullable=False, primary_key=True,default=None)
    orderId: str = Field(nullable=False)  # Unique identifier for the order
    paymentId: str = Field(nullable=True)  # Unique identifier for the payment
    offenseId: int = Field(nullable=False, foreign_key="offensehistory.offenseId")
    amount: Decimal = Field(nullable=False, max_digits=10, decimal_places=2)
    paymentStatus: str = Field(nullable=False)  # 'paid', 'pending', 'failed'
    paymentTimestamp: datetime = Field(nullable=False)
    paymentMethod: str = Field(nullable=True)  # e.g., 'credit_card', 'debit_card', 'net_banking'
