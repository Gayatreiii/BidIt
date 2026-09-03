import os
import json
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Header, status
from pydantic import EmailStr
from jose import JWTError, jwt

from backend.schemas import (
    UserSignupRequest,
    UserLoginRequest,
    UserProfileResponse,
    AuthResponse,
    UpdateProfileRequest
)
from backend.database import get_db_connection

router = APIRouter(prefix="/api/auth", tags=["Auth & Profile"])

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "bidup_portfolio_intelligence_secret_key_2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7 # 7 days

def hash_password(password: str) -> str:
    # Deterministic secure salt + sha256 for self-contained zero-breakage hashing
    salt = "bidup_secure_salt_v1_"
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hash_password(plain_password) == hashed_password

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user_id(authorization: Optional[str] = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication token"
        )
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token subject")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

@router.post("/signup", response_model=AuthResponse)
def signup(req: UserSignupRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if email exists
    cursor.execute("SELECT id FROM users WHERE email = ?", (req.email.lower(),))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    user_id = str(uuid.uuid4())
    hashed_pwd = hash_password(req.password)
    
    # Insert user
    cursor.execute(
        "INSERT INTO users (id, email, hashed_password) VALUES (?, ?, ?)",
        (user_id, req.email.lower(), hashed_pwd)
    )
    
    # Insert user profile with risk tolerance and investment horizon
    exclusions_json = json.dumps(req.sector_exclusions)
    cursor.execute("""
        INSERT INTO user_profile (id, display_name, risk_tolerance, investment_horizon, sector_exclusions)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, req.display_name, req.risk_tolerance, req.investment_horizon, exclusions_json))
    
    # Initialize paper trading account with 1,000,000 INR
    cursor.execute("""
        INSERT INTO paper_trading_accounts (user_id, cash_balance)
        VALUES (?, 1000000.0)
    """, (user_id,))
    
    conn.commit()
    conn.close()
    
    token = create_access_token(data={"sub": user_id, "email": req.email.lower()})
    
    user_profile = UserProfileResponse(
        id=user_id,
        email=req.email.lower(),
        display_name=req.display_name,
        risk_tolerance=req.risk_tolerance,
        investment_horizon=req.investment_horizon,
        sector_exclusions=req.sector_exclusions,
        created_at=datetime.utcnow().isoformat()
    )
    
    return AuthResponse(access_token=token, user=user_profile)

@router.post("/login", response_model=AuthResponse)
def login(req: UserLoginRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, email, hashed_password FROM users WHERE email = ?", (req.email.lower(),))
    user_row = cursor.fetchone()
    
    if not user_row or not verify_password(req.password, user_row["hashed_password"]):
        conn.close()
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    user_id = user_row["id"]
    cursor.execute("SELECT * FROM user_profile WHERE id = ?", (user_id,))
    profile_row = cursor.fetchone()
    conn.close()
    
    if not profile_row:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    exclusions = json.loads(profile_row["sector_exclusions"]) if profile_row["sector_exclusions"] else []
    
    token = create_access_token(data={"sub": user_id, "email": req.email.lower()})
    
    user_profile = UserProfileResponse(
        id=user_id,
        email=user_row["email"],
        display_name=profile_row["display_name"],
        risk_tolerance=profile_row["risk_tolerance"],
        investment_horizon=profile_row["investment_horizon"],
        sector_exclusions=exclusions,
        created_at=profile_row["created_at"]
    )
    
    return AuthResponse(access_token=token, user=user_profile)

@router.get("/me", response_model=UserProfileResponse)
def get_current_user_profile(user_id: str = Depends(get_current_user_id)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT email FROM users WHERE id = ?", (user_id,))
    user_row = cursor.fetchone()
    if not user_row:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")
        
    cursor.execute("SELECT * FROM user_profile WHERE id = ?", (user_id,))
    profile_row = cursor.fetchone()
    conn.close()
    
    if not profile_row:
        raise HTTPException(status_code=404, detail="Profile not found")
        
    exclusions = json.loads(profile_row["sector_exclusions"]) if profile_row["sector_exclusions"] else []
    
    return UserProfileResponse(
        id=user_id,
        email=user_row["email"],
        display_name=profile_row["display_name"],
        risk_tolerance=profile_row["risk_tolerance"],
        investment_horizon=profile_row["investment_horizon"],
        sector_exclusions=exclusions,
        created_at=profile_row["created_at"]
    )

@router.put("/profile", response_model=UserProfileResponse)
def update_profile(req: UpdateProfileRequest, user_id: str = Depends(get_current_user_id)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM user_profile WHERE id = ?", (user_id,))
    profile = cursor.fetchone()
    if not profile:
        conn.close()
        raise HTTPException(status_code=404, detail="Profile not found")
        
    new_name = req.display_name if req.display_name is not None else profile["display_name"]
    new_risk = req.risk_tolerance if req.risk_tolerance is not None else profile["risk_tolerance"]
    new_horizon = req.investment_horizon if req.investment_horizon is not None else profile["investment_horizon"]
    new_exclusions = json.dumps(req.sector_exclusions) if req.sector_exclusions is not None else profile["sector_exclusions"]
    
    cursor.execute("""
        UPDATE user_profile
        SET display_name = ?, risk_tolerance = ?, investment_horizon = ?, sector_exclusions = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (new_name, new_risk, new_horizon, new_exclusions, user_id))
    
    cursor.execute("SELECT email FROM users WHERE id = ?", (user_id,))
    user_email = cursor.fetchone()["email"]
    
    conn.commit()
    conn.close()
    
    return UserProfileResponse(
        id=user_id,
        email=user_email,
        display_name=new_name,
        risk_tolerance=new_risk,
        investment_horizon=new_horizon,
        sector_exclusions=json.loads(new_exclusions) if isinstance(new_exclusions, str) else new_exclusions,
        created_at=profile["created_at"]
    )
