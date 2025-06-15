from datetime import datetime, timedelta
from jose import JWTError, jwt
from DTO import TokenData  # TokenData should now have: adminId: str | None = None
from dotenv import load_dotenv
import os

load_dotenv()

# JWT configuration
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(data: dict, expires_delta: timedelta = None):
    """
    Creates a JWT token embedding adminId (as 'sub') with expiration.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_access_token(token: str, credentials_exception):
    """
    Verifies the token and extracts the adminId from the 'sub' claim.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        admin_id: str = payload.get("sub")
        if admin_id is None:
            raise credentials_exception
        return TokenData(adminId=admin_id)
    except JWTError:
        raise credentials_exception
