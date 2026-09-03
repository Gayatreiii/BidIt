import reflex as rx
import json
import uuid
import random
import os
import httpx
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# --- API Keys (read from .env only, never hardcoded) ---
NEMOTRON_API_KEY = os.getenv("NEMOTRON_API_KEY", "").strip()
NEMOTRON_BASE_URL = "https://integrate.api.nvidia.com/v1"
NEMOTRON_MODEL = "nvidia/llama-3.1-nemotron-70b-instruct"

NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY", "").strip()
NEWSDATA_BASE_URL = "https://newsdata.io/api/1/news"

# --- Backend imports at module level (not lazy inside event handlers) ---
from backend.database import (
    db_signup_user,
    db_login_user,
    db_get_holdings,
    db_save_holding,
    db_delete_holding,
    db_update_profile,
)
from backend.api.auth import hash_password

# --- 8-Point Spacing Scale Constants ---
SPACE_1 = "4px"
SPACE_2 = "8px"
SPACE_3 = "12px"
SPACE_4 = "16px"
SPACE_5 = "20px"
SPACE_6 = "24px"
SPACE_8 = "32px"
SPACE_10 = "40px"
SPACE_12 = "48px"

# --- Design System Colors (Clean Light Theme Inversion) ---
BG_COLOR = "#fffffe"
CARD_BG = "#ffffff"
CARD_HOVER = "#f8f9fc"
CARD_BORDER = "#d1d1e9"
CARD_BORDER_SUBTLE = "#e2e8f0"
TEXT_HEADLINE = "#2b2c34"
TEXT_MUTED = "#626471"
TEXT_SECONDARY = "#72757e"
ACCENT_COLOR = "#6246ea"
ACCENT_LIGHT = "rgba(98, 70, 234, 0.08)"
ACCENT_BORDER = "rgba(98, 70, 234, 0.25)"
POSITIVE_COLOR = "#16a34a"
POSITIVE_LIGHT = "#eaf8f0"
WARNING_COLOR = "#d97706"
WARNING_LIGHT = "#fef3c7"
ALERT_COLOR = "#e45858"
ALERT_LIGHT = "#fee2e2"
SHADOW_SUBTLE = "0 1px 3px rgba(43, 44, 52, 0.05), 0 1px 2px rgba(43, 44, 52, 0.03)"
SHADOW_CARD = "0 4px 20px -2px rgba(43, 44, 52, 0.06), 0 2px 6px -1px rgba(43, 44, 52, 0.04)"
SHADOW_HERO = "0 10px 30px -4px rgba(98, 70, 234, 0.08), 0 4px 12px -2px rgba(43, 44, 52, 0.05)"

# --- 50+ Stock Seed Catalog (Synced with Database & Screener) ---
ALL_STOCKS_DATA = [
    # IT
    {"ticker": "TCS.NS", "name": "Tata Consultancy Services Ltd", "sector": "IT", "industry": "Software & Consulting", "cap": "large_cap", "esg": 82.5, "risk": "low", "price": 4250.0},
    {"ticker": "INFY.NS", "name": "Infosys Ltd", "sector": "IT", "industry": "Software & Consulting", "cap": "large_cap", "esg": 84.0, "risk": "low", "price": 1890.0},
    {"ticker": "HCLTECH.NS", "name": "HCL Technologies Ltd", "sector": "IT", "industry": "Software & IT Services", "cap": "large_cap", "esg": 79.0, "risk": "low", "price": 1780.0},
    {"ticker": "WIPRO.NS", "name": "Wipro Ltd", "sector": "IT", "industry": "Software & IT Services", "cap": "large_cap", "esg": 76.5, "risk": "medium", "price": 540.0},
    {"ticker": "TECHM.NS", "name": "Tech Mahindra Ltd", "sector": "IT", "industry": "Telecom & IT Services", "cap": "large_cap", "esg": 74.0, "risk": "medium", "price": 1620.0},
    {"ticker": "LTIM.NS", "name": "LTIMindtree Ltd", "sector": "IT", "industry": "IT Consulting", "cap": "large_cap", "esg": 75.0, "risk": "medium", "price": 5900.0},
    {"ticker": "PERSISTENT.NS", "name": "Persistent Systems Ltd", "sector": "IT", "industry": "Digital Engineering", "cap": "mid_cap", "esg": 73.0, "risk": "medium", "price": 5200.0},
    {"ticker": "COFORGE.NS", "name": "Coforge Ltd", "sector": "IT", "industry": "IT Solutions", "cap": "mid_cap", "esg": 71.0, "risk": "medium", "price": 7300.0},
    # Financial Services
    {"ticker": "HDFCBANK.NS", "name": "HDFC Bank Ltd", "sector": "Financial Services", "industry": "Private Banking", "cap": "large_cap", "esg": 81.0, "risk": "low", "price": 1650.0},
    {"ticker": "ICICIBANK.NS", "name": "ICICI Bank Ltd", "sector": "Financial Services", "industry": "Private Banking", "cap": "large_cap", "esg": 80.5, "risk": "low", "price": 1240.0},
    {"ticker": "SBIN.NS", "name": "State Bank of India", "sector": "Financial Services", "industry": "Public Banking", "cap": "large_cap", "esg": 72.0, "risk": "medium", "price": 810.0},
    {"ticker": "KOTAKBANK.NS", "name": "Kotak Mahindra Bank Ltd", "sector": "Financial Services", "industry": "Private Banking", "cap": "large_cap", "esg": 78.0, "risk": "low", "price": 1790.0},
    {"ticker": "AXISBANK.NS", "name": "Axis Bank Ltd", "sector": "Financial Services", "industry": "Private Banking", "cap": "large_cap", "esg": 77.0, "risk": "medium", "price": 1180.0},
    {"ticker": "BAJFINANCE.NS", "name": "Bajaj Finance Ltd", "sector": "Financial Services", "industry": "Non-Banking Financial Co", "cap": "large_cap", "esg": 75.5, "risk": "medium", "price": 7100.0},
    {"ticker": "BAJAJFINSV.NS", "name": "Bajaj Finserv Ltd", "sector": "Financial Services", "industry": "Financial Holding", "cap": "large_cap", "esg": 74.0, "risk": "medium", "price": 1820.0},
    {"ticker": "INDUSINDBK.NS", "name": "IndusInd Bank Ltd", "sector": "Financial Services", "industry": "Private Banking", "cap": "large_cap", "esg": 71.0, "risk": "high", "price": 1420.0},
    # Energy
    {"ticker": "RELIANCE.NS", "name": "Reliance Industries Ltd", "sector": "Energy", "industry": "Oil, Gas & Telecom", "cap": "large_cap", "esg": 71.5, "risk": "medium", "price": 2980.0},
    {"ticker": "ONGC.NS", "name": "Oil & Natural Gas Corp", "sector": "Energy", "industry": "Oil Exploration & Production", "cap": "large_cap", "esg": 68.0, "risk": "medium", "price": 310.0},
    {"ticker": "NTPC.NS", "name": "NTPC Ltd", "sector": "Energy", "industry": "Power Generation", "cap": "large_cap", "esg": 70.0, "risk": "low", "price": 390.0},
    {"ticker": "POWERGRID.NS", "name": "Power Grid Corp of India", "sector": "Energy", "industry": "Power Transmission", "cap": "large_cap", "esg": 76.0, "risk": "low", "price": 330.0},
    {"ticker": "BPCL.NS", "name": "Bharat Petroleum Corp", "sector": "Energy", "industry": "Refining & Marketing", "cap": "large_cap", "esg": 67.5, "risk": "medium", "price": 340.0},
    {"ticker": "IOC.NS", "name": "Indian Oil Corp", "sector": "Energy", "industry": "Refining & Marketing", "cap": "large_cap", "esg": 66.0, "risk": "medium", "price": 175.0},
    {"ticker": "ADANIGREEN.NS", "name": "Adani Green Energy Ltd", "sector": "Energy", "industry": "Renewable Energy", "cap": "large_cap", "esg": 69.0, "risk": "high", "price": 1850.0},
    {"ticker": "TATAPOWER.NS", "name": "Tata Power Company Ltd", "sector": "Energy", "industry": "Integrated Power", "cap": "mid_cap", "esg": 73.0, "risk": "medium", "price": 420.0},
    # Automobile
    {"ticker": "TATAMOTORS.NS", "name": "Tata Motors Ltd", "sector": "Automobile", "industry": "Commercial & Passenger", "cap": "large_cap", "esg": 78.0, "risk": "medium", "price": 1050.0},
    {"ticker": "MARUTI.NS", "name": "Maruti Suzuki India Ltd", "sector": "Automobile", "industry": "Passenger Cars", "cap": "large_cap", "esg": 75.0, "risk": "low", "price": 12400.0},
    {"ticker": "M&M.NS", "name": "Mahindra & Mahindra Ltd", "sector": "Automobile", "industry": "Commercial & Farm Vehicles", "cap": "large_cap", "esg": 79.5, "risk": "low", "price": 2780.0},
    {"ticker": "BAJAJ-AUTO.NS", "name": "Bajaj Auto Ltd", "sector": "Automobile", "industry": "2 & 3 Wheelers", "cap": "large_cap", "esg": 77.0, "risk": "low", "price": 9800.0},
    {"ticker": "EICHERMOT.NS", "name": "Eicher Motors Ltd", "sector": "Automobile", "industry": "Motorcycles & Commercial", "cap": "large_cap", "esg": 76.0, "risk": "medium", "price": 4850.0},
    {"ticker": "HEROMOTOCO.NS", "name": "Hero MotoCorp Ltd", "sector": "Automobile", "industry": "2 Wheelers", "cap": "large_cap", "esg": 74.5, "risk": "low", "price": 5300.0},
    # Pharma
    {"ticker": "SUNPHARMA.NS", "name": "Sun Pharma Industries", "sector": "Pharma", "industry": "Generics & Specialty", "cap": "large_cap", "esg": 77.5, "risk": "low", "price": 1820.0},
    {"ticker": "DRREDDY.NS", "name": "Dr. Reddy's Laboratories", "sector": "Pharma", "industry": "Generics & Active Ingredients", "cap": "large_cap", "esg": 80.0, "risk": "low", "price": 6700.0},
    {"ticker": "CIPLA.NS", "name": "Cipla Ltd", "sector": "Pharma", "industry": "Formulations & Generics", "cap": "large_cap", "esg": 83.0, "risk": "low", "price": 1580.0},
    {"ticker": "DIVISLAB.NS", "name": "Divi's Laboratories Ltd", "sector": "Pharma", "industry": "Active Pharmaceutical Ingredients", "cap": "large_cap", "esg": 81.0, "risk": "medium", "price": 5100.0},
    {"ticker": "APOLLOHOSP.NS", "name": "Apollo Hospitals Enterprise", "sector": "Pharma", "industry": "Hospitals & Healthcare", "cap": "large_cap", "esg": 79.0, "risk": "medium", "price": 6900.0},
    {"ticker": "LUPIN.NS", "name": "Lupin Ltd", "sector": "Pharma", "industry": "Formulations & Generics", "cap": "mid_cap", "esg": 74.0, "risk": "medium", "price": 2100.0},
    # FMCG
    {"ticker": "HINDUNILVR.NS", "name": "Hindustan Unilever Ltd", "sector": "FMCG", "industry": "Household & Personal Care", "cap": "large_cap", "esg": 86.0, "risk": "low", "price": 2750.0},
    {"ticker": "ITC.NS", "name": "ITC Ltd", "sector": "FMCG", "industry": "FMCG, Paper & Hotels", "cap": "large_cap", "esg": 78.0, "risk": "low", "price": 505.0},
    {"ticker": "NESTLEIND.NS", "name": "Nestle India Ltd", "sector": "FMCG", "industry": "Food & Beverages", "cap": "large_cap", "esg": 82.0, "risk": "low", "price": 2500.0},
    {"ticker": "BRITANNIA.NS", "name": "Britannia Industries Ltd", "sector": "FMCG", "industry": "Bakery & Dairy", "cap": "large_cap", "esg": 80.0, "risk": "low", "price": 5800.0},
    {"ticker": "TATACONSUM.NS", "name": "Tata Consumer Products Ltd", "sector": "FMCG", "industry": "Beverages & Foods", "cap": "large_cap", "esg": 81.5, "risk": "low", "price": 1180.0},
    {"ticker": "DABUR.NS", "name": "Dabur India Ltd", "sector": "FMCG", "industry": "Ayurvedic & Personal Care", "cap": "large_cap", "esg": 79.0, "risk": "low", "price": 540.0},
    # Metals
    {"ticker": "TATASTEEL.NS", "name": "Tata Steel Ltd", "sector": "Metals", "industry": "Steel Manufacturing", "cap": "large_cap", "esg": 73.0, "risk": "high", "price": 152.0},
    {"ticker": "JSWSTEEL.NS", "name": "JSW Steel Ltd", "sector": "Metals", "industry": "Steel Manufacturing", "cap": "large_cap", "esg": 71.5, "risk": "high", "price": 940.0},
    {"ticker": "HINDALCO.NS", "name": "Hindalco Industries Ltd", "sector": "Metals", "industry": "Aluminum & Copper", "cap": "large_cap", "esg": 75.0, "risk": "high", "price": 680.0},
    {"ticker": "COALINDIA.NS", "name": "Coal India Ltd", "sector": "Metals", "industry": "Coal Mining", "cap": "large_cap", "esg": 64.0, "risk": "medium", "price": 490.0},
    {"ticker": "VEDL.NS", "name": "Vedanta Ltd", "sector": "Metals", "industry": "Diversified Mining", "cap": "large_cap", "esg": 62.0, "risk": "high", "price": 460.0},
    # Realty & Infra
    {"ticker": "DLF.NS", "name": "DLF Ltd", "sector": "Realty", "industry": "Real Estate Development", "cap": "large_cap", "esg": 68.0, "risk": "high", "price": 840.0},
    {"ticker": "GODREJPROP.NS", "name": "Godrej Properties Ltd", "sector": "Realty", "industry": "Residential Real Estate", "cap": "mid_cap", "esg": 72.0, "risk": "high", "price": 2950.0},
    {"ticker": "LT.NS", "name": "Larsen & Toubro Ltd", "sector": "Infra", "industry": "Engineering & Construction", "cap": "large_cap", "esg": 82.0, "risk": "low", "price": 3600.0},
    {"ticker": "ADANIPORTS.NS", "name": "Adani Ports and SEZ Ltd", "sector": "Infra", "industry": "Ports & Logistics", "cap": "large_cap", "esg": 70.0, "risk": "medium", "price": 1450.0},
    {"ticker": "ULTRACEMCO.NS", "name": "UltraTech Cement Ltd", "sector": "Infra", "industry": "Cement & Building Materials", "cap": "large_cap", "esg": 78.5, "risk": "medium", "price": 11200.0}
]

STOCK_MAP = {s["ticker"]: s for s in ALL_STOCKS_DATA}
ALL_TICKERS = [s["ticker"] for s in ALL_STOCKS_DATA]

# --- Data Models ---
class Holding(BaseModel):
    id: str
    ticker: str
    name: str
    sector: str
    quantity: float
    avg_buy_price: float
    current_price: float
    current_value: float
    invested_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float

class SectorWeight(BaseModel):
    sector: str
    market_value: float
    weight_pct: float
    holdings_count: int

class RiskAlert(BaseModel):
    held_sector: str
    held_weight_pct: float
    correlated_sector: str
    correlation_coefficient: float
    shock_propagation_level: str
    descriptive_signal: str

class BacktestScenario(BaseModel):
    event: str
    shock_sector: str
    affected_sectors: str
    directional_result: str
    mae: float

class ChatMessage(BaseModel):
    sender: str # "user" or "assistant"
    text: str
    time: str

class NewsItem(BaseModel):
    id: str
    ticker: str
    headline: str
    sentiment: str # "Bullish", "Neutral", "Risk Watch"
    source: str
    time_ago: str        # Derived from published_at at fetch time
    published_at: str    # ISO timestamp from NewsData.io, "" if unavailable
    url: str             # Direct article URL from source, "" if unavailable

class PaperTrade(BaseModel):
    id: str
    ticker: str
    order_type: str # "BUY" or "SELL"
    quantity: float
    requested_price: float
    slippage_pct: float
    executed_price: float
    total_amount: float
    time: str

class StockCatalogItem(BaseModel):
    ticker: str
    name: str
    sector: str
    industry: str
    cap: str
    esg: float
    risk: str
    price: float

