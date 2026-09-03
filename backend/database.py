import os
import sqlite3
import json
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

SUPABASE_URL = (os.getenv("SUPABASE_URL") or "").strip()
SUPABASE_KEY = (os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY") or "").strip()
SUPABASE_SERVICE_KEY = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or "").strip()

supabase_client = None
supabase_admin_client = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        from supabase import create_client, Client
        supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Warning: Could not initialize live Supabase anon client: {e}")

if SUPABASE_URL and SUPABASE_SERVICE_KEY:
    try:
        from supabase import create_client, Client
        supabase_admin_client: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    except Exception as e:
        print(f"Warning: Could not initialize live Supabase admin client: {e}")

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bidup_local.db")

def is_using_live_supabase() -> bool:
    """Returns True if connected to a real Supabase cloud project."""
    return supabase_client is not None

def get_db_connection():
    """Returns local SQLite connection with Row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initializes local schema and seeds stock dataset if not exists."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Stocks Reference Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stocks (
        ticker TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        sector TEXT NOT NULL,
        industry TEXT NOT NULL,
        market_cap_category TEXT NOT NULL,
        esg_score REAL DEFAULT 70.0,
        risk_level TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 2. Users and User Profile (mirrors auth.users + public.user_profile)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_profile (
        id TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
        display_name TEXT NOT NULL,
        risk_tolerance TEXT NOT NULL,
        investment_horizon TEXT NOT NULL,
        sector_exclusions TEXT DEFAULT '[]',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 3. Portfolio Holdings
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS portfolio_holdings (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        ticker TEXT NOT NULL REFERENCES stocks(ticker),
        quantity REAL NOT NULL,
        avg_buy_price REAL NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, ticker)
    )
    """)
    
    # 4. Simulated Portfolios
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS simulated_portfolios (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        holdings_json TEXT NOT NULL DEFAULT '[]',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 5. Paper Trading Accounts & Ledger
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS paper_trading_accounts (
        user_id TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
        cash_balance REAL NOT NULL DEFAULT 1000000.0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS paper_trading_ledger (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        ticker TEXT NOT NULL,
        order_type TEXT NOT NULL,
        quantity REAL NOT NULL,
        requested_price REAL NOT NULL,
        slippage_pct REAL NOT NULL,
        executed_price REAL NOT NULL,
        total_amount REAL NOT NULL,
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # 6. Notifications
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_notifications (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        category TEXT NOT NULL,
        is_read INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Seed stocks dataset
    seed_stocks = [
        # IT
        ('TCS.NS', 'Tata Consultancy Services Ltd', 'IT', 'Software & IT Consulting', 'large_cap', 82.5, 'low'),
        ('INFY.NS', 'Infosys Ltd', 'IT', 'Software & IT Consulting', 'large_cap', 84.0, 'low'),
        ('HCLTECH.NS', 'HCL Technologies Ltd', 'IT', 'Software & IT Services', 'large_cap', 79.0, 'low'),
        ('WIPRO.NS', 'Wipro Ltd', 'IT', 'Software & IT Services', 'large_cap', 76.5, 'medium'),
        ('TECHM.NS', 'Tech Mahindra Ltd', 'IT', 'Telecom & IT Services', 'large_cap', 74.0, 'medium'),
        ('LTIM.NS', 'LTIMindtree Ltd', 'IT', 'IT Consulting', 'large_cap', 75.0, 'medium'),
        ('PERSISTENT.NS', 'Persistent Systems Ltd', 'IT', 'Digital Engineering', 'mid_cap', 73.0, 'medium'),
        ('COFORGE.NS', 'Coforge Ltd', 'IT', 'IT Solutions', 'mid_cap', 71.0, 'medium'),
        
        # Financial Services / Banking
        ('HDFCBANK.NS', 'HDFC Bank Ltd', 'Financial Services', 'Private Banking', 'large_cap', 81.0, 'low'),
        ('ICICIBANK.NS', 'ICICI Bank Ltd', 'Financial Services', 'Private Banking', 'large_cap', 80.5, 'low'),
        ('SBIN.NS', 'State Bank of India', 'Financial Services', 'Public Banking', 'large_cap', 72.0, 'medium'),
        ('KOTAKBANK.NS', 'Kotak Mahindra Bank Ltd', 'Financial Services', 'Private Banking', 'large_cap', 78.0, 'low'),
        ('AXISBANK.NS', 'Axis Bank Ltd', 'Financial Services', 'Private Banking', 'large_cap', 77.0, 'medium'),
        ('BAJFINANCE.NS', 'Bajaj Finance Ltd', 'Financial Services', 'Non-Banking Financial Co', 'large_cap', 75.5, 'medium'),
        ('BAJAJFINSV.NS', 'Bajaj Finserv Ltd', 'Financial Services', 'Financial Holding', 'large_cap', 74.0, 'medium'),
        ('INDUSINDBK.NS', 'IndusInd Bank Ltd', 'Financial Services', 'Private Banking', 'large_cap', 71.0, 'high'),
        
        # Energy & Oil/Gas
        ('RELIANCE.NS', 'Reliance Industries Ltd', 'Energy', 'Oil, Gas & Telecom Conglomerate', 'large_cap', 71.5, 'medium'),
        ('ONGC.NS', 'Oil and Natural Gas Corporation', 'Energy', 'Oil Exploration & Production', 'large_cap', 68.0, 'medium'),
        ('NTPC.NS', 'NTPC Ltd', 'Energy', 'Power Generation', 'large_cap', 70.0, 'low'),
        ('POWERGRID.NS', 'Power Grid Corporation of India', 'Energy', 'Power Transmission', 'large_cap', 76.0, 'low'),
        ('BPCL.NS', 'Bharat Petroleum Corporation', 'Energy', 'Refining & Marketing', 'large_cap', 67.5, 'medium'),
        ('IOC.NS', 'Indian Oil Corporation', 'Energy', 'Refining & Marketing', 'large_cap', 66.0, 'medium'),
        ('ADANIGREEN.NS', 'Adani Green Energy Ltd', 'Energy', 'Renewable Energy', 'large_cap', 69.0, 'high'),
        ('TATAPOWER.NS', 'Tata Power Company Ltd', 'Energy', 'Integrated Power', 'mid_cap', 73.0, 'medium'),
        
        # Automobile
        ('TATAMOTORS.NS', 'Tata Motors Ltd', 'Automobile', 'Commercial & Passenger Vehicles', 'large_cap', 78.0, 'medium'),
        ('MARUTI.NS', 'Maruti Suzuki India Ltd', 'Automobile', 'Passenger Cars', 'large_cap', 75.0, 'low'),
        ('M&M.NS', 'Mahindra & Mahindra Ltd', 'Automobile', 'Commercial & Farm Vehicles', 'large_cap', 79.5, 'low'),
        ('BAJAJ-AUTO.NS', 'Bajaj Auto Ltd', 'Automobile', '2 & 3 Wheelers', 'large_cap', 77.0, 'low'),
        ('EICHERMOT.NS', 'Eicher Motors Ltd', 'Automobile', 'Motorcycles & Commercial', 'large_cap', 76.0, 'medium'),
        ('HEROMOTOCO.NS', 'Hero MotoCorp Ltd', 'Automobile', '2 Wheelers', 'large_cap', 74.5, 'low'),
        
        # Pharmaceuticals & Healthcare
        ('SUNPHARMA.NS', 'Sun Pharmaceutical Industries', 'Pharma', 'Generics & Specialty Pharma', 'large_cap', 77.5, 'low'),
        ('DRREDDY.NS', 'Dr. Reddys Laboratories Ltd', 'Pharma', 'Generics & Active Ingredients', 'large_cap', 80.0, 'low'),
        ('CIPLA.NS', 'Cipla Ltd', 'Pharma', 'Formulations & Generics', 'large_cap', 83.0, 'low'),
        ('DIVISLAB.NS', 'Divis Laboratories Ltd', 'Pharma', 'Active Pharmaceutical Ingredients', 'large_cap', 81.0, 'medium'),
        ('APOLLOHOSP.NS', 'Apollo Hospitals Enterprise', 'Pharma', 'Hospital Chains & Healthcare', 'large_cap', 79.0, 'medium'),
        ('LUPIN.NS', 'Lupin Ltd', 'Pharma', 'Formulations & Generics', 'mid_cap', 74.0, 'medium'),
        
        # FMCG
        ('HINDUNILVR.NS', 'Hindustan Unilever Ltd', 'FMCG', 'Household & Personal Care', 'large_cap', 86.0, 'low'),
        ('ITC.NS', 'ITC Ltd', 'FMCG', 'Tobacco, FMCG, Hotels, Paper', 'large_cap', 78.0, 'low'),
        ('NESTLEIND.NS', 'Nestle India Ltd', 'FMCG', 'Food Products & Beverages', 'large_cap', 82.0, 'low'),
        ('BRITANNIA.NS', 'Britannia Industries Ltd', 'FMCG', 'Bakery & Dairy Products', 'large_cap', 80.0, 'low'),
        ('TATACONSUM.NS', 'Tata Consumer Products Ltd', 'FMCG', 'Beverages & Foods', 'large_cap', 81.5, 'low'),
        ('DABUR.NS', 'Dabur India Ltd', 'FMCG', 'Ayurvedic & Personal Care', 'large_cap', 79.0, 'low'),
        
        # Metals & Mining
        ('TATASTEEL.NS', 'Tata Steel Ltd', 'Metals', 'Steel Manufacturing', 'large_cap', 73.0, 'high'),
        ('JSWSTEEL.NS', 'JSW Steel Ltd', 'Metals', 'Steel Manufacturing', 'large_cap', 71.5, 'high'),
        ('HINDALCO.NS', 'Hindalco Industries Ltd', 'Metals', 'Aluminum & Copper', 'large_cap', 75.0, 'high'),
        ('COALINDIA.NS', 'Coal India Ltd', 'Metals', 'Coal Mining', 'large_cap', 64.0, 'medium'),
        ('VEDL.NS', 'Vedanta Ltd', 'Metals', 'Diversified Metals & Mining', 'large_cap', 62.0, 'high'),
        
        # Realty & Infrastructure
        ('DLF.NS', 'DLF Ltd', 'Realty', 'Real Estate Development', 'large_cap', 68.0, 'high'),
        ('GODREJPROP.NS', 'Godrej Properties Ltd', 'Realty', 'Residential & Commercial Real Estate', 'mid_cap', 72.0, 'high'),
        ('LT.NS', 'Larsen & Toubro Ltd', 'Infra', 'Engineering & Construction', 'large_cap', 82.0, 'low'),
        ('ADANIPORTS.NS', 'Adani Ports and SEZ Ltd', 'Infra', 'Ports & Logistics', 'large_cap', 70.0, 'medium'),
        ('ULTRACEMCO.NS', 'UltraTech Cement Ltd', 'Infra', 'Cement & Building Materials', 'large_cap', 78.5, 'medium')
    ]
    
    cursor.executemany("""
    INSERT OR IGNORE INTO stocks (ticker, name, sector, industry, market_cap_category, esg_score, risk_level)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, seed_stocks)
    
    conn.commit()
    conn.close()

# Initialize upon import
init_database()

def db_signup_user(email: str, password_hash: str, display_name: str, risk_tolerance: str = "medium", investment_horizon: str = "long", sector_exclusions: list = None) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE email = ?", (email.lower(),))
    if cursor.fetchone():
        conn.close()
        return None
    
    user_id = str(uuid.uuid4())
    cursor.execute("INSERT INTO users (id, email, hashed_password) VALUES (?, ?, ?)", (user_id, email.lower(), password_hash))
    exclusions_json = json.dumps(sector_exclusions or ["Tobacco"])
    cursor.execute("""
        INSERT INTO user_profile (id, display_name, risk_tolerance, investment_horizon, sector_exclusions)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, display_name, risk_tolerance, investment_horizon, exclusions_json))
    cursor.execute("INSERT INTO paper_trading_accounts (user_id, cash_balance) VALUES (?, 1000000.0)", (user_id,))
    conn.commit()
    conn.close()
    return {
        "id": user_id,
        "email": email.lower(),
        "display_name": display_name,
        "risk_tolerance": risk_tolerance,
        "investment_horizon": investment_horizon,
        "sector_exclusions": sector_exclusions or ["Tobacco"]
    }

def db_login_user(email: str, password_hash: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.email, u.hashed_password, p.display_name, p.risk_tolerance, p.investment_horizon, p.sector_exclusions
        FROM users u
        LEFT JOIN user_profile p ON u.id = p.id
        WHERE u.email = ?
    """, (email.lower(),))
    row = cursor.fetchone()
    conn.close()
    if not row or row["hashed_password"] != password_hash:
        return None
    
    exclusions = []
    try:
        exclusions = json.loads(row["sector_exclusions"]) if row["sector_exclusions"] else []
    except Exception:
        pass
        
    return {
        "id": row["id"],
        "email": row["email"],
        "display_name": row["display_name"] or row["email"].split("@")[0],
        "risk_tolerance": row["risk_tolerance"] or "medium",
        "investment_horizon": row["investment_horizon"] or "long",
        "sector_exclusions": exclusions
    }

def db_get_holdings(user_id: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT h.id, h.ticker, h.quantity, h.avg_buy_price, s.name, s.sector, s.risk_level
        FROM portfolio_holdings h
        LEFT JOIN stocks s ON h.ticker = s.ticker
        WHERE h.user_id = ?
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    res = []
    for r in rows:
        res.append({
            "id": r["id"],
            "ticker": r["ticker"],
            "quantity": float(r["quantity"]),
            "avg_buy_price": float(r["avg_buy_price"]),
            "name": r["name"] or r["ticker"],
            "sector": r["sector"] or "Other",
            "risk": r["risk_level"] or "medium"
        })
    return res

def db_save_holding(user_id: str, ticker: str, quantity: float, avg_buy_price: float) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    holding_id = str(uuid.uuid4())[:8]
    cursor.execute("""
        INSERT INTO portfolio_holdings (id, user_id, ticker, quantity, avg_buy_price)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id, ticker) DO UPDATE SET
            quantity = excluded.quantity,
            avg_buy_price = excluded.avg_buy_price,
            updated_at = CURRENT_TIMESTAMP
    """, (holding_id, user_id, ticker, quantity, avg_buy_price))
    conn.commit()
    conn.close()
    return True

def db_delete_holding(user_id: str, ticker: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM portfolio_holdings WHERE user_id = ? AND ticker = ?", (user_id, ticker))
    conn.commit()
    conn.close()
    return True

def db_update_profile(user_id: str, risk_tolerance: str, investment_horizon: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE user_profile
        SET risk_tolerance = ?, investment_horizon = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (risk_tolerance, investment_horizon, user_id))
    conn.commit()
    conn.close()
    return True
