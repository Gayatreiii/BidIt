from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Literal
from datetime import datetime
import uuid

# --- Module 1: Auth & User Profile Schemas ---

class UserSignupRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=6)
    display_name: str
    risk_tolerance: Literal["low", "medium", "high"] = "medium"
    investment_horizon: Literal["short", "medium", "long"] = "medium"
    sector_exclusions: List[str] = []

class UserLoginRequest(BaseModel):
    email: str
    password: str

class UserProfileResponse(BaseModel):
    id: str
    email: str
    display_name: str
    risk_tolerance: Literal["low", "medium", "high"]
    investment_horizon: Literal["short", "medium", "long"]
    sector_exclusions: List[str]
    created_at: Optional[str] = None

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfileResponse

class UpdateProfileRequest(BaseModel):
    display_name: Optional[str] = None
    risk_tolerance: Optional[Literal["low", "medium", "high"]] = None
    investment_horizon: Optional[Literal["short", "medium", "long"]] = None
    sector_exclusions: Optional[List[str]] = None

# --- Stocks Reference ---

class StockItem(BaseModel):
    ticker: str
    name: str
    sector: str
    industry: str
    market_cap_category: Literal["large_cap", "mid_cap", "small_cap"]
    esg_score: float = 70.0
    risk_level: Literal["low", "medium", "high"]

# --- Module 2: Portfolio Sync Schemas ---

class PortfolioHoldingItem(BaseModel):
    ticker: str
    quantity: float = Field(..., gt=0)
    avg_buy_price: float = Field(..., ge=0)

class PortfolioHoldingResponse(BaseModel):
    id: str
    user_id: str
    ticker: str
    name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    quantity: float
    avg_buy_price: float
    current_price: Optional[float] = None
    current_value: Optional[float] = None
    invested_value: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    unrealized_pnl_pct: Optional[float] = None
    updated_at: Optional[str] = None

class ManualHoldingAddRequest(BaseModel):
    ticker: str
    quantity: float = Field(..., gt=0)
    avg_buy_price: float = Field(..., ge=0)

class CSVImportResult(BaseModel):
    success: bool
    imported_count: int
    errors: List[str] = []
    holdings: List[PortfolioHoldingResponse] = []

class BrokerConnectStatus(BaseModel):
    broker_name: str
    status: Literal["coming_soon", "in_progress", "active"] = "coming_soon"
    message: str = "Live broker sync via Kite Connect / Upstox OAuth2 is in progress. Please use CSV/manual import."