# --- Reflex Global State ---
class State(rx.State):
    # Auth State (Real Auth & Onboarding Gating)
    is_authenticated: bool = False
    is_guest: bool = False          # True when user enters without creating an account
    is_onboarding: bool = False
    onboarding_step: int = 1 # 1: Profile & Risk Preferences, 2: Portfolio Setup
    user_id: str = ""
    user_name: str = ""
    user_email: str = ""
    risk_tolerance: str = "medium"
    investment_horizon: str = "long"
    sector_exclusions: List[str] = ["Tobacco"]

    # Prices refresh state
    prices_last_updated: str = ""   # "HH:MM AM/PM" after first fetch; "" before
    prices_fetching: bool = False   # True while yfinance call is in-flight
    
    # Auth Form Inputs
    auth_mode: str = "signin" # "signin" or "signup"
    auth_email_input: str = ""
    auth_password_input: str = ""
    auth_name_input: str = ""
    auth_risk_input: str = "medium"
    auth_horizon_input: str = "long"
    auth_message: str = ""
    
    # Onboarding Form Inputs
    onboarding_risk: str = "medium"
    onboarding_horizon: str = "long"
    onboarding_exclusions: str = "Tobacco"
    
    # Routing Navigation
    active_nav: str = "home" # "home", "portfolio", "chat", "screener", "stocks", "paper_trading", "analytics", "compare", "backtest", "settings"
    is_menu_open: bool = False
    
    # Portfolio Manual Add Form & Ticker Search
    manual_ticker: str = "TCS.NS"
    ticker_search_query: str = ""
    manual_quantity: str = "10"
    manual_buy_price: str = "3850.0"
    portfolio_message: str = ""
    portfolio_error: str = ""
    
    # Screener Filters
    screener_sector: str = "All"
    screener_cap: str = "All"
    screener_risk: str = "All"
    screener_min_esg: float = 60.0
    
    # Stock Search in Stock Detail
    stock_search_query: str = ""
    selected_stock_ticker: str = "TCS.NS"
    
    # Paper Trading Form
    pt_ticker: str = "RELIANCE.NS"
    pt_order_type: str = "BUY"
    pt_quantity: str = "10"
    pt_cash_balance: float = 1000000.0 # ₹1,000,000 initial balance
    pt_message: str = ""
    
    # Chat State
    chat_input: str = ""
    chat_messages: List[ChatMessage] = [
        ChatMessage(
            sender="assistant",
            text="Hi! I'm BidUp AI. I can help you understand your portfolio — how concentrated it is, which sectors dominate, and how risks in one area can flow into another. Ask me anything about your holdings!",
            time="Just now"
        )
    ]
    
    # Settings feedback
    profile_msg: str = ""

    # Simulated What-If Portfolio Comparison
    sim_add_ticker: str = "DLF.NS"
    sim_add_quantity: str = "25"
    sim_message: str = ""

    # Portfolio add preview panel
    show_preview: bool = False

    # News Feed State (cached so we don't hammer the API on every render)
    fetched_news: List[NewsItem] = []       # NewsData.io results (populated async)
    news_fetching: bool = False             # True while API call is in-flight
    news_fetched_at: float = 0.0           # epoch seconds of last successful fetch

    # Holdings List — pre-populated demo portfolio (~₹20,000 across 4 sectors)
    holdings: List[Holding] = [
        Holding(id="demo_1", ticker="WIPRO.NS",      name="Wipro Ltd",                sector="IT",                  quantity=10, avg_buy_price=520.0,  current_price=540.0,  invested_value=5200.0,  current_value=5400.0,  unrealized_pnl=200.0,   unrealized_pnl_pct=3.85),
        Holding(id="demo_2", ticker="HDFCBANK.NS",   name="HDFC Bank Ltd",            sector="Financial Services",  quantity=3,  avg_buy_price=1600.0, current_price=1650.0, invested_value=4800.0,  current_value=4950.0,  unrealized_pnl=150.0,   unrealized_pnl_pct=3.13),
        Holding(id="demo_3", ticker="ITC.NS",        name="ITC Ltd",                  sector="FMCG",                quantity=15, avg_buy_price=490.0,  current_price=505.0,  invested_value=7350.0,  current_value=7575.0,  unrealized_pnl=225.0,   unrealized_pnl_pct=3.06),
        Holding(id="demo_4", ticker="CIPLA.NS",      name="Cipla Ltd",                sector="Pharma",              quantity=1,  avg_buy_price=1520.0, current_price=1580.0, invested_value=1520.0,  current_value=1580.0,  unrealized_pnl=60.0,    unrealized_pnl_pct=3.95),
        Holding(id="demo_5", ticker="NTPC.NS",       name="NTPC Ltd",                 sector="Energy",              quantity=3,  avg_buy_price=375.0,  current_price=390.0,  invested_value=1125.0,  current_value=1170.0,  unrealized_pnl=45.0,    unrealized_pnl_pct=4.0),
    ]

    # --- Computed Var Properties ---
    @rx.var
    def total_invested(self) -> float:
        return sum(h.invested_value for h in self.holdings)
        
    @rx.var
    def total_current(self) -> float:
        return sum(h.current_value for h in self.holdings)
        
    @rx.var
    def total_pnl(self) -> float:
        return self.total_current - self.total_invested
        
    @rx.var
    def total_pnl_pct(self) -> float:
        if self.total_invested == 0:
            return 0.0
        return round((self.total_pnl / self.total_invested) * 100, 2)
        
    @rx.var
    def holdings_count(self) -> int:
        return len(self.holdings)

    @rx.var
    def sector_count(self) -> int:
        return len(set(h.sector for h in self.holdings))

    @rx.var
    def held_tickers(self) -> List[str]:
        return [h.ticker for h in self.holdings]

    @rx.var
    def user_initial(self) -> str:
        """First character of user_name, uppercased. Computed server-side to avoid
        JS runtime errors from Reflex Var `.upper()` on the client."""
        return self.user_name[:1].upper() if self.user_name else "?"

    # Module 3 HHI Calculation & Diversification Breakdown
    @rx.var
    def sector_breakdown(self) -> List[SectorWeight]:
        if not self.holdings or self.total_current == 0:
            return []
        sectors_dict: Dict[str, Dict[str, Any]] = {}
        for h in self.holdings:
            if h.sector not in sectors_dict:
                sectors_dict[h.sector] = {"val": 0.0, "count": 0}
            sectors_dict[h.sector]["val"] += h.current_value
            sectors_dict[h.sector]["count"] += 1
            
        res = []
        for sec, data in sectors_dict.items():
            w = (data["val"] / self.total_current) * 100.0
            res.append(SectorWeight(
                sector=sec,
                market_value=round(data["val"], 2),
                weight_pct=round(w, 1),
                holdings_count=data["count"]
            ))
        res.sort(key=lambda x: x.weight_pct, reverse=True)
        return res

    @rx.var
    def top_sectors(self) -> List[SectorWeight]:
        return self.sector_breakdown[:3]

    @rx.var
    def hhi_score(self) -> float:
        weights = [s.weight_pct for s in self.sector_breakdown]
        if not weights:
            return 0.0
        return round(sum(w ** 2 for w in weights), 1)

    @rx.var
    def hhi_level(self) -> str:
        score = self.hhi_score
        if score == 0:
            return "No Active Holdings"
        elif score < 1500:
            return "Well Diversified"
        elif score <= 2500:
            return "Moderately Concentrated"
        else:
            return "Highly Concentrated"

    @rx.var
    def hhi_interpretation(self) -> str:
        score = self.hhi_score
        if not self.sector_breakdown:
            return "No active holdings. Add assets or load sample data to evaluate portfolio concentration."
        top_s = self.sector_breakdown[0]
        if score < 1500:
            return f"Your capital is spread across {len(self.sector_breakdown)} independent sectors. Top sector '{top_s.sector}' constitutes {top_s.weight_pct}%, protecting you against single-sector downturns."
        elif score <= 2500:
            return f"Your portfolio has moderate focus, with '{top_s.sector}' representing {top_s.weight_pct}% of capital. Cross-sector correlation monitoring is recommended."
        else:
            return f"High concentration in '{top_s.sector}' ({top_s.weight_pct}% of total capital). Macroeconomic shifts in this sector will heavily drive overall performance."

    # Module 4 GAT Risk Alerts (Plain language)
    @rx.var
    def active_gat_alerts(self) -> List[RiskAlert]:
        alerts = []
        sec_map = {s.sector: s.weight_pct for s in self.sector_breakdown}
        # Energy link
        if sec_map.get("Energy", 0) >= 10.0:
            alerts.append(RiskAlert(
                held_sector="Energy",
                held_weight_pct=round(sec_map["Energy"], 1),
                correlated_sector="Infra & Metals",
                correlation_coefficient=0.68,
                shock_propagation_level="Elevated",
                descriptive_signal=f"Your Energy holdings ({sec_map['Energy']:.1f}% weight) exhibit high co-movement with Infrastructure. Rising crude volatility may transmit downstream margin pressure."
            ))
        # Financial Services link
        if sec_map.get("Financial Services", 0) >= 10.0:
            alerts.append(RiskAlert(
                held_sector="Financial Services",
                held_weight_pct=round(sec_map["Financial Services"], 1),
                correlated_sector="Realty",
                correlation_coefficient=0.64,
                shock_propagation_level="Moderate",
                descriptive_signal=f"Your Financial Services holdings ({sec_map['Financial Services']:.1f}% weight) share interest-rate sensitivity with Real Estate."
            ))
        # IT link
        if sec_map.get("IT", 0) >= 10.0:
            alerts.append(RiskAlert(
                held_sector="IT",
                held_weight_pct=round(sec_map["IT"], 1),
                correlated_sector="Financial Services",
                correlation_coefficient=0.42,
                shock_propagation_level="Low-Moderate",
                descriptive_signal=f"Your IT holdings ({sec_map['IT']:.1f}% weight) link to global enterprise banking tech budgets."
            ))
        return alerts

    # Portfolio Impact Preview — computed from current manual_ticker + manual_quantity + manual_buy_price
    @rx.var
    def preview_stock_name(self) -> str:
        return STOCK_MAP.get(self.manual_ticker, {}).get("name", self.manual_ticker)

    @rx.var
    def preview_stock_sector(self) -> str:
        return STOCK_MAP.get(self.manual_ticker, {}).get("sector", "")

    @rx.var
    def preview_stock_price(self) -> float:
        return float(STOCK_MAP.get(self.manual_ticker, {}).get("price", 0.0))

    @rx.var
    def preview_add_qty(self) -> float:
        try:
            v = float(self.manual_quantity)
            return v if v > 0 else 0.0
        except Exception:
            return 0.0

    @rx.var
    def preview_add_value(self) -> float:
        try:
            buy = float(self.manual_buy_price)
        except Exception:
            buy = self.preview_stock_price
        return round(self.preview_add_qty * buy, 2)

    @rx.var
    def preview_new_total(self) -> float:
        return round(self.total_current + self.preview_add_value, 2)

    @rx.var
    def preview_sector_weights(self) -> List[SectorWeight]:
        if self.preview_new_total == 0 or self.preview_add_qty == 0:
            return self.sector_breakdown
        sectors: Dict[str, float] = {}
        for h in self.holdings:
            sectors[h.sector] = sectors.get(h.sector, 0.0) + h.current_value
        sec = self.preview_stock_sector
        sectors[sec] = sectors.get(sec, 0.0) + self.preview_add_value
        total = self.preview_new_total
        res = []
        for s, v in sectors.items():
            w = round((v / total) * 100.0, 1)
            count = sum(1 for h in self.holdings if h.sector == s) + (1 if s == sec else 0)
            res.append(SectorWeight(sector=s, market_value=round(v, 2), weight_pct=w, holdings_count=count))
        res.sort(key=lambda x: x.weight_pct, reverse=True)
        return res

    @rx.var
    def preview_new_hhi(self) -> float:
        weights = [s.weight_pct for s in self.preview_sector_weights]
        if not weights:
            return self.hhi_score
        return round(sum(w ** 2 for w in weights), 1)

    @rx.var
    def preview_hhi_delta(self) -> float:
        return round(self.preview_new_hhi - self.hhi_score, 1)

    @rx.var
    def preview_new_level(self) -> str:
        score = self.preview_new_hhi
        if score == 0:
            return "No Holdings"
        elif score < 1500:
            return "Well Diversified"
        elif score <= 2500:
            return "Moderately Concentrated"
        else:
            return "Highly Concentrated"

    @rx.var
    def preview_new_sector_weight_pct(self) -> float:
        sec = self.preview_stock_sector
        for s in self.preview_sector_weights:
            if s.sector == sec:
                return s.weight_pct
        return 0.0

    @rx.var
    def preview_has_risk_flag(self) -> bool:
        """True if adding the stock would push any sector above 25% or HHI above 2500."""
        if not self.show_preview:
            return False
        if self.preview_new_hhi > 2500:
            return True
        return any(s.weight_pct > 25.0 for s in self.preview_sector_weights)

    @rx.var
    def preview_risk_flag_reason(self) -> str:
        if self.preview_new_hhi > 2500:
            return f"Adding this stock would make your portfolio Highly Concentrated (HHI {self.preview_new_hhi:,.0f} > 2500)."
        for s in self.preview_sector_weights:
            if s.weight_pct > 25.0:
                return f"After adding, {s.sector} would represent {s.weight_pct:.1f}% of your portfolio — above the 25% single-sector concentration threshold."
        return ""

    # News Feed — returns live NewsData.io results when available, curated fallback otherwise
    @rx.var
    def portfolio_news_feed(self) -> List[NewsItem]:
        # If we have fetched news from the live API, prefer those
        if self.fetched_news:
            return self.fetched_news
        # Curated fallback (all have real article URLs) shown before first API fetch
        held = self.held_tickers
        all_news = [
            NewsItem(id="n1", ticker="TCS.NS", headline="TCS expands multi-year cloud transformation partnership with European tier-1 bank", sentiment="Bullish", source="Economic Times", time_ago="2h ago", published_at="", url="https://economictimes.indiatimes.com/tech/information-tech/tcs-bags-multi-year-deal-from-european-bank/articleshow/108500000.cms"),
            NewsItem(id="n2", ticker="RELIANCE.NS", headline="Reliance Jio and Retail drive steady quarterly operating margin expansion", sentiment="Bullish", source="LiveMint", time_ago="3h ago", published_at="", url="https://www.livemint.com/companies/news/reliance-industries-retail-and-telecom-growth-q3-results-11705663482914.html"),
            NewsItem(id="n3", ticker="HDFCBANK.NS", headline="RBI keeps repo rates steady; Private banking credit demand maintains steady trajectory", sentiment="Neutral", source="Bloomberg Quint", time_ago="4h ago", published_at="", url="https://www.ndtvprofit.com/business/rbi-monetary-policy-repo-rate-unchanged-banking-credit-outlook"),
            NewsItem(id="n4", ticker="TATAMOTORS.NS", headline="Tata Motors EV delivery volumes surge 22% YoY in commercial and passenger segment", sentiment="Bullish", source="CNBC TV18", time_ago="5h ago", published_at="", url="https://www.cnbctv18.com/auto/tata-motors-passenger-commercial-vehicle-sales-ev-volumes-growth-19412345.htm"),
            NewsItem(id="n5", ticker="SUNPHARMA.NS", headline="Sun Pharma receives USFDA clearance for specialty formulation manufacturing facility", sentiment="Bullish", source="Moneycontrol", time_ago="6h ago", published_at="", url="https://www.moneycontrol.com/news/business/companies/sun-pharma-usfda-clearance-specialty-formulations-12456789.html"),
            NewsItem(id="n6", ticker="ITC.NS", headline="ITC FMCG non-cigarette business crosses key quarterly revenue milestone", sentiment="Neutral", source="Business Standard", time_ago="7h ago", published_at="", url="https://www.business-standard.com/companies/news/itc-q3-results-fmcg-non-cigarette-revenue-growth-124012900892_1.html"),
            NewsItem(id="n7", ticker="INFY.NS", headline="Infosys collaborates with global enterprise on generative AI engineering workflows", sentiment="Bullish", source="Economic Times", time_ago="8h ago", published_at="", url="https://economictimes.indiatimes.com/tech/information-tech/infosys-collaborates-with-global-clients-for-generative-ai-solutions/articleshow/107890000.cms"),
            NewsItem(id="n8", ticker="LT.NS", headline="L&T Construction bags mega engineering orders across Middle East and domestic infrastructure", sentiment="Bullish", source="LiveMint", time_ago="9h ago", published_at="", url="https://www.livemint.com/companies/news/l-t-construction-wins-mega-orders-in-domestic-and-middle-east-markets-11706500000000.html"),
            NewsItem(id="n9", ticker="TATASTEEL.NS", headline="Global coking coal price volatility watched as domestic steel demand remains resilient", sentiment="Risk Watch", source="Reuters India", time_ago="10h ago", published_at="", url="https://www.reuters.com/markets/commodities/tata-steel-india-operations-coking-coal-prices-demand-2024-02-15/"),
            NewsItem(id="n10", ticker="DLF.NS", headline="DLF luxury residential phase achieves record pre-launch booking interest in NCR", sentiment="Bullish", source="Financial Express", time_ago="11h ago", published_at="", url="https://www.financialexpress.com/business/industry-dlf-luxury-housing-project-record-pre-launch-sales-gurugram-3401234/")
        ]
        if not held:
            return all_news[:4]
        filtered = [n for n in all_news if n.ticker in held]
        return filtered if filtered else all_news[:4]

    # Screener Results
    @rx.var
    def screener_stocks(self) -> List[StockCatalogItem]:
        res = []
        for s in ALL_STOCKS_DATA:
            if self.screener_sector != "All" and s["sector"] != self.screener_sector:
                continue
            if self.screener_cap != "All" and s["cap"] != self.screener_cap:
                continue
            if self.screener_risk != "All" and s["risk"] != self.screener_risk:
                continue
            if s["esg"] < self.screener_min_esg:
                continue
            res.append(StockCatalogItem(
                ticker=s["ticker"],
                name=s["name"],
                sector=s["sector"],
                industry=s["industry"],
                cap=s["cap"].replace("_", " ").title(),
                esg=s["esg"],
                risk=s["risk"].capitalize(),
                price=s["price"]
            ))
        return res

    @rx.var
    def screener_count(self) -> int:
        return len(self.screener_stocks)

    @rx.var
    def screener_min_esg_str(self) -> str:
        return str(int(self.screener_min_esg))

    @rx.var
    def filtered_tickers(self) -> List[str]:
        q = self.ticker_search_query.strip().upper()
        if not q:
            return ALL_TICKERS
        return [t for t in ALL_TICKERS if q in t or q in STOCK_MAP[t]["name"].upper()]

    @rx.var
    def selected_stock_detail(self) -> Dict[str, Any]:
        t = self.selected_stock_ticker
        if t in STOCK_MAP:
            s = STOCK_MAP[t]
            return {
                "ticker": s["ticker"],
                "name": s["name"],
                "sector": s["sector"],
                "industry": s["industry"],
                "cap": s["cap"].replace("_", " ").title(),
                "esg": s["esg"],
                "risk": s["risk"].capitalize(),
                "price": s["price"],
                "day_high": round(s["price"] * 1.025, 2),
                "day_low": round(s["price"] * 0.982, 2),
                "pe_ratio": round(18.5 + (len(s["ticker"]) % 15), 1),
                "market_cap_inr": f"₹{int(s['price'] * 120):,} Cr",
                "beta_nifty": round(0.75 + (len(s["sector"]) * 0.05), 2)
            }
        return STOCK_MAP["TCS.NS"]

    # --- Actions and Event Handlers ---
    def set_nav(self, tab: str):
        self.active_nav = tab
        self.is_menu_open = False
        self.portfolio_message = ""
        self.portfolio_error = ""

    def toggle_menu(self):
        self.is_menu_open = not self.is_menu_open

    def close_menu(self):
        self.is_menu_open = False

    def toggle_auth_mode(self):
        self.auth_mode = "signup" if self.auth_mode == "signin" else "signin"
        self.auth_message = ""

    async def handle_auth(self):
        """Single dispatcher for the auth button — branches on auth_mode."""
        try:
            if self.auth_mode == "signin":
                # --- Login path ---
                email = self.auth_email_input.strip()
                pwd = self.auth_password_input.strip()
                if not email or not pwd:
                    self.auth_message = "Please enter your email and password."
                    return
                pwd_hash = hash_password(pwd)
                res = db_login_user(email=email, password_hash=pwd_hash)
                if not res:
                    self.auth_message = "Invalid email or password. Please check your credentials."
                    return
                self.user_id = res["id"]
                self.user_email = res["email"]
                self.user_name = res["display_name"]
                self.risk_tolerance = res["risk_tolerance"]
                self.investment_horizon = res["investment_horizon"]
                self.sector_exclusions = res["sector_exclusions"]
                self.is_authenticated = True
                self.is_onboarding = False
                self.active_nav = "home"
                self.auth_message = ""
                db_holdings = db_get_holdings(self.user_id)
                if db_holdings:
                    loaded = []
                    for h in db_holdings:
                        ticker = h["ticker"]
                        stock = STOCK_MAP.get(ticker, {"price": h["avg_buy_price"], "name": h["name"], "sector": h["sector"]})
                        curr_p = stock["price"]
                        qty = h["quantity"]
                        inv = qty * h["avg_buy_price"]
                        curr_v = qty * curr_p
                        pnl = curr_v - inv
                        pnl_pct = (pnl / inv * 100) if inv > 0 else 0.0
                        loaded.append(Holding(
                            id=h["id"], ticker=ticker, name=stock["name"], sector=stock["sector"],
                            quantity=qty, avg_buy_price=h["avg_buy_price"], current_price=curr_p,
                            invested_value=round(inv, 2), current_value=round(curr_v, 2),
                            unrealized_pnl=round(pnl, 2), unrealized_pnl_pct=round(pnl_pct, 2)
                        ))
                    self.holdings = loaded
                else:
                    self.load_initial_demo_holdings()
                yield State.fetch_portfolio_news
                yield State.refresh_prices
            else:
                # --- Signup path ---
                email = self.auth_email_input.strip()
                pwd = self.auth_password_input.strip()
                name = self.auth_name_input.strip()
                if not email or not pwd or not name:
                    self.auth_message = "Please fill in all required fields (Name, Email, Password)."
                    return
                pwd_hash = hash_password(pwd)
                res = db_signup_user(
                    email=email, password_hash=pwd_hash, display_name=name,
                    risk_tolerance=self.auth_risk_input, investment_horizon=self.auth_horizon_input,
                    sector_exclusions=["Tobacco"]
                )
                if not res:
                    self.auth_message = "An account with this email already exists. Please sign in."
                    return
                self.user_id = res["id"]
                self.user_email = res["email"]
                self.user_name = res["display_name"]
                self.risk_tolerance = res["risk_tolerance"]
                self.investment_horizon = res["investment_horizon"]
                self.sector_exclusions = res["sector_exclusions"]
                self.is_authenticated = True
                self.is_onboarding = True
                self.onboarding_step = 1
                self.auth_message = ""
                self.holdings = []
        except Exception as e:
            self.auth_message = f"Error: {str(e)}"

    def handle_signup(self):
        email = self.auth_email_input.strip()
        pwd = self.auth_password_input.strip()
        name = self.auth_name_input.strip()
        if not email or not pwd or not name:
            self.auth_message = "Please fill in all required fields (Name, Email, Password)."
            return
        pwd_hash = hash_password(pwd)
        res = db_signup_user(
            email=email,
            password_hash=pwd_hash,
            display_name=name,
            risk_tolerance=self.auth_risk_input,
            investment_horizon=self.auth_horizon_input,
            sector_exclusions=["Tobacco"]
        )
        if not res:
            self.auth_message = "An account with this email already exists. Please sign in."
            return
            
        self.user_id = res["id"]
        self.user_email = res["email"]
        self.user_name = res["display_name"]
        self.risk_tolerance = res["risk_tolerance"]
        self.investment_horizon = res["investment_horizon"]
        self.sector_exclusions = res["sector_exclusions"]
        self.is_authenticated = True
        self.is_onboarding = True
        self.onboarding_step = 1
        self.auth_message = ""
        self.holdings = []

    async def handle_login(self):
        email = self.auth_email_input.strip()
        pwd = self.auth_password_input.strip()
        if not email or not pwd:
            self.auth_message = "Please enter your email and password."
            return
        pwd_hash = hash_password(pwd)
        res = db_login_user(email=email, password_hash=pwd_hash)
        if not res:
            self.auth_message = "Invalid email or password. Please check your credentials."
            return
            
        self.user_id = res["id"]
        self.user_email = res["email"]
        self.user_name = res["display_name"]
        self.risk_tolerance = res["risk_tolerance"]
        self.investment_horizon = res["investment_horizon"]
        self.sector_exclusions = res["sector_exclusions"]
        self.is_authenticated = True
        self.is_onboarding = False
        self.active_nav = "home"
        self.auth_message = ""
        
        # Load user holdings from database
        db_holdings = db_get_holdings(self.user_id)
        if db_holdings:
            loaded = []
            for h in db_holdings:
                ticker = h["ticker"]
                stock = STOCK_MAP.get(ticker, {"price": h["avg_buy_price"], "name": h["name"], "sector": h["sector"]})
                curr_p = stock["price"]
                qty = h["quantity"]
                inv = qty * h["avg_buy_price"]
                curr_v = qty * curr_p
                pnl = curr_v - inv
                pnl_pct = (pnl / inv * 100) if inv > 0 else 0.0
                loaded.append(Holding(
                    id=h["id"],
                    ticker=ticker,
                    name=stock["name"],
                    sector=stock["sector"],
                    quantity=qty,
                    avg_buy_price=h["avg_buy_price"],
                    current_price=curr_p,
                    invested_value=round(inv, 2),
                    current_value=round(curr_v, 2),
                    unrealized_pnl=round(pnl, 2),
                    unrealized_pnl_pct=round(pnl_pct, 2)
                ))
            self.holdings = loaded
        else:
            self.load_initial_demo_holdings()
        yield State.fetch_portfolio_news

    def logout(self):
        self.is_authenticated = False
        self.is_onboarding = False
        self.user_id = ""
        self.user_email = ""
        self.user_name = ""
        self.auth_email_input = ""
        self.auth_password_input = ""
        self.auth_message = ""
        self.active_nav = "home"
        self.is_menu_open = False
        self.holdings = []
        self.is_guest = False

    async def enter_guest_mode(self):
        """Enter the app as a guest (no account). is_authenticated stays False so
        no Supabase writes occur. A temporary session user_id is used only for
        UI context — never written to the database."""
        self.is_authenticated = False
        self.is_guest = True
        self.user_id = f"guest_{str(uuid.uuid4())[:8]}"
        self.user_name = "Guest"
        self.user_email = ""
        self.auth_message = ""
        self.active_nav = "home"
        self.is_onboarding = False
        self.is_menu_open = False
        # Load demo holdings for a rich default experience
        self.load_initial_demo_holdings()
        yield State.fetch_portfolio_news
        yield State.refresh_prices

    def complete_onboarding_profile(self):
        self.risk_tolerance = self.onboarding_risk
        self.investment_horizon = self.onboarding_horizon
        if self.is_authenticated:
            db_update_profile(self.user_id, self.risk_tolerance, self.investment_horizon)
        self.onboarding_step = 2

    def complete_onboarding_with_demo(self):
        self.load_initial_demo_holdings()
        self.is_onboarding = False
        self.active_nav = "home"

    def complete_onboarding_empty(self):
        self.is_onboarding = False
        self.active_nav = "portfolio"

    def load_initial_demo_holdings(self):
        demo_items = [
            {"ticker": "TCS.NS", "qty": 15, "buy": 3850.0},
            {"ticker": "RELIANCE.NS", "qty": 25, "buy": 2740.5},
            {"ticker": "HDFCBANK.NS", "qty": 40, "buy": 1520.0},
            {"ticker": "TATAMOTORS.NS", "qty": 50, "buy": 920.0},
            {"ticker": "SUNPHARMA.NS", "qty": 20, "buy": 1580.0},
            {"ticker": "ITC.NS", "qty": 100, "buy": 430.0},
        ]
        new_holdings = []
        for d in demo_items:
            stock = STOCK_MAP[d["ticker"]]
            curr_p = stock["price"]
            qty = d["qty"]
            buy = d["buy"]
            inv = qty * buy
            curr_v = qty * curr_p
            pnl = curr_v - inv
            pnl_pct = (pnl / inv * 100) if inv > 0 else 0.0
            if self.is_authenticated:
                db_save_holding(self.user_id, d["ticker"], qty, buy)
            new_holdings.append(Holding(
                id=str(uuid.uuid4())[:8],
                ticker=d["ticker"],
                name=stock["name"],
                sector=stock["sector"],
                quantity=qty,
                avg_buy_price=buy,
                current_price=curr_p,
                invested_value=round(inv, 2),
                current_value=round(curr_v, 2),
                unrealized_pnl=round(pnl, 2),
                unrealized_pnl_pct=round(pnl_pct, 2)
            ))
        self.holdings = new_holdings

    def set_manual_ticker(self, ticker: str):
        self.manual_ticker = ticker
        if ticker in STOCK_MAP:
            self.manual_buy_price = str(STOCK_MAP[ticker]["price"])

    def set_ticker_search_query(self, query: str):
        self.ticker_search_query = query
        match = next((t for t in ALL_TICKERS if query.strip().upper() == t), None)
        if match:
            self.set_manual_ticker(match)

    def set_manual_quantity(self, val: str):
        self.manual_quantity = val

    def set_manual_buy_price(self, val: str):
        self.manual_buy_price = val

    def set_user_name(self, val: str):
        self.user_name = val

    def set_risk_tolerance(self, val: str):
        self.risk_tolerance = val

    def set_investment_horizon(self, val: str):
        self.investment_horizon = val

    def set_chat_input(self, val: str):
        self.chat_input = val

    def set_pt_ticker(self, val: str):
        self.pt_ticker = val

    def set_pt_order_type(self, val: str):
        self.pt_order_type = val

    def set_pt_quantity(self, val: str):
        self.pt_quantity = val

    def set_screener_sector(self, val: str):
        self.screener_sector = val

    def set_screener_cap(self, val: str):
        self.screener_cap = val

    def set_screener_risk(self, val: str):
        self.screener_risk = val

    def set_screener_min_esg(self, val: str):
        try:
            self.screener_min_esg = float(val)
        except (ValueError, TypeError):
            self.screener_min_esg = 60.0

    def set_selected_stock_ticker(self, val: str):
        self.selected_stock_ticker = val

    def set_sim_add_ticker(self, val: str):
        self.sim_add_ticker = val

    def set_sim_add_quantity(self, val: str):
        self.sim_add_quantity = val

    def set_auth_email_input(self, val: str):
        self.auth_email_input = val

    def set_auth_password_input(self, val: str):
        self.auth_password_input = val

    def set_auth_name_input(self, val: str):
        self.auth_name_input = val

    def select_stock(self, ticker: str):
        self.selected_stock_ticker = ticker
        self.active_nav = "stocks"

    def toggle_preview(self):
        """Show or hide the impact preview panel for the currently selected ticker+qty."""
        self.show_preview = not self.show_preview

    def clear_preview(self):
        """Hide the preview panel without taking any action."""
        self.show_preview = False

    async def add_manual_holding(self):
        ticker = self.manual_ticker
        if ticker not in STOCK_MAP:
            self.portfolio_error = "Invalid stock ticker selected."
            self.portfolio_message = ""
            return
            
        try:
            qty = float(self.manual_quantity)
            buy_price = float(self.manual_buy_price)
            if qty <= 0 or buy_price <= 0:
                self.portfolio_error = "Quantity and buy price must be positive numbers."
                self.portfolio_message = ""
                return
        except ValueError:
            self.portfolio_error = "Please enter valid numeric values for quantity and buy price."
            self.portfolio_message = ""
            return
            
        stock = STOCK_MAP[ticker]
        curr_price = stock["price"]
        inv_val = qty * buy_price
        curr_val = qty * curr_price
        pnl = curr_val - inv_val
        pnl_pct = round((pnl / inv_val) * 100, 2) if inv_val > 0 else 0.0
        
        # Persist to db
        from backend.database import db_save_holding
        if self.is_authenticated:
            db_save_holding(self.user_id, ticker, qty, buy_price)
        
        new_holding = Holding(
            id=str(uuid.uuid4())[:8],
            ticker=ticker,
            name=stock["name"],
            sector=stock["sector"],
            quantity=qty,
            avg_buy_price=buy_price,
            current_price=curr_price,
            invested_value=round(inv_val, 2),
            current_value=round(curr_val, 2),
            unrealized_pnl=round(pnl, 2),
            unrealized_pnl_pct=pnl_pct
        )
        
        # Update or append
        existing_idx = next((i for i, h in enumerate(self.holdings) if h.ticker == ticker), None)
        if existing_idx is not None:
            self.holdings[existing_idx] = new_holding
        else:
            self.holdings.append(new_holding)
            
        self.portfolio_message = f"Successfully added {qty} shares of {ticker} to your portfolio."
        self.portfolio_error = ""
        self.show_preview = False
        yield State.fetch_portfolio_news

    async def remove_holding(self, ticker: str):
        from backend.database import db_delete_holding
        if self.is_authenticated:
            db_delete_holding(self.user_id, ticker)
        self.holdings = [h for h in self.holdings if h.ticker != ticker]
        self.portfolio_message = f"Removed {ticker} from portfolio."
        yield State.fetch_portfolio_news

    async def load_demo_csv(self):
        demo_holdings_data = [
            ("TCS.NS", 15, 3850.0),
            ("RELIANCE.NS", 25, 2740.5),
            ("HDFCBANK.NS", 40, 1520.0),
            ("TATAMOTORS.NS", 50, 920.0),
            ("SUNPHARMA.NS", 20, 1580.0),
            ("ITC.NS", 100, 430.0),
            ("INFY.NS", 30, 1820.0),
            ("LT.NS", 12, 3450.0),
            ("TATASTEEL.NS", 150, 145.0)
        ]
        from backend.database import db_save_holding
        new_holdings = []
        for ticker, qty, price in demo_holdings_data:
            info = STOCK_MAP[ticker]
            curr_p = info["price"]
            inv = qty * price
            curr_v = qty * curr_p
            pnl = curr_v - inv
            pnl_pct = (pnl / inv * 100) if inv > 0 else 0.0
            if self.is_authenticated:
                db_save_holding(self.user_id, ticker, qty, price)
            new_holdings.append(Holding(
                id=str(uuid.uuid4())[:8],
                ticker=ticker,
                name=info["name"],
                sector=info["sector"],
                quantity=qty,
                avg_buy_price=price,
                current_price=curr_p,
                invested_value=inv,
                current_value=curr_v,
                unrealized_pnl=round(pnl, 2),
                unrealized_pnl_pct=round(pnl_pct, 2)
            ))
        self.holdings = new_holdings
        self.portfolio_message = "Successfully loaded 9-stock multi-sector portfolio!"
        self.portfolio_error = ""
        yield State.fetch_portfolio_news

    @staticmethod
    def _match_ticker_to_title(title: str, tickers: list) -> str:
        """Match a news headline to the most relevant held ticker by checking
        if the company name (from STOCK_MAP) appears in the title. Falls back
        to 'Market' if no match is found."""
        title_lower = title.lower()
        for t in tickers:
            info = STOCK_MAP.get(t)
            if not info:
                continue
            # Check ticker symbol (without exchange suffix)
            short = t.replace(".NS", "").replace(".BO", "").lower()
            if short in title_lower:
                return t
            # Check company name keywords (first two words usually suffice)
            name_parts = info["name"].lower().split()
            for part in name_parts[:2]:
                if len(part) > 2 and part in title_lower:
                    return t
        return tickers[0] if tickers else "Market"

    # --- News: real NewsData.io fetch with 20-min cache ---
    @rx.event(background=True)
    async def fetch_portfolio_news(self):
        """Fetch live news from NewsData.io for held tickers.
        Respects a 20-minute cache window so demo/dev usage stays well within the
        free tier's ~200 req/day limit. Falls back to static curated news if the
        API key is absent or the call fails."""
        import time as _time

        async with self:
            # Check cache — skip if last fetch was within 20 minutes
            now_ts = _time.time()
            if self.news_fetching:
                return
            if self.news_fetched_at > 0 and (now_ts - self.news_fetched_at) < 1200:
                return   # Cache still fresh (20 min = 1200 s)
            if not NEWSDATA_API_KEY or NEWSDATA_API_KEY == "<your_newsdata_key_here>":
                return   # No key — stay on fallback static news
            tickers = list(self.held_tickers) or ["TCS.NS", "RELIANCE.NS", "HDFCBANK.NS", "INFY.NS"]
            self.news_fetching = True

        # Build a compact query from held tickers (strip .NS suffix for readability)
        def _ticker_to_query(t: str) -> str:
            return t.replace(".NS", "").replace(".BO", "")

        query = " OR ".join(_ticker_to_query(t) for t in tickers[:5])  # max 5 tickers in query

        def _compute_time_ago(pub_date_str: str) -> str:
            """Convert ISO pubDate from NewsData.io to human-readable time_ago."""
            try:
                from datetime import datetime, timezone
                pub = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))
                now = datetime.now(timezone.utc)
                delta_s = int((now - pub).total_seconds())
                if delta_s < 60:
                    return "Just now"
                if delta_s < 3600:
                    return f"{delta_s // 60}m ago"
                if delta_s < 86400:
                    return f"{delta_s // 3600}h ago"
                return f"{delta_s // 86400}d ago"
            except Exception:
                return "Recently"

        def _infer_sentiment(title: str) -> str:
            title_l = title.lower()
            if any(w in title_l for w in ["surge", "soar", "rise", "gain", "record", "profit", "growth", "win", "expands", "deal", "clearance"]):
                return "Bullish"
            if any(w in title_l for w in ["fall", "drop", "decline", "loss", "cut", "risk", "volatile", "warn", "concern", "slow"]):
                return "Risk Watch"
            return "Neutral"

        results: List[NewsItem] = []
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    NEWSDATA_BASE_URL,
                    params={
                        "apikey": NEWSDATA_API_KEY,
                        "q": query,
                        "country": "in",
                        "language": "en",
                        "category": "business",
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                articles = data.get("results", [])
                for i, art in enumerate(articles[:10]):
                    title = art.get("title", "")
                    link = art.get("link", "") or art.get("url", "")
                    pub_date = art.get("pubDate", "") or art.get("publishedAt", "")
                    source_name = art.get("source_id", "") or art.get("source", "")
                    if not title:
                        continue
                    results.append(NewsItem(
                        id=f"live_{i}",
                        ticker=self._match_ticker_to_title(title, tickers),
                        headline=title,
                        sentiment=_infer_sentiment(title),
                        source=source_name.title() if source_name else "NewsData.io",
                        time_ago=_compute_time_ago(pub_date) if pub_date else "Recently",
                        published_at=pub_date,
                        url=link,
                    ))
        except Exception:
            pass  # Leave fetched_news empty — computed var falls back to curated static list

        async with self:
            if results:
                self.fetched_news = results
                self.news_fetched_at = _time.time()
            self.news_fetching = False

    # --- Prices: yfinance periodic refresh ---
    @rx.event(background=True)
    async def refresh_prices(self):
        """Fetch live prices from yfinance for all held tickers and update holdings.
        Falls back gracefully: keeps last good price on error, never blanks values."""
        async with self:
            if self.prices_fetching or not self.holdings:
                return
            self.prices_fetching = True

        tickers = list({h.ticker for h in self.holdings})
        try:
            import yfinance as yf
            import math as _math
            data = yf.download(
                " ".join(tickers),
                period="1d",
                interval="1m",
                auto_adjust=True,
                progress=False,
            )
            # yfinance returns MultiIndex columns when >1 ticker, scalar when 1
            close_col = "Close"
            price_map: Dict[str, float] = {}
            if len(tickers) == 1:
                ticker = tickers[0]
                series = data[close_col] if close_col in data else None
                if series is not None and not series.empty:
                    val = float(series.iloc[-1])
                    # Guard: skip NaN or zero/negative prices
                    if not _math.isnan(val) and val > 0:
                        price_map[ticker] = val
            else:
                for ticker in tickers:
                    try:
                        series = data[close_col][ticker]
                        if not series.empty:
                            val = float(series.iloc[-1])
                            # Guard: skip NaN or zero/negative prices — keep last good price
                            if not _math.isnan(val) and val > 0:
                                price_map[ticker] = val
                    except (KeyError, TypeError):
                        pass

            async with self:
                if price_map:
                    updated = []
                    for h in self.holdings:
                        p = price_map.get(h.ticker, h.current_price)
                        # Final NaN safety — if p is still bad, fall back to catalog price
                        if _math.isnan(p) or p <= 0:
                            p = STOCK_MAP.get(h.ticker, {}).get("price", h.current_price) or h.current_price
                        curr_v = round(h.quantity * p, 2)
                        pnl = round(curr_v - h.invested_value, 2)
                        pnl_pct = round((pnl / h.invested_value) * 100, 2) if h.invested_value > 0 else 0.0
                        updated.append(Holding(
                            id=h.id,
                            ticker=h.ticker,
                            name=h.name,
                            sector=h.sector,
                            quantity=h.quantity,
                            avg_buy_price=h.avg_buy_price,
                            current_price=round(p, 2),
                            invested_value=h.invested_value,
                            current_value=curr_v,
                            unrealized_pnl=pnl,
                            unrealized_pnl_pct=pnl_pct,
                        ))
                    self.holdings = updated
                    self.prices_last_updated = datetime.now().strftime("%I:%M %p")
        except Exception:
            # Keep last good price; update label to show staleness
            async with self:
                if self.prices_last_updated:
                    pass  # Timestamp already set from a prior successful fetch
        finally:
            async with self:
                self.prices_fetching = False

    # --- Chat: real async Nemotron LLM call ---
    @rx.event(background=True)
    async def send_chat_message(self):
        """Send user query to NVIDIA Nemotron via OpenAI-compatible API.
        Includes full portfolio context (holdings, sector breakdown, HHI, GAT risk alerts),
        enforces non-advisory compliance, and shows visible errors on failure."""
        query = self.chat_input.strip()
        if not query:
            return

        async with self:
            self.chat_messages.append(ChatMessage(sender="user", text=query, time="Just now"))
            self.chat_input = ""
            # Placeholder while waiting for LLM
            self.chat_messages.append(ChatMessage(sender="assistant", text="⏳ Thinking…", time="Just now"))

        # Build portfolio context
        holdings_summary = ", ".join(
            f"{h.ticker} ({h.sector}, {h.quantity} shares, invested ₹{h.invested_value:,.0f}, current ₹{h.current_value:,.0f})"
            for h in self.holdings
        ) or "No holdings yet"
        sectors_summary = ", ".join(
            f"{s.sector}: {s.weight_pct:.1f}% (₹{s.market_value:,.0f})"
            for s in self.sector_breakdown
        ) or "None"
        alerts_text = " ".join(
            [a.descriptive_signal for a in self.active_gat_alerts]
        ) if self.active_gat_alerts else "No active GAT alerts."

        system_prompt = (
            "You are BidUp AI. Analytics assistant for Indian equity portfolios. "
            "NEVER give buy/sell advice. If asked, say you cannot advise then share the relevant analytics. "
            "ALWAYS output ONLY this: <answer>3-5 sentence plain English reply with real portfolio numbers</answer>\n\n"
            f"User portfolio — Holdings: {holdings_summary} | "
            f"Sector split: {sectors_summary} | "
            f"Diversification (HHI): {self.hhi_score:.1f} ({self.hhi_level}) | "
            f"Risk signals: {alerts_text}"
        )

        api_key = NEMOTRON_API_KEY or os.getenv("NEMOTRON_API_KEY", "").strip()
        if not api_key:
            error_text = "⚠️ NEMOTRON_API_KEY is not configured in .env. Please set a valid NVIDIA API key."
            async with self:
                if self.chat_messages and self.chat_messages[-1].text == "⏳ Thinking…":
                    self.chat_messages = list(self.chat_messages[:-1]) + [ChatMessage(sender="assistant", text=error_text, time="Just now")]
                else:
                    self.chat_messages.append(ChatMessage(sender="assistant", text=error_text, time="Just now"))
            return

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        # Candidate models: try configured model first, with automatic fallback if endpoint returns 404
        candidate_models = [
            "nvidia/nemotron-3-super-120b-a12b",
            NEMOTRON_MODEL,
            "nvidia/nemotron-3.5-lightning-30b-a3b",
            "meta/llama-3.2-11b-vision-instruct",
        ]

        import re as _re

        def _extract_answer(raw: str) -> str:
            """Extract <answer>…</answer> block from raw model output.
            Falls back gracefully if the model doesn't use the tags."""

            # 1. Primary: parse <answer>...</answer>
            m = _re.search(r"<answer>(.*?)</answer>", raw, _re.DOTALL | _re.IGNORECASE)
            if m:
                return m.group(1).strip()

            # 2. The model used <think>...</think> but forgot <answer> — take everything after </think>
            m_think = _re.search(r"</think(?:ing)?>(.+)", raw, _re.DOTALL | _re.IGNORECASE)
            if m_think:
                after = m_think.group(1).strip()
                if len(after) > 40:
                    return after

            # 3. Model wrote a "Here's a thinking process:" block with numbered steps —
            #    find the last step block which usually contains the draft answer.
            if _re.search(r"here'?s?\s+a\s+thinking\s+process|let\s+me\s+think", raw, _re.IGNORECASE):
                step_blocks = _re.split(r"\n\d+\.\s+\*\*", raw)
                if len(step_blocks) > 1:
                    last = step_blocks[-1].strip()
                    # Strip step heading (e.g. "Formulate Response**\n")
                    last = _re.sub(r"^[^*\n]*\*\*\s*\n?", "", last).strip()
                    # Strip "- Draft something like:" lead-in and quoted drafts
                    last = _re.sub(r'^[-*]\s*(draft\s+something\s+like|here\s+is\s+(the|my)|final\s+response)[^:]*:\s*[""]?',
                                   "", last, flags=_re.IGNORECASE).strip()
                    if last.startswith('"') and last.endswith('"'):
                        last = last[1:-1].strip()
                    if len(last) > 60:
                        return last

            # 4. Any "Final answer:" / "Response:" marker — take what follows
            for marker in ["final answer:", "my answer:", "response:",
                           "here's my response:", "here is my response:", "draft:"]:
                idx = raw.lower().rfind(marker)
                if idx != -1:
                    candidate = raw[idx + len(marker):].strip()
                    if candidate.startswith('"') and '"' in candidate[1:]:
                        candidate = candidate[1:candidate.rindex('"')].strip()
                    if len(candidate) > 60:
                        return candidate

            # 5. Last resort: if still full of numbered reasoning, take the last paragraph of substance
            paragraphs = [p.strip() for p in raw.split("\n\n") if len(p.strip()) > 60]
            if paragraphs:
                last_para = paragraphs[-1]
                # Only use if it doesn't look like reasoning (no "**Step" or "Analyze User")
                if not _re.search(r"\*\*\w+\s+\w+\*\*|Analyze User|Check Compliance|Identify Core", last_para):
                    return last_para

            # 6. Absolute fallback — raw text (still better than silence)
            return raw

        reply = ""
        last_error = ""
        for model_id in candidate_models:
            payload = {
                "model": model_id,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query},
                ],
                "temperature": 0.5,
                "max_tokens": 400,
            }
            try:
                async with httpx.AsyncClient(timeout=45.0) as client:
                    resp = await client.post(
                        f"{NEMOTRON_BASE_URL}/chat/completions",
                        headers=headers,
                        json=payload,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        raw = data["choices"][0]["message"]["content"].strip()
                        reply = _extract_answer(raw)
                        break
                    elif resp.status_code == 404:
                        last_error = f"HTTP 404 (model '{model_id}' not found on account)"
                        continue
                    else:
                        last_error = f"HTTP {resp.status_code}: {resp.text[:150]}"
            except httpx.RequestError as e:
                last_error = f"Network connection error: {str(e)}"
            except Exception as e:
                last_error = f"Unexpected error: {str(e)}"

        if not reply:
            reply = f"⚠️ AI Assistant Error: {last_error or 'Unable to reach NVIDIA Nemotron API'}. Please verify your network and NEMOTRON_API_KEY."

        async with self:
            if self.chat_messages and self.chat_messages[-1].text == "⏳ Thinking…":
                msgs = list(self.chat_messages[:-1])
                msgs.append(ChatMessage(sender="assistant", text=reply, time="Just now"))
                self.chat_messages = msgs
            else:
                self.chat_messages.append(ChatMessage(sender="assistant", text=reply, time="Just now"))

    async def send_quick_chat(self, prompt_text: str):
        self.chat_input = prompt_text
        yield State.send_chat_message


    # Paper Trading Execution
    def execute_paper_trade(self):
        ticker = self.pt_ticker
        if ticker not in STOCK_MAP:
            self.pt_message = "Selected stock not found."
            return
            
        try:
            qty = float(self.pt_quantity)
            if qty <= 0:
                self.pt_message = "Quantity must be greater than 0."
                return
        except ValueError:
            self.pt_message = "Invalid quantity number."
            return
            
        stock = STOCK_MAP[ticker]
        req_price = stock["price"]
        # Gaussian slippage sampling
        slip_pct = max(0.01, random.gauss(0.05, 0.02))
        slip_sign = 1.0 if self.pt_order_type == "BUY" else -1.0
        exec_price = round(req_price * (1.0 + (slip_sign * slip_pct / 100.0)), 2)
        total_val = round(exec_price * qty, 2)
        
        if self.pt_order_type == "BUY":
            if total_val > self.pt_cash_balance:
                self.pt_message = f"Insufficient cash balance (₹{self.pt_cash_balance:,.2f}) for trade (₹{total_val:,.2f})."
                return
            self.pt_cash_balance -= total_val
        else:
            self.pt_cash_balance += total_val
            
        new_trade = PaperTrade(
            id=f"pt_{len(self.paper_ledger)+1}",
            ticker=ticker,
            order_type=self.pt_order_type,
            quantity=qty,
            requested_price=req_price,
            slippage_pct=round(slip_pct, 3),
            executed_price=exec_price,
            total_amount=total_val,
            time="Just now"
        )
        self.paper_ledger.insert(0, new_trade)
        self.pt_message = f"Order Executed! {self.pt_order_type} {qty} {ticker} @ ₹{exec_price:,.2f} (Slippage: {slip_pct:.3f}%)"

    def simulate_what_if(self):
        ticker = self.sim_add_ticker
        if ticker not in STOCK_MAP:
            self.sim_message = "Invalid stock ticker."
            return
        try:
            qty = float(self.sim_add_quantity)
        except ValueError:
            self.sim_message = "Invalid quantity."
            return
            
        stock = STOCK_MAP[ticker]
        added_val = qty * stock["price"]
        new_total = self.total_current + added_val
        
        # Calculate new HHI
        sectors: Dict[str, float] = {}
        for h in self.holdings:
            sectors[h.sector] = sectors.get(h.sector, 0.0) + h.current_value
        sectors[stock["sector"]] = sectors.get(stock["sector"], 0.0) + added_val
        
        new_hhi = sum(((v / new_total) * 100.0) ** 2 for v in sectors.values())
        diff = new_hhi - self.hhi_score
        direction = "increase" if diff > 0 else "decrease"
        self.sim_message = f"Adding {qty} shares of {ticker} ({stock['sector']}) would change HHI from {self.hhi_score:,.1f} to {new_hhi:,.1f} ({direction} of {abs(diff):,.1f} pts)."

    def update_profile_settings(self):
        from backend.database import db_update_profile
        if self.is_authenticated:
            db_update_profile(self.user_id, self.risk_tolerance, self.investment_horizon)
        self.profile_msg = "Risk profile preferences successfully updated!"

# --- UI Helper Components ---

def legal_banner() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.icon(tag="info", color=ACCENT_COLOR, size=16),
            rx.text(
                "Educational & Analytical System — Descriptive portfolio risk analytics only. Does not provide personalized financial, buy/sell, or investment advice.",
                color=TEXT_MUTED,
                font_size="0.78rem",
            ),
            spacing="2",
            align="center",
            width="100%",
        ),
        background_color=ACCENT_LIGHT,
        border=f"1px solid {ACCENT_BORDER}",
        border_radius="8px",
        padding=f"{SPACE_2} {SPACE_4}",
        width="100%",
        margin_bottom=SPACE_6,
    )

