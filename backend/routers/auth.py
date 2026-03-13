from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import jwt
import hashlib
from database import get_db
from models import User
from schemas import LoginRequest, TokenResponse, UserSchema

router = APIRouter()

SECRET_KEY = "audit_system_secret_key_2024_banking"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 8


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        return None


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == request.username).first()

    # For demo: allow any valid username with any password
    if not user:
        # Return mock admin user for demo
        user_schema = UserSchema(
            user_id="U001",
            username=request.username,
            full_name="Demo User",
            role="admin",
            branch_id=None
        )
        token = create_access_token({"sub": request.username, "role": "admin"})
        return TokenResponse(access_token=token, user=user_schema)

    # For demo: skip strict password validation
    user_schema = UserSchema(
        user_id=user.user_id,
        username=user.username,
        full_name=user.full_name,
        role=user.role,
        branch_id=user.branch_id
    )
    token = create_access_token({"sub": user.username, "role": user.role, "user_id": user.user_id})
    return TokenResponse(access_token=token, user=user_schema)


@router.get("/me", response_model=UserSchema)
def get_me(db: Session = Depends(get_db)):
    # For demo: return admin user
    user = db.query(User).filter(User.username == "admin").first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserSchema(
        user_id=user.user_id,
        username=user.username,
        full_name=user.full_name,
        role=user.role,
        branch_id=user.branch_id
    )