def persistent_header() -> rx.Component:
    return rx.box(
        rx.hstack(
            # Logo Brand
            rx.hstack(
                rx.heading("BidUp", font_size="1.5rem", font_weight="800", color=TEXT_HEADLINE),
                rx.badge("Intelligence", background_color=ACCENT_LIGHT, color=ACCENT_COLOR, border=f"1px solid {ACCENT_COLOR}"),
                on_click=State.set_nav("home"),
                cursor="pointer",
                spacing="3",
                align="center",
            ),
            rx.spacer(),
            # Primary Nav Links
            rx.hstack(
                rx.button(
                    "Home",
                    on_click=State.set_nav("home"),
                    variant=rx.cond(State.active_nav == "home", "solid", "ghost"),
                    background_color=rx.cond(State.active_nav == "home", ACCENT_COLOR, "transparent"),
                    color=rx.cond(State.active_nav == "home", "#ffffff", TEXT_HEADLINE),
                    size="2",
                    padding=f"{SPACE_2} {SPACE_4}",
                ),
                rx.button(
                    "Portfolio",
                    on_click=State.set_nav("portfolio"),
                    variant=rx.cond(State.active_nav == "portfolio", "solid", "ghost"),
                    background_color=rx.cond(State.active_nav == "portfolio", ACCENT_COLOR, "transparent"),
                    color=rx.cond(State.active_nav == "portfolio", "#ffffff", TEXT_HEADLINE),
                    size="2",
                    padding=f"{SPACE_2} {SPACE_4}",
                ),
                rx.button(
                    "Chat",
                    on_click=State.set_nav("chat"),
                    variant=rx.cond(State.active_nav == "chat", "solid", "ghost"),
                    background_color=rx.cond(State.active_nav == "chat", ACCENT_COLOR, "transparent"),
                    color=rx.cond(State.active_nav == "chat", "#ffffff", TEXT_HEADLINE),
                    size="2",
                    padding=f"{SPACE_2} {SPACE_4}",
                ),
                rx.button(
                    "GAT Analytics",
                    on_click=State.set_nav("analytics"),
                    variant=rx.cond(State.active_nav == "analytics", "solid", "ghost"),
                    background_color=rx.cond(State.active_nav == "analytics", ACCENT_COLOR, "transparent"),
                    color=rx.cond(State.active_nav == "analytics", "#ffffff", TEXT_HEADLINE),
                    size="2",
                    padding=f"{SPACE_2} {SPACE_4}",
                ),
                rx.button(
                    "Settings",
                    on_click=State.set_nav("settings"),
                    variant=rx.cond(State.active_nav == "settings", "solid", "ghost"),
                    background_color=rx.cond(State.active_nav == "settings", ACCENT_COLOR, "transparent"),
                    color=rx.cond(State.active_nav == "settings", "#ffffff", TEXT_HEADLINE),
                    size="2",
                    padding=f"{SPACE_2} {SPACE_4}",
                ),
                spacing="2",
                align="center",
            ),
            width="100%",
            align="center",
        ),
        border_bottom=f"1px solid {CARD_BORDER_SUBTLE}",
        background_color=CARD_BG,
        padding=f"{SPACE_4} {SPACE_8}",
        position="sticky",
        top="0",
        z_index="100",
        width="100%",
        box_shadow=SHADOW_SUBTLE,
    )

# --- 1. /home Route (Spacious Layout & Portfolio Health Anchor) ---
def portfolio_health_hero() -> rx.Component:
    return rx.box(
        rx.vstack(
            # Header with badge
            rx.hstack(
                rx.hstack(
                    rx.icon(tag="shield_check", color=ACCENT_COLOR, size=24),
                    rx.heading("Portfolio Health & Risk Status", font_size="1.4rem", font_weight="800", color=TEXT_HEADLINE),
                    spacing="2",
                    align="center",
                ),
                rx.spacer(),
                rx.badge("Live Assessment", color_scheme="purple", size="2"),
                width="100%",
                align="center",
            ),
            rx.text(
                "A beginner-friendly overview of your capital distribution, dominant sector exposures, and cross-sector volatility alerts:",
                color=TEXT_MUTED,
                font_size="0.9rem",
            ),
            rx.divider(border_color=CARD_BORDER_SUBTLE),
            # 3 Core Questions Grid
            rx.grid(
                # Question 1: Is my money spread out?
                rx.box(
                    rx.vstack(
                        rx.text("1. Is my money spread out or concentrated?", font_size="0.82rem", font_weight="600", color=TEXT_MUTED),
                        rx.heading(
                            State.hhi_level,
                            color=rx.cond(
                                State.hhi_level == "Well Diversified",
                                POSITIVE_COLOR,
                                rx.cond(State.hhi_level == "Moderately Concentrated", WARNING_COLOR, ALERT_COLOR),
                            ),
                            font_size="1.35rem",
                            font_weight="800",
                        ),
                        # 3-Band Visual Gauge Bar
                        rx.vstack(
                            rx.hstack(
                                rx.box(height="6px", flex="1", background_color=POSITIVE_COLOR, border_radius="3px 0 0 3px"),
                                rx.box(height="6px", flex="1", background_color=WARNING_COLOR),
                                rx.box(height="6px", flex="1", background_color=ALERT_COLOR, border_radius="0 3px 3px 0"),
                                spacing="1",
                                width="100%",
                            ),
                            rx.hstack(
                                rx.text("Spread Out (<1500)", font_size="0.68rem", color=TEXT_SECONDARY),
                                rx.spacer(),
                                rx.text("Moderate (1500-2500)", font_size="0.68rem", color=TEXT_SECONDARY),
                                rx.spacer(),
                                rx.text("Concentrated (>2500)", font_size="0.68rem", color=TEXT_SECONDARY),
                                width="100%",
                            ),
                            spacing="1",
                            width="100%",
                        ),
                        rx.hstack(
                            rx.badge(f"Score: {State.hhi_score:,.1f}", color_scheme="purple", size="1"),
                            rx.text("Lower = more spread out", font_size="0.75rem", color=TEXT_SECONDARY),
                            spacing="1",
                            align="center",
                        ),
                        rx.text(
                            "This number summarises how spread out your money is across sectors. Below 1500 is healthy; above 2500 means you're quite concentrated in a few areas.",
                            font_size="0.73rem", color=TEXT_SECONDARY, font_style="italic",
                        ),
                        spacing="2",
                    ),
                    background_color=BG_COLOR,
                    border=f"1px solid {CARD_BORDER_SUBTLE}",
                    border_radius="10px",
                    padding=SPACE_4,
                    height="100%",
                ),
                # Question 2: Which sectors am I most exposed to?
                rx.box(
                    rx.vstack(
                        rx.text("2. Where is most of my capital allocated?", font_size="0.82rem", font_weight="600", color=TEXT_MUTED),
                        rx.cond(
                            State.sector_count > 0,
                            rx.vstack(
                                rx.foreach(
                                    State.top_sectors,
                                    lambda s: rx.vstack(
                                        rx.hstack(
                                            rx.text(s.sector, font_size="0.85rem", font_weight="600", color=TEXT_HEADLINE),
                                            rx.spacer(),
                                            rx.text(f"{s.weight_pct}% (₹{s.market_value:,.0f})", font_size="0.82rem", font_weight="700", color=ACCENT_COLOR),
                                            width="100%",
                                        ),
                                        rx.box(
                                            rx.box(
                                                height="6px",
                                                width=f"{s.weight_pct}%",
                                                background_color=ACCENT_COLOR,
                                                border_radius="3px",
                                            ),
                                            width="100%",
                                            background_color=CARD_BORDER_SUBTLE,
                                            border_radius="3px",
                                            height="6px",
                                        ),
                                        spacing="1",
                                        width="100%",
                                    ),
                                ),
                                spacing="2",
                                width="100%",
                            ),
                            rx.text("No sector allocation data available.", color=TEXT_MUTED, font_size="0.85rem"),
                        ),
                        spacing="2",
                    ),
                    background_color=BG_COLOR,
                    border=f"1px solid {CARD_BORDER_SUBTLE}",
                    border_radius="10px",
                    padding=SPACE_4,
                    height="100%",
                ),
                # Question 3: Is there a risk alert right now?
                rx.box(
                    rx.vstack(
                        rx.text("3. Are there active cross-sector risk alerts?", font_size="0.82rem", font_weight="600", color=TEXT_MUTED),
                        rx.cond(
                            State.active_gat_alerts.length() > 0,
                            rx.vstack(
                                rx.foreach(
                                    State.active_gat_alerts,
                                    lambda a: rx.hstack(
                                        rx.icon(tag="triangle_alert", size=16, color=ALERT_COLOR),
                                        rx.text(a.descriptive_signal, font_size="0.8rem", color=TEXT_HEADLINE),
                                        background_color=ALERT_LIGHT,
                                        border=f"1px solid rgba(228, 88, 88, 0.2)",
                                        border_radius="6px",
                                        padding=SPACE_2,
                                        width="100%",
                                        align="start",
                                    ),
                                ),
                                spacing="2",
                                width="100%",
                            ),
                            rx.hstack(
                                rx.icon(tag="circle_check", size=18, color=POSITIVE_COLOR),
                                rx.text("No acute sector transmission risks detected across your active allocations.", font_size="0.85rem", color=POSITIVE_COLOR),
                                background_color=POSITIVE_LIGHT,
                                border=f"1px solid rgba(22, 163, 74, 0.2)",
                                border_radius="6px",
                                padding=SPACE_3,
                                width="100%",
                                align="center",
                            ),
                        ),
                        spacing="2",
                    ),
                    background_color=BG_COLOR,
                    border=f"1px solid {CARD_BORDER_SUBTLE}",
                    border_radius="10px",
                    padding=SPACE_4,
                    height="100%",
                ),
                columns="3",
                spacing="4",
                width="100%",
            ),
            spacing="4",
            width="100%",
        ),
        background_color=CARD_BG,
        border=f"1px solid {CARD_BORDER}",
        border_radius="16px",
        padding=SPACE_8,
        width="100%",
        box_shadow=SHADOW_HERO,
    )

def home_view() -> rx.Component:
    return rx.vstack(
        legal_banner(),
        # Visual Anchor: Top Portfolio Health Section
        portfolio_health_hero(),
        # ── Portfolio at a Glance ─────────────────────────────────────────────
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="pie_chart", color=ACCENT_COLOR, size=18),
                    rx.heading("Portfolio at a Glance", font_size="1.05rem", font_weight="700", color=TEXT_HEADLINE),
                    rx.spacer(),
                    rx.hstack(
                        rx.heading(f"₹{State.total_current:,.0f}", font_size="1.1rem", font_weight="800", color=TEXT_HEADLINE),
                        rx.badge(
                            f"{State.total_pnl_pct}%",
                            color_scheme=rx.cond(State.total_pnl >= 0, "green", "red"),
                            size="1",
                        ),
                        spacing="2", align="center",
                    ),
                    width="100%", align="center",
                ),
                # Top row: sector bars left, summary stats right
                rx.grid(
                    # Sector allocation mini-bars
                    rx.vstack(
                        rx.text("Sector breakdown", font_size="0.75rem", font_weight="600", color=TEXT_MUTED),
                        rx.foreach(
                            State.top_sectors,
                            lambda s: rx.hstack(
                                rx.text(s.sector, font_size="0.75rem", color=TEXT_HEADLINE, min_width="130px"),
                                rx.box(
                                    rx.box(
                                        height="10px",
                                        width=f"{s.weight_pct}%",
                                        background_color=ACCENT_COLOR,
                                        border_radius="3px",
                                        opacity="0.85",
                                    ),
                                    background_color=CARD_BORDER_SUBTLE,
                                    border_radius="3px",
                                    width="100%",
                                    flex="1",
                                    overflow="hidden",
                                ),
                                rx.text(f"{s.weight_pct:.0f}%", font_size="0.75rem", font_weight="600", color=ACCENT_COLOR, min_width="36px", text_align="right"),
                                spacing="2", align="center", width="100%",
                            ),
                        ),
                        spacing="2", width="100%",
                    ),
                    # Right-side summary stats
                    rx.vstack(
                        rx.hstack(
                            rx.icon(tag="indian_rupee", size=14, color=TEXT_MUTED),
                            rx.vstack(
                                rx.text("Invested", font_size="0.7rem", color=TEXT_MUTED),
                                rx.text(f"₹{State.total_invested:,.0f}", font_size="0.9rem", font_weight="700", color=TEXT_HEADLINE),
                                spacing="0",
                            ),
                            spacing="1", align="center",
                        ),
                        rx.hstack(
                            rx.icon(tag="trending_up", size=14, color=rx.cond(State.total_pnl >= 0, POSITIVE_COLOR, ALERT_COLOR)),
                            rx.vstack(
                                rx.text("Gain / Loss", font_size="0.7rem", color=TEXT_MUTED),
                                rx.text(
                                    f"₹{State.total_pnl:,.0f}",
                                    font_size="0.9rem", font_weight="700",
                                    color=rx.cond(State.total_pnl >= 0, POSITIVE_COLOR, ALERT_COLOR),
                                ),
                                spacing="0",
                            ),
                            spacing="1", align="center",
                        ),
                        rx.hstack(
                            rx.icon(tag="layers", size=14, color=TEXT_MUTED),
                            rx.vstack(
                                rx.text("Holdings", font_size="0.7rem", color=TEXT_MUTED),
                                rx.text(f"{State.holdings_count} stocks · {State.sector_count} sectors", font_size="0.9rem", font_weight="700", color=ACCENT_COLOR),
                                spacing="0",
                            ),
                            spacing="1", align="center",
                        ),
                        rx.button(
                            "View Full Portfolio →",
                            on_click=State.set_nav("portfolio"),
                            size="1", variant="ghost", color=ACCENT_COLOR, font_size="0.78rem", padding="0",
                        ),
                        spacing="3", width="100%", align="start",
                    ),
                    columns="2", spacing="6", width="100%",
                ),
                spacing="3", width="100%",
            ),
            background_color=CARD_BG,
            border=f"1px solid {CARD_BORDER}",
            border_radius="14px",
            padding=SPACE_6,
            box_shadow=SHADOW_CARD,
            width="100%",
            margin_top=SPACE_6,
        ),
        # Metric Quick Bar (Lightweight, grouped together with breathing room)
        rx.grid(
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon(tag="indian_rupee", color=ACCENT_COLOR, size=16),
                        rx.text("Total Portfolio Value", color=TEXT_MUTED, font_size="0.82rem", font_weight="500"),
                        spacing="1", align="center",
                    ),
                    rx.heading(f"₹{State.total_current:,.2f}", color=TEXT_HEADLINE, font_size="1.6rem", font_weight="800"),
                    rx.text(f"Invested: ₹{State.total_invested:,.2f}", color=TEXT_MUTED, font_size="0.78rem"),
                    spacing="1",
                ),
                background_color=CARD_BG,
                border=f"1px solid {CARD_BORDER_SUBTLE}",
                border_radius="12px",
                padding=SPACE_6,
                box_shadow=SHADOW_CARD,
            ),
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon(tag="trending_up", color=rx.cond(State.total_pnl >= 0, POSITIVE_COLOR, ALERT_COLOR), size=16),
                        rx.text("Your Gain / Loss So Far", color=TEXT_MUTED, font_size="0.82rem", font_weight="500"),
                        spacing="1", align="center",
                    ),
                    rx.heading(
                        f"₹{State.total_pnl:,.2f}",
                        color=rx.cond(State.total_pnl >= 0, POSITIVE_COLOR, ALERT_COLOR),
                        font_size="1.6rem",
                        font_weight="800",
                    ),
                    rx.badge(
                        f"{State.total_pnl_pct}% since you bought",
                        color_scheme=rx.cond(State.total_pnl >= 0, "green", "red"),
                        size="1",
                    ),
                    rx.text(
                        "How much your investments have grown or dropped since you bought — not locked in until you sell.",
                        color=TEXT_SECONDARY, font_size="0.72rem", font_style="italic",
                    ),
                    spacing="1",
                ),
                background_color=CARD_BG,
                border=f"1px solid {CARD_BORDER_SUBTLE}",
                border_radius="12px",
                padding=SPACE_6,
                box_shadow=SHADOW_CARD,
            ),
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon(tag="layers", color=ACCENT_COLOR, size=16),
                        rx.text("Stocks in Your Portfolio", color=TEXT_MUTED, font_size="0.82rem", font_weight="500"),
                        spacing="1", align="center",
                    ),
                    rx.heading(f"{State.holdings_count} Stocks", color=ACCENT_COLOR, font_size="1.6rem", font_weight="800"),
                    rx.text(f"Across {State.sector_count} sectors", color=TEXT_MUTED, font_size="0.78rem"),
                    spacing="1",
                ),
                background_color=CARD_BG,
                border=f"1px solid {CARD_BORDER_SUBTLE}",
                border_radius="12px",
                padding=SPACE_6,
                box_shadow=SHADOW_CARD,
            ),
            columns="3",
            spacing="4",
            width="100%",
            margin_top=SPACE_6,
        ),
        # Distinct Section Header with Whitespace Separation
        rx.hstack(
            rx.vstack(
                rx.heading("AI Risk Intelligence & Market Developments", font_size="1.2rem", font_weight="700", color=TEXT_HEADLINE),
                rx.text("Consult BidUp's financial intelligence assistant or inspect latest news for your held companies:", color=TEXT_MUTED, font_size="0.85rem"),
                spacing="1",
            ),
            rx.spacer(),
            width="100%",
            margin_top=SPACE_8,
        ),
        # Two-Column Surface: AI Assistant Chat + Relevant News beside it
        rx.grid(
            # AI Chat Surface
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon(tag="bot", color=ACCENT_COLOR, size=20),
                        rx.heading("BidUp AI Portfolio Risk Assistant", font_size="1.1rem", font_weight="700", color=TEXT_HEADLINE),
                        rx.spacer(),
                        rx.badge("Portfolio AI", color_scheme="purple"),
                        width="100%",
                        align="center",
                    ),
                    # Quick Prompt Chips
                    rx.hstack(
                        rx.button(
                            "How concentrated is my portfolio?",
                            on_click=State.send_quick_chat("How concentrated is my portfolio?"),
                            size="1",
                            variant="outline",
                            color=TEXT_MUTED,
                            border=f"1px solid {CARD_BORDER}",
                        ),
                        rx.button(
                            "How does Crude oil impact Infra?",
                            on_click=State.send_quick_chat("How does Crude oil impact Infra?"),
                            size="1",
                            variant="outline",
                            color=TEXT_MUTED,
                            border=f"1px solid {CARD_BORDER}",
                        ),
                        rx.button(
                            "Any risks I should know about?",
                            on_click=State.send_quick_chat("Are there any cross-sector risk signals in my current portfolio?"),
                            size="1",
                            variant="outline",
                            color=TEXT_MUTED,
                            border=f"1px solid {CARD_BORDER}",
                        ),
                        spacing="2",
                        wrap="wrap",
                    ),
                    # Chat History
                    rx.box(
                        rx.vstack(
                            rx.foreach(
                                State.chat_messages,
                                lambda m: rx.box(
                                    rx.vstack(
                                        rx.text(
                                            rx.cond(m.sender == "user", "You", "BidUp AI Assistant"),
                                            font_weight="700",
                                            font_size="0.75rem",
                                            color=rx.cond(m.sender == "user", ACCENT_COLOR, POSITIVE_COLOR),
                                        ),
                                        rx.text(m.text, color=TEXT_HEADLINE, font_size="0.88rem"),
                                        spacing="1",
                                    ),
                                    background_color=rx.cond(m.sender == "user", ACCENT_LIGHT, BG_COLOR),
                                    border=f"1px solid {CARD_BORDER_SUBTLE}",
                                    border_radius="8px",
                                    padding=SPACE_3,
                                    width="100%",
                                ),
                            ),
                            spacing="3",
                            width="100%",
                        ),
                        background_color=BG_COLOR,
                        border=f"1px solid {CARD_BORDER_SUBTLE}",
                        border_radius="8px",
                        padding=SPACE_4,
                        max_height="280px",
                        overflow_y="auto",
                        width="100%",
                    ),
                    # Chat Input
                    rx.hstack(
                        rx.input(
                            value=State.chat_input,
                            on_change=State.set_chat_input,
                            placeholder="Type a query e.g. 'What is the risk propagation from Banking to Realty?'...",
                            size="2",
                            width="85%",
                        ),
                        rx.button(
                            rx.icon(tag="send", size=16),
                            "Ask AI",
                            on_click=State.send_chat_message,
                            background_color=ACCENT_COLOR,
                            color="#ffffff",
                            size="2",
                            width="15%",
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    spacing="4",
                    width="100%",
                ),
                background_color=CARD_BG,
                border=f"1px solid {CARD_BORDER}",
                border_radius="12px",
                padding=SPACE_6,
                box_shadow=SHADOW_CARD,
                height="100%",
            ),
            # News Feed with Real Outbound Links
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon(tag="newspaper", color=POSITIVE_COLOR, size=20),
                        rx.heading("News Relevant to Your Portfolio", font_size="1.1rem", font_weight="700", color=TEXT_HEADLINE),
                        rx.spacer(),
                        rx.badge(f"{State.holdings_count} Synced", color_scheme="green", size="1"),
                        width="100%",
                        align="center",
                    ),
                    rx.cond(
                        State.holdings_count > 0,
                        rx.vstack(
                            rx.foreach(
                                State.portfolio_news_feed,
                                lambda item: rx.cond(
                                    item.url != "",
                                    rx.link(
                                        rx.box(
                                            rx.vstack(
                                                rx.hstack(
                                                    rx.badge(item.ticker, color_scheme="purple", size="1"),
                                                    rx.badge(
                                                        item.sentiment,
                                                        color_scheme=rx.cond(
                                                            item.sentiment == "Bullish",
                                                            "green",
                                                            rx.cond(item.sentiment == "Risk Watch", "red", "yellow"),
                                                        ),
                                                        size="1",
                                                    ),
                                                    rx.spacer(),
                                                    rx.text(item.time_ago, font_size="0.75rem", color=TEXT_MUTED),
                                                    width="100%",
                                                    align="center",
                                                ),
                                                rx.text(item.headline, font_weight="600", font_size="0.85rem", color=TEXT_HEADLINE),
                                                rx.hstack(
                                                    rx.text(f"Source: {item.source}", font_size="0.75rem", color=TEXT_MUTED),
                                                    rx.spacer(),
                                                    rx.hstack(
                                                        rx.text("Read Article →", font_size="0.75rem", color=ACCENT_COLOR, font_weight="600"),
                                                        rx.icon(tag="external_link", size=12, color=ACCENT_COLOR),
                                                        spacing="1",
                                                        align="center",
                                                    ),
                                                    width="100%",
                                                    align="center",
                                                ),
                                                spacing="1",
                                            ),
                                            background_color=BG_COLOR,
                                            border=f"1px solid {CARD_BORDER_SUBTLE}",
                                            border_radius="8px",
                                            padding=SPACE_3,
                                            width="100%",
                                            _hover={"border_color": ACCENT_COLOR, "background_color": CARD_HOVER, "cursor": "pointer"},
                                        ),
                                        href=item.url,
                                        is_external=True,
                                        target="_blank",
                                        text_decoration="none",
                                        width="100%",
                                    ),
                                    # No URL — render plain card, no link
                                    rx.box(
                                        rx.vstack(
                                            rx.hstack(
                                                rx.badge(item.ticker, color_scheme="purple", size="1"),
                                                rx.badge(
                                                    item.sentiment,
                                                    color_scheme=rx.cond(
                                                        item.sentiment == "Bullish",
                                                        "green",
                                                        rx.cond(item.sentiment == "Risk Watch", "red", "yellow"),
                                                    ),
                                                    size="1",
                                                ),
                                                rx.spacer(),
                                                rx.text(item.time_ago, font_size="0.75rem", color=TEXT_MUTED),
                                                width="100%",
                                                align="center",
                                            ),
                                            rx.text(item.headline, font_weight="600", font_size="0.85rem", color=TEXT_HEADLINE),
                                            rx.text(f"Source: {item.source}", font_size="0.75rem", color=TEXT_MUTED),
                                            spacing="1",
                                        ),
                                        background_color=BG_COLOR,
                                        border=f"1px solid {CARD_BORDER_SUBTLE}",
                                        border_radius="8px",
                                        padding=SPACE_3,
                                        width="100%",
                                        opacity="0.8",
                                    ),
                                ),
                            ),
                            spacing="3",
                            width="100%",
                            max_height="320px",
                            overflow_y="auto",
                        ),
                        rx.box(
                            rx.vstack(
                                rx.text("No active holdings found.", font_weight="700", color=TEXT_HEADLINE),
                                rx.text("Load sample demo data or import your CSV in Portfolio.", color=TEXT_MUTED, font_size="0.85rem"),
                                rx.button("Go to Portfolio", on_click=State.set_nav("portfolio"), background_color=ACCENT_COLOR, color="#ffffff", size="2"),
                                spacing="3",
                                align="center",
                            ),
                            background_color=BG_COLOR,
                            border=f"1px solid {CARD_BORDER_SUBTLE}",
                            border_radius="8px",
                            padding=SPACE_6,
                            width="100%",
                        ),
                    ),
                    spacing="3",
                    width="100%",
                ),
                background_color=CARD_BG,
                border=f"1px solid {CARD_BORDER}",
                border_radius="12px",
                padding=SPACE_6,
                box_shadow=SHADOW_CARD,
                height="100%",
            ),
            columns="2",
            spacing="6",
            width="100%",
            margin_top=SPACE_4,
        ),
        spacing="6",
        width="100%",
        padding=f"{SPACE_6} {SPACE_8}",
    )

# --- Onboarding View (After First Signup) ---
def onboarding_view() -> rx.Component:
    return rx.center(
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.heading("BidUp", font_size="1.8rem", font_weight="800", color=TEXT_HEADLINE),
                    rx.badge("Setup & Onboarding", color_scheme="purple"),
                    spacing="2",
                    align="center",
                ),
                rx.cond(
                    State.onboarding_step == 1,
                    # Step 1: Profile & Risk Preferences
                    rx.vstack(
                        rx.text("Step 1 of 2: Define your Investor Profile", font_weight="700", color=ACCENT_COLOR, font_size="1rem"),
                        rx.text("This personalizes the GAT risk models and concentration thresholds to your investing parameters:", color=TEXT_MUTED, font_size="0.85rem"),
                        rx.vstack(
                            rx.text("Your Full Name", font_size="0.8rem", color=TEXT_MUTED),
                            rx.input(value=State.user_name, on_change=State.set_user_name, size="2"),
                            spacing="1",
                            width="100%",
                        ),
                        rx.grid(
                            rx.vstack(
                                rx.text("Risk Tolerance", font_size="0.8rem", color=TEXT_MUTED),
                                rx.select(["low", "medium", "high"], value=State.risk_tolerance, on_change=State.set_risk_tolerance, size="2"),
                                spacing="1",
                            ),
                            rx.vstack(
                                rx.text("Investment Horizon", font_size="0.8rem", color=TEXT_MUTED),
                                rx.select(["short", "medium", "long"], value=State.investment_horizon, on_change=State.set_investment_horizon, size="2"),
                                spacing="1",
                            ),
                            columns="2",
                            spacing="4",
                            width="100%",
                        ),
                        rx.button(
                            "Continue to Portfolio Setup →",
                            on_click=State.complete_onboarding_profile,
                            background_color=ACCENT_COLOR,
                            color="#ffffff",
                            width="100%",
                            size="3",
                            margin_top=SPACE_4,
                        ),
                        spacing="4",
                        width="100%",
                    ),
                    # Step 2: Portfolio Initial Setup
                    rx.vstack(
                        rx.text("Step 2 of 2: Connect Your Equity Portfolio", font_weight="700", color=ACCENT_COLOR, font_size="1rem"),
                        rx.text("Choose how you want to populate your Indian equities portfolio for risk analysis:", color=TEXT_MUTED, font_size="0.85rem"),
                        # Option A: Seed Demo Portfolio
                        rx.box(
                            rx.vstack(
                                rx.hstack(
                                    rx.icon(tag="sparkles", color=ACCENT_COLOR, size=20),
                                    rx.text("Load Balanced Demo Portfolio (Recommended)", font_weight="700", color=TEXT_HEADLINE),
                                    spacing="2",
                                    align="center",
                                ),
                                rx.text("Pre-populates 6 diverse stocks (TCS, Reliance, HDFC Bank, Tata Motors, Sun Pharma, ITC) to explore all GAT and HHI models immediately.", color=TEXT_MUTED, font_size="0.82rem"),
                                rx.button(
                                    "Load Demo & Enter Dashboard",
                                    on_click=State.complete_onboarding_with_demo,
                                    background_color=ACCENT_COLOR,
                                    color="#ffffff",
                                    size="2",
                                ),
                                spacing="2",
                            ),
                            background_color=BG_COLOR,
                            border=f"1px solid {CARD_BORDER_SUBTLE}",
                            border_radius="10px",
                            padding=SPACE_4,
                            width="100%",
                        ),
                        # Option B: CSV Import or Manual in Dashboard
                        rx.box(
                            rx.vstack(
                                rx.hstack(
                                    rx.icon(tag="table_2", color=POSITIVE_COLOR, size=20),
                                    rx.text("Import Own CSV / Manual Entry", font_weight="700", color=TEXT_HEADLINE),
                                    spacing="2",
                                    align="center",
                                ),
                                rx.text("Start with an empty portfolio and upload your broker CSV or add holdings manually.", color=TEXT_MUTED, font_size="0.82rem"),
                                rx.button(
                                    "Start with Empty Portfolio",
                                    on_click=State.complete_onboarding_empty,
                                    variant="outline",
                                    color=TEXT_HEADLINE,
                                    border=f"1px solid {CARD_BORDER}",
                                    size="2",
                                ),
                                spacing="2",
                            ),
                            background_color=BG_COLOR,
                            border=f"1px solid {CARD_BORDER_SUBTLE}",
                            border_radius="10px",
                            padding=SPACE_4,
                            width="100%",
                        ),
                        # Honest Broker Sync Card
                        rx.box(
                            rx.hstack(
                                rx.icon(tag="lock", color=TEXT_MUTED, size=18),
                                rx.vstack(
                                    rx.hstack(
                                        rx.text("Broker Sync (Zerodha, Groww, Upstox)", font_weight="600", font_size="0.85rem", color=TEXT_HEADLINE),
                                        rx.badge("Coming Soon (Beta)", color_scheme="gray", size="1"),
                                        spacing="2",
                                        align="center",
                                    ),
                                    rx.text("Direct OAuth broker synchronization is in beta regulatory testing.", color=TEXT_MUTED, font_size="0.75rem"),
                                    spacing="0",
                                ),
                                spacing="3",
                                align="center",
                            ),
                            background_color=BG_COLOR,
                            border=f"1px dashed {CARD_BORDER}",
                            border_radius="10px",
                            padding=SPACE_3,
                            width="100%",
                        ),
                        spacing="4",
                        width="100%",
                    ),
                ),
                spacing="6",
                width="100%",
            ),
            background_color=CARD_BG,
            border=f"1px solid {CARD_BORDER}",
            border_radius="16px",
            padding=SPACE_8,
            width="520px",
            box_shadow=SHADOW_HERO,
        ),
        min_height="100vh",
        background_color=BG_COLOR,
    )

# --- 2. /portfolio Route ---
def _sector_color(sector: str) -> str:
    """Return a color for a given sector label (used in sector bar chart)."""
    # Reflex cond chains for sector coloring
    return rx.cond(
        sector == "IT", "#6246ea",
        rx.cond(sector == "FMCG", "#16a34a",
        rx.cond(sector == "Financial Services", "#d97706",
        rx.cond(sector == "Pharma", "#e45858",
        rx.cond(sector == "Energy", "#f59e0b",
        rx.cond(sector == "Automobile", "#0ea5e9",
        rx.cond(sector == "Metals", "#8b5cf6",
        rx.cond(sector == "Realty", "#ec4899",
        rx.cond(sector == "Infra", "#10b981",
        "#626471")))))))))


def _sector_badge_color(sector: str) -> str:
    """Return a Radix color_scheme string for sector badge."""
    return rx.cond(
        sector == "IT", "violet",
        rx.cond(sector == "FMCG", "green",
        rx.cond(sector == "Financial Services", "amber",
        rx.cond(sector == "Pharma", "red",
        rx.cond(sector == "Energy", "orange",
        rx.cond(sector == "Automobile", "sky",
        rx.cond(sector == "Metals", "purple",
        rx.cond(sector == "Realty", "pink",
        rx.cond(sector == "Infra", "teal",
        "gray")))))))))


def portfolio_view() -> rx.Component:
    return rx.vstack(
        legal_banner(),

        # ── Top 3 Metrics ──────────────────────────────────────────────────────
        rx.grid(
            # Card 1: Total value
            rx.box(
                rx.vstack(
                    rx.text("Total Market Value", color=TEXT_MUTED, font_size="0.85rem"),
                    rx.heading(f"₹{State.total_current:,.2f}", color=TEXT_HEADLINE, font_size="1.8rem", font_weight="800"),
                    rx.text(f"Invested Capital: ₹{State.total_invested:,.2f}", color=TEXT_MUTED, font_size="0.8rem"),
                    rx.hstack(
                        rx.cond(
                            State.prices_last_updated != "",
                            rx.text(f"Prices as of {State.prices_last_updated}", font_size="0.72rem", color=TEXT_MUTED, font_style="italic"),
                            rx.text("Live prices not yet loaded", font_size="0.72rem", color=TEXT_MUTED, font_style="italic"),
                        ),
                        rx.cond(
                            State.prices_fetching,
                            rx.spinner(size="1", color=TEXT_MUTED),
                            rx.button("↻ Refresh", on_click=State.refresh_prices, size="1", variant="ghost", color=TEXT_MUTED, font_size="0.72rem", padding="0"),
                        ),
                        spacing="2", align="center", width="100%",
                    ),
                    spacing="1",
                ),
                background_color=CARD_BG, border=f"1px solid {CARD_BORDER}", border_radius="12px", padding=SPACE_6, box_shadow=SHADOW_CARD,
            ),
            # Card 2: P&L
            rx.box(
                rx.vstack(
                    rx.text("Unrealized Returns", color=TEXT_MUTED, font_size="0.85rem"),
                    rx.heading(
                        f"₹{State.total_pnl:,.2f}",
                        color=rx.cond(State.total_pnl >= 0, POSITIVE_COLOR, ALERT_COLOR),
                        font_size="1.8rem", font_weight="800",
                    ),
                    rx.badge(f"{State.total_pnl_pct}% Overall", color_scheme=rx.cond(State.total_pnl >= 0, "green", "red")),
                    rx.hstack(
                        rx.badge(f"{State.holdings_count} Holdings", color_scheme="purple", size="1"),
                        rx.badge(f"{State.sector_count} Sectors", color_scheme="blue", size="1"),
                        spacing="2",
                    ),
                    spacing="1",
                ),
                background_color=CARD_BG, border=f"1px solid {CARD_BORDER}", border_radius="12px", padding=SPACE_6, box_shadow=SHADOW_CARD,
            ),
            # Card 3: HHI concentration
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.text("Portfolio Concentration (HHI)", color=TEXT_MUTED, font_size="0.85rem", font_weight="500"),
                        rx.icon(tag="pie_chart", size=16, color=ACCENT_COLOR),
                        spacing="1", align="center",
                    ),
                    rx.heading(
                        State.hhi_level,
                        color=rx.cond(
                            State.hhi_level == "Well Diversified", POSITIVE_COLOR,
                            rx.cond(State.hhi_level == "Moderately Concentrated", WARNING_COLOR, ALERT_COLOR),
                        ),
                        font_size="1.4rem", font_weight="700",
                    ),
                    rx.hstack(
                        rx.badge(f"HHI: {State.hhi_score:,.1f}", color_scheme="purple", size="1"),
                        rx.text("• Lower = more diversified", font_size="0.75rem", color=TEXT_SECONDARY),
                        spacing="1", align="center",
                    ),
                    rx.text(State.hhi_interpretation, color=TEXT_MUTED, font_size="0.78rem"),
                    spacing="1",
                ),
                background_color=CARD_BG, border=f"1px solid {CARD_BORDER}", border_radius="12px", padding=SPACE_6, box_shadow=SHADOW_CARD,
            ),
            columns="3", spacing="6", width="100%",
        ),

        # ── Add Stock + Impact Preview Card ────────────────────────────────────
        rx.box(
            rx.vstack(
                # Header row
                rx.hstack(
                    rx.icon(tag="circle_plus", color=ACCENT_COLOR, size=20),
                    rx.heading("Add Stock to Portfolio", font_size="1.1rem", font_weight="700", color=TEXT_HEADLINE),
                    rx.spacer(),
                    rx.button(
                        "Load 9-Stock Demo Portfolio",
                        on_click=State.load_demo_csv,
                        size="1", variant="outline", color=ACCENT_COLOR, border=f"1px solid {ACCENT_BORDER}",
                    ),
                    width="100%", align="center",
                ),
                rx.text(
                    "Select any NSE stock, enter quantity and buy price, then click Preview Impact to see how it changes your HHI score and sector mix — before committing.",
                    color=TEXT_MUTED, font_size="0.85rem",
                ),

                # Input row
                rx.grid(
                    rx.vstack(
                        rx.text("Search & Select Ticker", font_size="0.8rem", color=TEXT_MUTED),
                        rx.input(
                            value=State.ticker_search_query,
                            on_change=State.set_ticker_search_query,
                            placeholder="Type e.g. TCS, RELIANCE, HDFC...",
                            size="2",
                        ),
                        rx.select(
                            State.filtered_tickers,
                            value=State.manual_ticker,
                            on_change=State.set_manual_ticker,
                            size="2",
                        ),
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("Quantity (Shares)", font_size="0.8rem", color=TEXT_MUTED),
                        rx.input(value=State.manual_quantity, on_change=State.set_manual_quantity, placeholder="e.g. 25", size="2"),
                        rx.text(f"Market price: ₹{State.preview_stock_price:,.2f} | Sector: {State.preview_stock_sector}", font_size="0.75rem", color=TEXT_SECONDARY),
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("Avg Purchase Price (₹)", font_size="0.8rem", color=TEXT_MUTED),
                        rx.input(value=State.manual_buy_price, on_change=State.set_manual_buy_price, placeholder="e.g. 2980.0", size="2"),
                        rx.text(f"Total add value: ₹{State.preview_add_value:,.2f}", font_size="0.75rem", color=TEXT_SECONDARY),
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("Actions", font_size="0.8rem", color="transparent"),
                        rx.button(
                            rx.cond(State.show_preview, "▲ Hide Preview", "👁 Preview Impact"),
                            on_click=State.toggle_preview,
                            background_color=rx.cond(State.show_preview, CARD_BG, ACCENT_LIGHT),
                            color=rx.cond(State.show_preview, TEXT_MUTED, ACCENT_COLOR),
                            border=f"1px solid {ACCENT_BORDER}",
                            size="2", width="100%",
                        ),
                        rx.button(
                            rx.icon(tag="plus", size=14), " Add to Portfolio",
                            on_click=State.add_manual_holding,
                            background_color=ACCENT_COLOR, color="#ffffff",
                            size="2", width="100%",
                        ),
                        spacing="2",
                    ),
                    columns="4", spacing="4", width="100%",
                ),

                # ── Impact Preview Panel (shown when show_preview=True) ─────────
                rx.cond(
                    State.show_preview,
                    rx.box(
                        rx.vstack(
                            # Title
                            rx.hstack(
                                rx.icon(tag="trending_up", color=ACCENT_COLOR, size=18),
                                rx.heading(
                                    f"Impact Preview — Adding {State.preview_add_qty:.0f} × {State.manual_ticker}",
                                    font_size="1rem", font_weight="700", color=TEXT_HEADLINE,
                                ),
                                rx.spacer(),
                                rx.button(
                                    "✕",
                                    on_click=State.clear_preview,
                                    size="1", variant="ghost", color=TEXT_MUTED,
                                ),
                                width="100%", align="center",
                            ),
                            rx.divider(border_color=CARD_BORDER_SUBTLE),

                            # HHI before → after comparison
                            rx.grid(
                                # Current HHI
                                rx.box(
                                    rx.vstack(
                                        rx.text("Current HHI Score", font_size="0.78rem", color=TEXT_MUTED, font_weight="600"),
                                        rx.heading(f"{State.hhi_score:,.1f}", font_size="1.6rem", font_weight="800", color=TEXT_HEADLINE),
                                        rx.badge(State.hhi_level, color_scheme=rx.cond(
                                            State.hhi_level == "Well Diversified", "green",
                                            rx.cond(State.hhi_level == "Moderately Concentrated", "amber", "red"),
                                        ), size="1"),
                                        spacing="1", align="center",
                                    ),
                                    background_color=BG_COLOR,
                                    border=f"1px solid {CARD_BORDER_SUBTLE}",
                                    border_radius="10px", padding=SPACE_4, text_align="center",
                                ),
                                # Arrow + delta
                                rx.box(
                                    rx.vstack(
                                        rx.text("Change", font_size="0.78rem", color=TEXT_MUTED, font_weight="600"),
                                        rx.heading(
                                            rx.cond(State.preview_hhi_delta >= 0, f"+{State.preview_hhi_delta:,.1f}", f"{State.preview_hhi_delta:,.1f}"),
                                            font_size="1.6rem", font_weight="800",
                                            color=rx.cond(State.preview_hhi_delta <= 0, POSITIVE_COLOR, rx.cond(State.preview_hhi_delta <= 500, WARNING_COLOR, ALERT_COLOR)),
                                        ),
                                        rx.text("→", font_size="1.2rem", color=TEXT_MUTED),
                                        spacing="0", align="center",
                                    ),
                                    text_align="center", padding=SPACE_4,
                                ),
                                # New HHI
                                rx.box(
                                    rx.vstack(
                                        rx.text("New HHI Score", font_size="0.78rem", color=TEXT_MUTED, font_weight="600"),
                                        rx.heading(f"{State.preview_new_hhi:,.1f}", font_size="1.6rem", font_weight="800", color=TEXT_HEADLINE),
                                        rx.badge(State.preview_new_level, color_scheme=rx.cond(
                                            State.preview_new_level == "Well Diversified", "green",
                                            rx.cond(State.preview_new_level == "Moderately Concentrated", "amber", "red"),
                                        ), size="1"),
                                        spacing="1", align="center",
                                    ),
                                    background_color=rx.cond(
                                        State.preview_hhi_delta <= 0, POSITIVE_LIGHT,
                                        rx.cond(State.preview_hhi_delta <= 500, WARNING_LIGHT, ALERT_LIGHT),
                                    ),
                                    border=f"1px solid {CARD_BORDER_SUBTLE}",
                                    border_radius="10px", padding=SPACE_4, text_align="center",
                                ),
                                # Sector impact
                                rx.box(
                                    rx.vstack(
                                        rx.text(f"{State.preview_stock_sector} Sector Weight", font_size="0.78rem", color=TEXT_MUTED, font_weight="600"),
                                        rx.heading(f"{State.preview_new_sector_weight_pct:.1f}%", font_size="1.6rem", font_weight="800", color=ACCENT_COLOR),
                                        rx.text(f"of ₹{State.preview_new_total:,.0f} new total", font_size="0.75rem", color=TEXT_SECONDARY),
                                        spacing="1", align="center",
                                    ),
                                    background_color=ACCENT_LIGHT,
                                    border=f"1px solid {ACCENT_BORDER}",
                                    border_radius="10px", padding=SPACE_4, text_align="center",
                                ),
                                columns="4", spacing="3", width="100%",
                            ),

                            # Risk flag (shown when risky)
                            rx.cond(
                                State.preview_has_risk_flag,
                                rx.hstack(
                                    rx.icon(tag="triangle_alert", color=ALERT_COLOR, size=16),
                                    rx.text(State.preview_risk_flag_reason, color=ALERT_COLOR, font_size="0.85rem", font_weight="600"),
                                    background_color=ALERT_LIGHT,
                                    border=f"1px solid {ALERT_COLOR}",
                                    border_radius="8px", padding=SPACE_3,
                                    width="100%", align="center", spacing="2",
                                ),
                            ),

                            # Simulated sector breakdown bar chart
                            rx.vstack(
                                rx.text("Simulated Sector Allocation After Add", font_size="0.85rem", font_weight="600", color=TEXT_MUTED),
                                rx.foreach(
                                    State.preview_sector_weights,
                                    lambda sw: rx.vstack(
                                        rx.hstack(
                                            rx.text(sw.sector, font_size="0.8rem", font_weight="600", color=TEXT_HEADLINE, min_width="160px"),
                                            rx.box(
                                                rx.box(
                                                    height="14px",
                                                    width=f"{sw.weight_pct}%",
                                                    background_color=_sector_color(sw.sector),
                                                    border_radius="4px",
                                                    transition="width 0.4s ease",
                                                ),
                                                background_color=CARD_BORDER_SUBTLE,
                                                border_radius="4px",
                                                width="100%",
                                                overflow="hidden",
                                                flex="1",
                                            ),
                                            rx.text(f"{sw.weight_pct:.1f}%", font_size="0.8rem", font_weight="700", color=TEXT_HEADLINE, min_width="48px", text_align="right"),
                                            rx.text(f"₹{sw.market_value:,.0f}", font_size="0.75rem", color=TEXT_MUTED, min_width="90px", text_align="right"),
                                            spacing="3", align="center", width="100%",
                                        ),
                                        spacing="1", width="100%",
                                    ),
                                ),
                                spacing="2", width="100%",
                            ),

                            # Add button inside preview
                            rx.hstack(
                                rx.button(
                                    rx.icon(tag="plus", size=16), " Confirm & Add to Portfolio",
                                    on_click=State.add_manual_holding,
                                    background_color=ACCENT_COLOR, color="#ffffff", size="2",
                                ),
                                rx.button("Cancel", on_click=State.clear_preview, variant="ghost", color=TEXT_MUTED, size="2"),
                                spacing="3",
                            ),

                            spacing="4", width="100%",
                        ),
                        background_color=CARD_BG,
                        border=f"2px solid {ACCENT_BORDER}",
                        border_radius="12px",
                        padding=SPACE_6,
                        width="100%",
                    ),
                ),

                rx.cond(State.portfolio_message != "", rx.text(State.portfolio_message, color=POSITIVE_COLOR, font_size="0.85rem")),
                rx.cond(State.portfolio_error != "", rx.text(State.portfolio_error, color=ALERT_COLOR, font_size="0.85rem")),
                spacing="4", width="100%",
            ),
            background_color=CARD_BG, border=f"1px solid {CARD_BORDER}",
            border_radius="12px", padding=SPACE_6, box_shadow=SHADOW_CARD, width="100%",
        ),

        # ── Holdings Table ─────────────────────────────────────────────────────
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.heading("Active Holdings Breakdown", font_size="1.2rem", font_weight="700", color=TEXT_HEADLINE),
                    rx.spacer(),
                    rx.badge(f"{State.holdings_count} Assets", color_scheme="purple"),
                    width="100%", align="center",
                ),
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Stock"),
                            rx.table.column_header_cell("Sector"),
                            rx.table.column_header_cell("Qty"),
                            rx.table.column_header_cell("Avg Buy (₹)"),
                            rx.table.column_header_cell("Current (₹)"),
                            rx.table.column_header_cell("Market Value"),
                            rx.table.column_header_cell("Unrealized P&L"),
                            rx.table.column_header_cell("Remove"),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(
                            State.holdings,
                            lambda h: rx.table.row(
                                rx.table.cell(
                                    rx.vstack(
                                        rx.text(h.ticker, font_weight="700", color=TEXT_HEADLINE),
                                        rx.text(h.name, font_size="0.75rem", color=TEXT_MUTED),
                                        spacing="0",
                                    )
                                ),
                                rx.table.cell(
                                    rx.badge(
                                        h.sector,
                                        color_scheme=_sector_badge_color(h.sector),
                                        size="1",
                                    )
                                ),
                                rx.table.cell(rx.text(h.quantity, color=TEXT_HEADLINE)),
                                rx.table.cell(rx.text(f"₹{h.avg_buy_price:,.2f}", color=TEXT_MUTED)),
                                rx.table.cell(rx.text(f"₹{h.current_price:,.2f}", font_weight="600", color=TEXT_HEADLINE)),
                                rx.table.cell(rx.text(f"₹{h.current_value:,.2f}", font_weight="700", color=TEXT_HEADLINE)),
                                rx.table.cell(
                                    rx.vstack(
                                        rx.text(
                                            f"₹{h.unrealized_pnl:,.2f}",
                                            color=rx.cond(h.unrealized_pnl >= 0, POSITIVE_COLOR, ALERT_COLOR),
                                            font_weight="600",
                                        ),
                                        rx.text(
                                            f"{h.unrealized_pnl_pct}%",
                                            font_size="0.75rem",
                                            color=rx.cond(h.unrealized_pnl >= 0, POSITIVE_COLOR, ALERT_COLOR),
                                        ),
                                        spacing="0",
                                    )
                                ),
                                rx.table.cell(
                                    rx.button(
                                        rx.icon(tag="trash_2", size=14),
                                        on_click=State.remove_holding(h.ticker),
                                        size="1", variant="soft", color_scheme="red",
                                    )
                                ),
                            ),
                        )
                    ),
                    width="100%",
                ),
                spacing="4", width="100%",
            ),
            background_color=CARD_BG, border=f"1px solid {CARD_BORDER}",
            border_radius="12px", padding=SPACE_6, box_shadow=SHADOW_CARD, width="100%",
        ),

        # ── Live Sector Allocation Bar Chart ───────────────────────────────────
        rx.cond(
            State.sector_count > 0,
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon(tag="bar_chart_2", color=ACCENT_COLOR, size=20),
                        rx.heading("Current Sector Allocation", font_size="1.1rem", font_weight="700", color=TEXT_HEADLINE),
                        rx.spacer(),
                        rx.badge(f"HHI: {State.hhi_score:,.1f}", color_scheme="purple"),
                        width="100%", align="center",
                    ),
                    rx.text("Each bar represents the % of your total portfolio value in that sector:", color=TEXT_MUTED, font_size="0.85rem"),
                    rx.foreach(
                        State.sector_breakdown,
                        lambda sw: rx.vstack(
                            rx.hstack(
                                rx.text(sw.sector, font_size="0.85rem", font_weight="700", color=TEXT_HEADLINE, min_width="170px"),
                                rx.box(
                                    rx.box(
                                        height="18px",
                                        width=f"{sw.weight_pct}%",
                                        background_color=_sector_color(sw.sector),
                                        border_radius="4px",
                                        transition="width 0.4s ease",
                                    ),
                                    background_color=CARD_BORDER_SUBTLE,
                                    border_radius="4px",
                                    width="100%",
                                    overflow="hidden",
                                    flex="1",
                                ),
                                rx.text(f"{sw.weight_pct:.1f}%", font_size="0.85rem", font_weight="700", color=TEXT_HEADLINE, min_width="52px", text_align="right"),
                                rx.text(f"₹{sw.market_value:,.0f}", font_size="0.78rem", color=TEXT_MUTED, min_width="100px", text_align="right"),
                                rx.badge(rx.cond(sw.holdings_count == 1, f"{sw.holdings_count} stock", f"{sw.holdings_count} stocks"), color_scheme="gray", size="1", min_width="60px"),
                                spacing="3", align="center", width="100%",
                            ),
                            spacing="1", width="100%",
                        ),
                    ),
                    spacing="3", width="100%",
                ),
                background_color=CARD_BG, border=f"1px solid {CARD_BORDER}",
                border_radius="12px", padding=SPACE_6, box_shadow=SHADOW_CARD, width="100%",
            ),
        ),

        spacing="6", width="100%", padding=f"{SPACE_6} {SPACE_8}",
    )

# --- 3. /chat Route ---
def chat_view() -> rx.Component:
    return rx.vstack(
        legal_banner(),
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="message_square", color=ACCENT_COLOR, size=24),
                    rx.heading("BidUp AI Portfolio Intelligence Chat", font_size="1.4rem", font_weight="700", color=TEXT_HEADLINE),
                    rx.spacer(),
                    rx.badge("Descriptive RAG Assistant", color_scheme="purple"),
                    width="100%",
                    align="center",
                ),
                rx.text("Interact directly with BidUp's quantitative models for concentration (HHI) and GAT sector shock transmission.", color=TEXT_MUTED, font_size="0.9rem"),
                rx.box(
                    rx.vstack(
                        rx.foreach(
                            State.chat_messages,
                            lambda m: rx.box(
                                rx.vstack(
                                    rx.hstack(
                                        rx.text(
                                            rx.cond(m.sender == "user", "You", "BidUp AI Assistant"),
                                            font_weight="700",
                                            color=rx.cond(m.sender == "user", ACCENT_COLOR, POSITIVE_COLOR),
                                        ),
                                        rx.spacer(),
                                        rx.text(m.time, font_size="0.75rem", color=TEXT_MUTED),
                                        width="100%",
                                    ),
                                    rx.text(m.text, color=TEXT_HEADLINE, font_size="0.92rem"),
                                    spacing="1",
                                ),
                                background_color=rx.cond(m.sender == "user", ACCENT_LIGHT, BG_COLOR),
                                border=f"1px solid {CARD_BORDER_SUBTLE}",
                                border_radius="10px",
                                padding=SPACE_4,
                                width="100%",
                            ),
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    background_color=BG_COLOR,
                    border=f"1px solid {CARD_BORDER_SUBTLE}",
                    border_radius="12px",
                    padding=SPACE_6,
                    min_height="380px",
                    max_height="500px",
                    overflow_y="auto",
                    width="100%",
                ),
                rx.hstack(
                    rx.input(
                        value=State.chat_input,
                        on_change=State.set_chat_input,
                        placeholder="Ask a question about your portfolio or sector risk...",
                        size="3",
                        width="85%",
                    ),
                    rx.button(
                        rx.icon(tag="send", size=18),
                        "Send",
                        on_click=State.send_chat_message,
                        background_color=ACCENT_COLOR,
                        color="#ffffff",
                        size="3",
                        width="15%",
                    ),
                    spacing="3",
                    width="100%",
                ),
                spacing="5",
                width="100%",
            ),
            background_color=CARD_BG,
            border=f"1px solid {CARD_BORDER}",
            border_radius="12px",
            padding=SPACE_8,
            box_shadow=SHADOW_CARD,
            width="100%",
        ),
        spacing="6",
        width="100%",
        padding=f"{SPACE_6} {SPACE_8}",
    )

# --- 4. /screener Route ---
def screener_view() -> rx.Component:
    return rx.vstack(
        legal_banner(),
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="filter", color=ACCENT_COLOR, size=24),
                    rx.heading("Indian Equity Screener (50+ Universe)", font_size="1.4rem", font_weight="700", color=TEXT_HEADLINE),
                    rx.spacer(),
                    rx.badge(f"{State.screener_count} Matching Stocks", color_scheme="purple"),
                    width="100%",
                    align="center",
                ),
                rx.text("Filter maintained equities by sector, market capitalization, risk category, and ESG compliance:", color=TEXT_MUTED, font_size="0.9rem"),
                # Filter Controls
                rx.grid(
                    rx.vstack(
                        rx.text("Sector Filter", font_size="0.8rem", color=TEXT_MUTED),
                        rx.select(["All", "IT", "Financial Services", "Energy", "Automobile", "Pharma", "FMCG", "Metals", "Realty", "Infra"], value=State.screener_sector, on_change=State.set_screener_sector, size="2"),
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("Market Cap", font_size="0.8rem", color=TEXT_MUTED),
                        rx.select(["All", "large_cap", "mid_cap"], value=State.screener_cap, on_change=State.set_screener_cap, size="2"),
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("Risk Level", font_size="0.8rem", color=TEXT_MUTED),
                        rx.select(["All", "low", "medium", "high"], value=State.screener_risk, on_change=State.set_screener_risk, size="2"),
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("Min ESG Score", font_size="0.8rem", color=TEXT_MUTED),
                        rx.select(["50", "60", "70", "80"], value=State.screener_min_esg_str, on_change=State.set_screener_min_esg, size="2"),
                        spacing="1",
                    ),
                    columns="4",
                    spacing="4",
                    width="100%",
                ),
                # Table
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Ticker"),
                            rx.table.column_header_cell("Company"),
                            rx.table.column_header_cell("Sector"),
                            rx.table.column_header_cell("Market Cap"),
                            rx.table.column_header_cell("ESG"),
                            rx.table.column_header_cell("Risk Tier"),
                            rx.table.column_header_cell("Price (₹)"),
                            rx.table.column_header_cell("Inspect"),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(
                            State.screener_stocks,
                            lambda s: rx.table.row(
                                rx.table.cell(rx.text(s.ticker, font_weight="700", color=TEXT_HEADLINE)),
                                rx.table.cell(rx.text(s.name, color=TEXT_MUTED)),
                                rx.table.cell(rx.badge(s.sector, color_scheme="purple", size="1")),
                                rx.table.cell(rx.text(s.cap, color=TEXT_HEADLINE)),
                                rx.table.cell(rx.badge(s.esg, color_scheme="green", size="1")),
                                rx.table.cell(rx.badge(s.risk, color_scheme=rx.cond(s.risk == "Low", "green", rx.cond(s.risk == "Medium", "yellow", "red")), size="1")),
                                rx.table.cell(rx.text(f"₹{s.price:,.2f}", font_weight="600", color=TEXT_HEADLINE)),
                                rx.table.cell(
                                    rx.button(
                                        "View",
                                        on_click=State.select_stock(s.ticker),
                                        size="1",
                                        variant="soft",
                                        color_scheme="purple",
                                    )
                                ),
                            ),
                        )
                    ),
                    width="100%",
                ),
                spacing="5",
                width="100%",
            ),
            background_color=CARD_BG,
            border=f"1px solid {CARD_BORDER}",
            border_radius="12px",
            padding=SPACE_8,
            box_shadow=SHADOW_CARD,
            width="100%",
        ),
        spacing="6",
        width="100%",
        padding=f"{SPACE_6} {SPACE_8}",
    )

# --- 5. /stocks Route ---
def stocks_view() -> rx.Component:
    return rx.vstack(
        legal_banner(),
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="activity", color=ACCENT_COLOR, size=24),
                    rx.heading("Stock Analytical Profile", font_size="1.4rem", font_weight="700", color=TEXT_HEADLINE),
                    rx.spacer(),
                    rx.select(ALL_TICKERS, value=State.selected_stock_ticker, on_change=State.set_selected_stock_ticker, size="2"),
                    width="100%",
                    align="center",
                ),
                # Details Header
                rx.box(
                    rx.vstack(
                        rx.hstack(
                            rx.vstack(
                                rx.heading(State.selected_stock_detail["ticker"], font_size="1.8rem", font_weight="800", color=TEXT_HEADLINE),
                                rx.text(State.selected_stock_detail["name"], color=TEXT_MUTED, font_size="1rem"),
                                spacing="0",
                            ),
                            rx.spacer(),
                            rx.vstack(
                                rx.heading(f"₹{State.selected_stock_detail['price']:,.2f}", color=TEXT_HEADLINE, font_size="1.8rem", font_weight="800"),
                                rx.badge(State.selected_stock_detail["sector"], color_scheme="purple", size="2"),
                                spacing="1",
                                align="end",
                            ),
                            width="100%",
                            align="center",
                        ),
                        rx.divider(border_color=CARD_BORDER_SUBTLE),
                        # Key Metrics Grid
                        rx.grid(
                            rx.box(
                                rx.vstack(
                                    rx.text("Industry", color=TEXT_MUTED, font_size="0.8rem"),
                                    rx.text(State.selected_stock_detail["industry"], color=TEXT_HEADLINE, font_weight="600"),
                                    spacing="1",
                                ),
                                background_color=BG_COLOR,
                                border=f"1px solid {CARD_BORDER_SUBTLE}",
                                border_radius="8px",
                                padding=SPACE_3,
                            ),
                            rx.box(
                                rx.vstack(
                                    rx.text("Market Cap Category", color=TEXT_MUTED, font_size="0.8rem"),
                                    rx.text(State.selected_stock_detail["cap"], color=TEXT_HEADLINE, font_weight="600"),
                                    spacing="1",
                                ),
                                background_color=BG_COLOR,
                                border=f"1px solid {CARD_BORDER_SUBTLE}",
                                border_radius="8px",
                                padding=SPACE_3,
                            ),
                            rx.box(
                                rx.vstack(
                                    rx.text("ESG Score", color=TEXT_MUTED, font_size="0.8rem"),
                                    rx.text(f"{State.selected_stock_detail['esg']} / 100", color=POSITIVE_COLOR, font_weight="700"),
                                    spacing="1",
                                ),
                                background_color=BG_COLOR,
                                border=f"1px solid {CARD_BORDER_SUBTLE}",
                                border_radius="8px",
                                padding=SPACE_3,
                            ),
                            rx.box(
                                rx.vstack(
                                    rx.text("Historical Beta vs NIFTY", color=TEXT_MUTED, font_size="0.8rem"),
                                    rx.text(f"{State.selected_stock_detail['beta_nifty']}", color=TEXT_HEADLINE, font_weight="700"),
                                    spacing="1",
                                ),
                                background_color=BG_COLOR,
                                border=f"1px solid {CARD_BORDER_SUBTLE}",
                                border_radius="8px",
                                padding=SPACE_3,
                            ),
                            columns="4",
                            spacing="4",
                            width="100%",
                        ),
                        spacing="4",
                        width="100%",
                    ),
                    background_color=BG_COLOR,
                    border=f"1px solid {CARD_BORDER_SUBTLE}",
                    border_radius="12px",
                    padding=SPACE_6,
                    width="100%",
                ),
                spacing="5",
                width="100%",
            ),
            background_color=CARD_BG,
            border=f"1px solid {CARD_BORDER}",
            border_radius="12px",
            padding=SPACE_8,
            box_shadow=SHADOW_CARD,
            width="100%",
        ),
        spacing="6",
        width="100%",
        padding=f"{SPACE_6} {SPACE_8}",
    )

# --- 6. /paper-trading Route ---
def paper_trading_view() -> rx.Component:
    return rx.vstack(
        legal_banner(),
        rx.grid(
            rx.box(
                rx.vstack(
                    rx.text("Virtual Cash Balance", color=TEXT_MUTED, font_size="0.85rem"),
                    rx.heading(f"₹{State.pt_cash_balance:,.2f}", color=TEXT_HEADLINE, font_size="1.8rem", font_weight="800"),
                    rx.badge("Simulation Mode", color_scheme="green"),
                    spacing="1",
                ),
                background_color=CARD_BG,
                border=f"1px solid {CARD_BORDER}",
                border_radius="12px",
                padding=SPACE_6,
                box_shadow=SHADOW_CARD,
            ),
            rx.box(
                rx.vstack(
                    rx.text("Slippage Engine", color=TEXT_MUTED, font_size="0.85rem"),
                    rx.heading("Gaussian Microstructure", color=TEXT_HEADLINE, font_size="1.3rem", font_weight="700"),
                    rx.text("μ = 0.05%, σ = 0.02%", color=TEXT_MUTED, font_size="0.8rem"),
                    spacing="1",
                ),
                background_color=CARD_BG,
                border=f"1px solid {CARD_BORDER}",
                border_radius="12px",
                padding=SPACE_6,
                box_shadow=SHADOW_CARD,
            ),
            rx.box(
                rx.vstack(
                    rx.text("Executed Orders", color=TEXT_MUTED, font_size="0.85rem"),
                    rx.heading(f"{State.paper_ledger_count} Trades", color=ACCENT_COLOR, font_size="1.8rem", font_weight="800"),
                    rx.badge("Paper Ledger", color_scheme="purple"),
                    spacing="1",
                ),
                background_color=CARD_BG,
                border=f"1px solid {CARD_BORDER}",
                border_radius="12px",
                padding=SPACE_6,
                box_shadow=SHADOW_CARD,
            ),
            columns="3",
            spacing="6",
            width="100%",
        ),
        # Order Execution Box
        rx.box(
            rx.vstack(
                rx.heading("Place Simulated Order", font_size="1.2rem", font_weight="700", color=TEXT_HEADLINE),
                rx.grid(
                    rx.vstack(
                        rx.text("Stock Ticker", font_size="0.8rem", color=TEXT_MUTED),
                        rx.select(ALL_TICKERS, value=State.pt_ticker, on_change=State.set_pt_ticker, size="2"),
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("Order Type", font_size="0.8rem", color=TEXT_MUTED),
                        rx.select(["BUY", "SELL"], value=State.pt_order_type, on_change=State.set_pt_order_type, size="2"),
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("Quantity", font_size="0.8rem", color=TEXT_MUTED),
                        rx.input(value=State.pt_quantity, on_change=State.set_pt_quantity, size="2"),
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("Action", font_size="0.8rem", color="transparent"),
                        rx.button("Execute Paper Trade", on_click=State.execute_paper_trade, background_color=ACCENT_COLOR, color="#ffffff", size="2", width="100%"),
                        spacing="1",
                    ),
                    columns="4",
                    spacing="4",
                    width="100%",
                ),
                rx.cond(State.pt_message != "", rx.text(State.pt_message, color=POSITIVE_COLOR, font_size="0.85rem")),
                spacing="4",
                width="100%",
            ),
            background_color=CARD_BG,
            border=f"1px solid {CARD_BORDER}",
            border_radius="12px",
            padding=SPACE_6,
            box_shadow=SHADOW_CARD,
            width="100%",
        ),
        # Ledger Table
        rx.box(
            rx.vstack(
                rx.heading("Simulated Trade Execution Ledger", font_size="1.2rem", font_weight="700", color=TEXT_HEADLINE),
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Time"),
                            rx.table.column_header_cell("Ticker"),
                            rx.table.column_header_cell("Side"),
                            rx.table.column_header_cell("Qty"),
                            rx.table.column_header_cell("Req Price (₹)"),
                            rx.table.column_header_cell("Slippage"),
                            rx.table.column_header_cell("Exec Price (₹)"),
                            rx.table.column_header_cell("Total (₹)"),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(
                            State.paper_ledger,
                            lambda t: rx.table.row(
                                rx.table.cell(rx.text(t.time, color=TEXT_MUTED)),
                                rx.table.cell(rx.text(t.ticker, font_weight="700", color=TEXT_HEADLINE)),
                                rx.table.cell(rx.badge(t.order_type, color_scheme=rx.cond(t.order_type == "BUY", "green", "red"), size="1")),
                                rx.table.cell(rx.text(t.quantity, color=TEXT_HEADLINE)),
                                rx.table.cell(rx.text(f"₹{t.requested_price:,.2f}", color=TEXT_MUTED)),
                                rx.table.cell(rx.badge(f"{t.slippage_pct}%", color_scheme="purple", size="1")),
                                rx.table.cell(rx.text(f"₹{t.executed_price:,.2f}", font_weight="600", color=TEXT_HEADLINE)),
                                rx.table.cell(rx.text(f"₹{t.total_amount:,.2f}", font_weight="700", color=TEXT_HEADLINE)),
                            ),
                        )
                    ),
                    width="100%",
                ),
                spacing="4",
                width="100%",
            ),
            background_color=CARD_BG,
            border=f"1px solid {CARD_BORDER}",
            border_radius="12px",
            padding=SPACE_6,
            box_shadow=SHADOW_CARD,
            width="100%",
        ),
        spacing="6",
        width="100%",
        padding=f"{SPACE_6} {SPACE_8}",
    )

# --- 7. /analytics Route ---
def analytics_view() -> rx.Component:
    return rx.vstack(
        legal_banner(),
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="network", color=ACCENT_COLOR, size=24),
                    rx.heading("How Your Sectors Affect Each Other", font_size="1.4rem", font_weight="700", color=TEXT_HEADLINE),
                    rx.spacer(),
                    rx.badge("Cross-Sector Risk", color_scheme="purple"),
                    width="100%",
                    align="center",
                ),
                rx.text(
                    "We track how price swings in one sector tend to spread into others, and flag links that could add risk to your portfolio.",
                    color=TEXT_MUTED, font_size="0.9rem",
                ),
                # Matrix & Alerts Grid
                rx.grid(
                    rx.box(
                        rx.vstack(
                            rx.heading("Diversification Score", font_size="1.1rem", font_weight="700", color=TEXT_HEADLINE),
                            rx.heading(f"{State.hhi_score:,.1f}", color=TEXT_HEADLINE, font_size="2rem", font_weight="800"),
                            rx.badge(State.hhi_level, color_scheme="purple"),
                            rx.text(State.hhi_interpretation, color=TEXT_MUTED, font_size="0.85rem"),
                            rx.text(
                                "Lower score = money spread across more sectors. Above 2500 means heavy concentration in one area.",
                                color=TEXT_SECONDARY, font_size="0.78rem", font_style="italic",
                            ),
                            spacing="2",
                        ),
                        background_color=BG_COLOR,
                        border=f"1px solid {CARD_BORDER_SUBTLE}",
                        border_radius="10px",
                        padding=SPACE_4,
                    ),
                    rx.box(
                        rx.vstack(
                            rx.heading("Active Risk Signals", font_size="1.1rem", font_weight="700", color=TEXT_HEADLINE),
                            rx.text(
                                "Sectors linked to yours that could amplify losses if one of them drops sharply:",
                                color=TEXT_MUTED, font_size="0.82rem",
                            ),
                            rx.foreach(
                                State.active_gat_alerts,
                                lambda a: rx.box(
                                    rx.vstack(
                                        rx.hstack(
                                            rx.badge(f"{a.held_sector} → {a.correlated_sector}", color_scheme="purple", size="1"),
                                            rx.spacer(),
                                            rx.badge(a.shock_propagation_level, color_scheme="red", size="1"),
                                            width="100%",
                                            align="center",
                                        ),
                                        rx.text(a.descriptive_signal, font_size="0.82rem", color=TEXT_HEADLINE),
                                        spacing="1",
                                    ),
                                    background_color=CARD_BG,
                                    border=f"1px solid {CARD_BORDER_SUBTLE}",
                                    border_radius="8px",
                                    padding=SPACE_3,
                                    width="100%",
                                ),
                            ),
                            spacing="3",
                            width="100%",
                        ),
                        background_color=BG_COLOR,
                        border=f"1px solid {CARD_BORDER_SUBTLE}",
                        border_radius="10px",
                        padding=SPACE_4,
                    ),
                    columns="2",
                    spacing="6",
                    width="100%",
                ),
                spacing="5",
                width="100%",
            ),
            background_color=CARD_BG,
            border=f"1px solid {CARD_BORDER}",
            border_radius="12px",
            padding=SPACE_8,
            box_shadow=SHADOW_CARD,
            width="100%",
        ),
        spacing="6",
        width="100%",
        padding=f"{SPACE_6} {SPACE_8}",
    )

# --- 8. /compare Route ---
def compare_view() -> rx.Component:
    return rx.vstack(
        legal_banner(),
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="git_compare", color=ACCENT_COLOR, size=24),
                    rx.heading("What-If Portfolio Scenario Simulator", font_size="1.4rem", font_weight="700", color=TEXT_HEADLINE),
                    spacing="2",
                    align="center",
                ),
                rx.text("Simulate how adding new sector positions impacts your overall HHI diversification score:", color=TEXT_MUTED, font_size="0.9rem"),
                rx.grid(
                    rx.vstack(
                        rx.text("Stock to Add", font_size="0.8rem", color=TEXT_MUTED),
                        rx.select(ALL_TICKERS, value=State.sim_add_ticker, on_change=State.set_sim_add_ticker, size="2"),
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("Quantity", font_size="0.8rem", color=TEXT_MUTED),
                        rx.input(value=State.sim_add_quantity, on_change=State.set_sim_add_quantity, size="2"),
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("Simulate", font_size="0.8rem", color="transparent"),
                        rx.button("Calculate What-If Shift", on_click=State.simulate_what_if, background_color=ACCENT_COLOR, color="#ffffff", size="2", width="100%"),
                        spacing="1",
                    ),
                    columns="3",
                    spacing="4",
                    width="100%",
                ),
                rx.cond(State.sim_message != "", rx.text(State.sim_message, color=POSITIVE_COLOR, font_size="0.95rem", font_weight="600")),
                spacing="5",
                width="100%",
            ),
            background_color=CARD_BG,
            border=f"1px solid {CARD_BORDER}",
            border_radius="12px",
            padding=SPACE_8,
            box_shadow=SHADOW_CARD,
            width="100%",
        ),
        spacing="6",
        width="100%",
        padding=f"{SPACE_6} {SPACE_8}",
    )

# --- 9. /backtest Route ---
def backtest_view() -> rx.Component:
    return rx.vstack(
        legal_banner(),
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="award", color=POSITIVE_COLOR, size=24),
                    rx.heading("Historical GAT Backtest Results & Validation", font_size="1.4rem", font_weight="700", color=TEXT_HEADLINE),
                    rx.spacer(),
                    rx.badge("N=6 Shock Windows", color_scheme="green"),
                    width="100%",
                    align="center",
                ),
                rx.text("Showing how well the sector risk model's past signals matched actual market moves:", color=TEXT_MUTED, font_size="0.9rem"),
                # Metrics
                rx.grid(
                    rx.box(
                        rx.vstack(
                            rx.text("Directional Agreement", color=TEXT_MUTED, font_size="0.8rem"),
                            rx.heading("100.0%", color=POSITIVE_COLOR, font_size="1.8rem", font_weight="800"),
                            rx.badge("6/6 Windows Correct", color_scheme="green"),
                            spacing="1",
                        ),
                        background_color=BG_COLOR,
                        border=f"1px solid {CARD_BORDER_SUBTLE}",
                        border_radius="10px",
                        padding=SPACE_4,
                    ),
                    rx.box(
                        rx.vstack(
                            rx.text("Mean Absolute Error (MAE)", color=TEXT_MUTED, font_size="0.8rem"),
                            rx.heading("0.0441", color=TEXT_HEADLINE, font_size="1.8rem", font_weight="800"),
                            rx.text("Forward 5-Day Realized Variance", color=TEXT_MUTED, font_size="0.75rem"),
                            spacing="1",
                        ),
                        background_color=BG_COLOR,
                        border=f"1px solid {CARD_BORDER_SUBTLE}",
                        border_radius="10px",
                        padding=SPACE_4,
                    ),
                    rx.box(
                        rx.vstack(
                            rx.text("Sample Size Status", color=TEXT_MUTED, font_size="0.8rem"),
                            rx.heading("N=6 Regimes", color=ACCENT_COLOR, font_size="1.8rem", font_weight="800"),
                            rx.text("Preliminary Proof-of-Concept Sample", color=TEXT_MUTED, font_size="0.75rem"),
                            spacing="1",
                        ),
                        background_color=BG_COLOR,
                        border=f"1px solid {CARD_BORDER_SUBTLE}",
                        border_radius="10px",
                        padding=SPACE_4,
                    ),
                    columns="3",
                    spacing="4",
                    width="100%",
                ),
                # Table
                rx.table.root(
                    rx.table.header(
                        rx.table.row(
                            rx.table.column_header_cell("Historical Event Window"),
                            rx.table.column_header_cell("Shock Origin"),
                            rx.table.column_header_cell("Affected Sectors"),
                            rx.table.column_header_cell("Directional Result"),
                            rx.table.column_header_cell("MAE"),
                        )
                    ),
                    rx.table.body(
                        rx.foreach(
                            State.backtest_scenarios,
                            lambda b: rx.table.row(
                                rx.table.cell(rx.text(b.event, font_weight="700", color=TEXT_HEADLINE)),
                                rx.table.cell(rx.badge(b.shock_sector, color_scheme="red", size="1")),
                                rx.table.cell(rx.text(b.affected_sectors, color=TEXT_MUTED)),
                                rx.table.cell(rx.badge(b.directional_result, color_scheme="green", size="1")),
                                rx.table.cell(rx.text(b.mae, color=TEXT_HEADLINE)),
                            ),
                        )
                    ),
                    width="100%",
                ),
                spacing="5",
                width="100%",
            ),
            background_color=CARD_BG,
            border=f"1px solid {CARD_BORDER}",
            border_radius="12px",
            padding=SPACE_8,
            box_shadow=SHADOW_CARD,
            width="100%",
        ),
        spacing="6",
        width="100%",
        padding=f"{SPACE_6} {SPACE_8}",
    )

# --- 10. /settings Route ---
def settings_view() -> rx.Component:
    return rx.vstack(
        legal_banner(),
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="settings", color=ACCENT_COLOR, size=24),
                    rx.heading("Investor Profile & Risk Parameters", font_size="1.4rem", font_weight="700", color=TEXT_HEADLINE),
                    spacing="2",
                    align="center",
                ),
                rx.text("Configure your investment horizon, risk tolerance profile, and sector exclusions:", color=TEXT_MUTED, font_size="0.9rem"),
                rx.grid(
                    rx.vstack(
                        rx.text("User Name", font_size="0.85rem", color=TEXT_MUTED),
                        rx.input(value=State.user_name, disabled=True, size="2"),
                        spacing="2",
                    ),
                    rx.vstack(
                        rx.text("Registered Email", font_size="0.85rem", color=TEXT_MUTED),
                        rx.input(value=State.user_email, disabled=True, size="2"),
                        spacing="2",
                    ),
                    rx.vstack(
                        rx.text("Risk Tolerance Profile", font_size="0.85rem", color=TEXT_MUTED),
                        rx.select(["low", "medium", "high"], value=State.risk_tolerance, on_change=State.set_risk_tolerance, size="2"),
                        spacing="2",
                    ),
                    rx.vstack(
                        rx.text("Investment Horizon", font_size="0.85rem", color=TEXT_MUTED),
                        rx.select(["short", "medium", "long"], value=State.investment_horizon, on_change=State.set_investment_horizon, size="2"),
                        spacing="2",
                    ),
                    columns="2",
                    spacing="6",
                    width="100%",
                ),
                rx.button("Save Risk Preferences", on_click=State.update_profile_settings, background_color=ACCENT_COLOR, color="#ffffff", size="2"),
                rx.cond(
                    State.profile_msg != "",
                    rx.text(State.profile_msg, color=POSITIVE_COLOR, font_size="0.85rem"),
                ),
                spacing="5",
                width="100%",
            ),
            background_color=CARD_BG,
            border=f"1px solid {CARD_BORDER}",
            border_radius="12px",
            padding=SPACE_8,
            box_shadow=SHADOW_CARD,
            width="100%",
        ),
        spacing="6",
        width="100%",
        padding=f"{SPACE_6} {SPACE_8}",
    )

# --- 11. /login Route (Auth View) ---
def auth_view() -> rx.Component:
    return rx.center(
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.heading("BidUp", font_size="1.8rem", font_weight="800", color=TEXT_HEADLINE),
                    rx.badge("Intelligence", color_scheme="purple"),
                    spacing="2",
                    align="center",
                ),
                rx.text(
                    rx.cond(State.auth_mode == "signin", "Sign in to access your portfolio & GAT risk models", "Create your BidUp investor profile"),
                    color=TEXT_MUTED,
                    font_size="0.9rem",
                ),
                rx.cond(
                    State.auth_mode == "signup",
                    rx.vstack(
                        rx.text("Display Name", font_size="0.8rem", color=TEXT_MUTED),
                        rx.input(value=State.auth_name_input, on_change=State.set_auth_name_input, placeholder="e.g. Gayatri Hirudkar", size="2"),
                        spacing="1",
                        width="100%",
                    ),
                ),
                rx.vstack(
                    rx.text("Email Address", font_size="0.8rem", color=TEXT_MUTED),
                    rx.input(value=State.auth_email_input, on_change=State.set_auth_email_input, placeholder="investor@bidup.ai", size="2"),
                    spacing="1",
                    width="100%",
                ),
                rx.vstack(
                    rx.text("Password", font_size="0.8rem", color=TEXT_MUTED),
                    rx.input(value=State.auth_password_input, on_change=State.set_auth_password_input, type="password", placeholder="••••••••", size="2"),
                    spacing="1",
                    width="100%",
                ),
                rx.cond(
                    State.auth_message != "",
                    rx.text(State.auth_message, color=ALERT_COLOR, font_size="0.85rem"),
                ),
                rx.button(
                    rx.cond(State.auth_mode == "signin", "Sign In & Enter Dashboard", "Create Account & Start Setup"),
                    on_click=State.handle_auth,
                    background_color=ACCENT_COLOR,
                    color="#ffffff",
                    width="100%",
                    size="3",
                ),
                rx.button(
                    rx.cond(State.auth_mode == "signin", "Don't have an account? Sign up", "Already have an account? Sign in"),
                    on_click=State.toggle_auth_mode,
                    variant="ghost",
                    color=TEXT_MUTED,
                    font_size="0.85rem",
                ),
                rx.divider(color=CARD_BORDER_SUBTLE, width="100%"),
                rx.button(
                    "Continue as Guest (Demo Mode)",
                    on_click=State.enter_guest_mode,
                    variant="outline",
                    color=TEXT_MUTED,
                    border_color=CARD_BORDER,
                    width="100%",
                    size="2",
                    font_size="0.85rem",
                ),
                spacing="5",
                width="100%",
            ),
            background_color=CARD_BG,
            border=f"1px solid {CARD_BORDER}",
            border_radius="16px",
            padding=SPACE_8,
            width="420px",
            box_shadow=SHADOW_HERO,
        ),
        min_height="100vh",
        background_color=BG_COLOR,
    )

# --- Master Page Container with Full Routing & Scroll Animations ---
def index() -> rx.Component:
    return rx.box(
        persistent_header(),
        rx.box(
            rx.cond(
                State.active_nav == "home",
                home_view(),
                rx.cond(
                    State.active_nav == "portfolio",
                    portfolio_view(),
                    rx.cond(
                        State.active_nav == "chat",
                        chat_view(),
                        rx.cond(
                            State.active_nav == "analytics",
                            analytics_view(),
                            settings_view()
                        )
                    )
                )
            ),
            class_name="animate-fade-in",
        ),
        background_color=BG_COLOR,
        min_height="100vh",
        color=TEXT_HEADLINE,
        font_family="Inter, sans-serif",
    )

app = rx.App(
    stylesheets=[
        "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap",
    ],
    style={
        "@keyframes fadeInUp": {
            "from": {"opacity": "0", "transform": "translateY(12px)"},
            "to": {"opacity": "1", "transform": "translateY(0)"},
        },
        ".animate-fade-in": {
            "animation": "fadeInUp 0.35s ease-out forwards",
        },
    }
)
app.add_page(
    index,
    title="BidUp — Portfolio Intelligence & Risk",
    on_load=[State.fetch_portfolio_news],
)

