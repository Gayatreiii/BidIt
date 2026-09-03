-- ==============================================================================
-- BidUp Database Schema & Migrations
-- Target: Supabase (PostgreSQL with built-in Auth and Row-Level Security)
-- ==============================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 0. SCHEMA PERMISSIONS FOR SUPABASE ROLES
GRANT USAGE ON SCHEMA public TO postgres, anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA public TO postgres, anon, authenticated, service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO postgres, anon, authenticated, service_role;
GRANT ALL ON ALL ROUTINES IN SCHEMA public TO postgres, anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO postgres, anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO postgres, anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON ROUTINES TO postgres, anon, authenticated, service_role;

-- 1. STOCKS REFERENCE TABLE (Maintained Indian Market Equities)
CREATE TABLE IF NOT EXISTS public.stocks (
    ticker TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    sector TEXT NOT NULL,
    industry TEXT NOT NULL,
    market_cap_category TEXT NOT NULL CHECK (market_cap_category IN ('large_cap', 'mid_cap', 'small_cap')),
    esg_score NUMERIC DEFAULT 70.0,
    risk_level TEXT NOT NULL CHECK (risk_level IN ('low', 'medium', 'high')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Public read access for stock reference data
ALTER TABLE public.stocks ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Allow public read-only access on stocks" ON public.stocks;
CREATE POLICY "Allow public read-only access on stocks"
    ON public.stocks FOR SELECT
    USING (true);

-- 2. USER PROFILE TABLE (Linked to Supabase auth.users)
CREATE TABLE IF NOT EXISTS public.user_profile (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    display_name TEXT NOT NULL,
    risk_tolerance TEXT NOT NULL CHECK (risk_tolerance IN ('low', 'medium', 'high')),
    investment_horizon TEXT NOT NULL CHECK (investment_horizon IN ('short', 'medium', 'long')),
    sector_exclusions TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.user_profile ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can view their own profile" ON public.user_profile;
CREATE POLICY "Users can view their own profile"
    ON public.user_profile FOR SELECT
    USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can insert their own profile" ON public.user_profile;
CREATE POLICY "Users can insert their own profile"
    ON public.user_profile FOR INSERT
    WITH CHECK (auth.uid() = id);

DROP POLICY IF EXISTS "Users can update their own profile" ON public.user_profile;
CREATE POLICY "Users can update their own profile"
    ON public.user_profile FOR UPDATE
    USING (auth.uid() = id);

-- 3. PORTFOLIO HOLDINGS TABLE (Scoped to user via RLS)
CREATE TABLE IF NOT EXISTS public.portfolio_holdings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    ticker TEXT NOT NULL REFERENCES public.stocks(ticker) ON UPDATE CASCADE,
    quantity NUMERIC NOT NULL CHECK (quantity > 0),
    avg_buy_price NUMERIC NOT NULL CHECK (avg_buy_price >= 0),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (user_id, ticker)
);

ALTER TABLE public.portfolio_holdings ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can view their own portfolio holdings" ON public.portfolio_holdings;
CREATE POLICY "Users can view their own portfolio holdings"
    ON public.portfolio_holdings FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert their own portfolio holdings" ON public.portfolio_holdings;
CREATE POLICY "Users can insert their own portfolio holdings"
    ON public.portfolio_holdings FOR INSERT
    WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update their own portfolio holdings" ON public.portfolio_holdings;
CREATE POLICY "Users can update their own portfolio holdings"
    ON public.portfolio_holdings FOR UPDATE
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete their own portfolio holdings" ON public.portfolio_holdings;
CREATE POLICY "Users can delete their own portfolio holdings"
    ON public.portfolio_holdings FOR DELETE
    USING (auth.uid() = user_id);

-- 4. SIMULATED PORTFOLIOS TABLE (For "What-If" and Multi-Portfolio Comparison)
CREATE TABLE IF NOT EXISTS public.simulated_portfolios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    holdings_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.simulated_portfolios ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can manage their simulated portfolios" ON public.simulated_portfolios;
CREATE POLICY "Users can manage their simulated portfolios"
    ON public.simulated_portfolios FOR ALL
    USING (auth.uid() = user_id);

-- 5. PAPER TRADING ACCOUNTS & LEDGER
CREATE TABLE IF NOT EXISTS public.paper_trading_accounts (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    cash_balance NUMERIC NOT NULL DEFAULT 1000000.0 CHECK (cash_balance >= 0),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.paper_trading_accounts ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can access their paper trading account" ON public.paper_trading_accounts;
CREATE POLICY "Users can access their paper trading account"
    ON public.paper_trading_accounts FOR ALL
    USING (auth.uid() = user_id);

CREATE TABLE IF NOT EXISTS public.paper_trading_ledger (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    ticker TEXT NOT NULL REFERENCES public.stocks(ticker),
    order_type TEXT NOT NULL CHECK (order_type IN ('BUY', 'SELL')),
    quantity NUMERIC NOT NULL CHECK (quantity > 0),
    requested_price NUMERIC NOT NULL,
    slippage_pct NUMERIC NOT NULL,
    executed_price NUMERIC NOT NULL,
    total_amount NUMERIC NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.paper_trading_ledger ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users can view their paper trading ledger" ON public.paper_trading_ledger;
CREATE POLICY "Users can view their paper trading ledger"
    ON public.paper_trading_ledger FOR ALL
    USING (auth.uid() = user_id);

-- 6. SAVED SCREENERS & NOTIFICATIONS
CREATE TABLE IF NOT EXISTS public.user_saved_screeners (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    filter_json JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.user_saved_screeners ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users manage their saved screeners" ON public.user_saved_screeners;
CREATE POLICY "Users manage their saved screeners"
    ON public.user_saved_screeners FOR ALL
    USING (auth.uid() = user_id);

CREATE TABLE IF NOT EXISTS public.user_notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('risk', 'sentiment', 'price', 'general')),
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.user_notifications ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users manage their notifications" ON public.user_notifications;
CREATE POLICY "Users manage their notifications"
    ON public.user_notifications FOR ALL
    USING (auth.uid() = user_id);

-- ==============================================================================
-- SEED DATA: 50+ Major Indian Market Stocks Across Key Sectors
-- ==============================================================================
INSERT INTO public.stocks (ticker, name, sector, industry, market_cap_category, esg_score, risk_level)
VALUES
-- IT Sector
('TCS.NS', 'Tata Consultancy Services Ltd', 'IT', 'Software & IT Consulting', 'large_cap', 82.5, 'low'),
('INFY.NS', 'Infosys Ltd', 'IT', 'Software & IT Consulting', 'large_cap', 84.0, 'low'),
('HCLTECH.NS', 'HCL Technologies Ltd', 'IT', 'Software & IT Services', 'large_cap', 79.0, 'low'),
('WIPRO.NS', 'Wipro Ltd', 'IT', 'Software & IT Services', 'large_cap', 76.5, 'medium'),
('TECHM.NS', 'Tech Mahindra Ltd', 'IT', 'Telecom & IT Services', 'large_cap', 74.0, 'medium'),
('LTIM.NS', 'LTIMindtree Ltd', 'IT', 'IT Consulting', 'large_cap', 75.0, 'medium'),
('PERSISTENT.NS', 'Persistent Systems Ltd', 'IT', 'Digital Engineering', 'mid_cap', 73.0, 'medium'),
('COFORGE.NS', 'Coforge Ltd', 'IT', 'IT Solutions', 'mid_cap', 71.0, 'medium'),

-- Financial Services / Banking
('HDFCBANK.NS', 'HDFC Bank Ltd', 'Financial Services', 'Private Banking', 'large_cap', 81.0, 'low'),
('ICICIBANK.NS', 'ICICI Bank Ltd', 'Financial Services', 'Private Banking', 'large_cap', 80.5, 'low'),
('SBIN.NS', 'State Bank of India', 'Financial Services', 'Public Banking', 'large_cap', 72.0, 'medium'),
('KOTAKBANK.NS', 'Kotak Mahindra Bank Ltd', 'Financial Services', 'Private Banking', 'large_cap', 78.0, 'low'),
('AXISBANK.NS', 'Axis Bank Ltd', 'Financial Services', 'Private Banking', 'large_cap', 77.0, 'medium'),
('BAJFINANCE.NS', 'Bajaj Finance Ltd', 'Financial Services', 'Non-Banking Financial Co', 'large_cap', 75.5, 'medium'),
('BAJAJFINSV.NS', 'Bajaj Finserv Ltd', 'Financial Services', 'Financial Holding', 'large_cap', 74.0, 'medium'),
('INDUSINDBK.NS', 'IndusInd Bank Ltd', 'Financial Services', 'Private Banking', 'large_cap', 71.0, 'high'),

-- Energy & Oil/Gas
('RELIANCE.NS', 'Reliance Industries Ltd', 'Energy', 'Oil, Gas & Petrochemicals / Retail / Telecom', 'large_cap', 71.5, 'medium'),
('ONGC.NS', 'Oil and Natural Gas Corporation', 'Energy', 'Oil Exploration & Production', 'large_cap', 68.0, 'medium'),
('NTPC.NS', 'NTPC Ltd', 'Energy', 'Power Generation', 'large_cap', 70.0, 'low'),
('POWERGRID.NS', 'Power Grid Corporation of India', 'Energy', 'Power Transmission', 'large_cap', 76.0, 'low'),
('BPCL.NS', 'Bharat Petroleum Corporation', 'Energy', 'Refining & Marketing', 'large_cap', 67.5, 'medium'),
('IOC.NS', 'Indian Oil Corporation', 'Energy', 'Refining & Marketing', 'large_cap', 66.0, 'medium'),
('ADANIGREEN.NS', 'Adani Green Energy Ltd', 'Energy', 'Renewable Energy', 'large_cap', 69.0, 'high'),
('TATAPOWER.NS', 'Tata Power Company Ltd', 'Energy', 'Integrated Power', 'mid_cap', 73.0, 'medium'),

-- Automobile
('TATAMOTORS.NS', 'Tata Motors Ltd', 'Automobile', 'Commercial & Passenger Vehicles', 'large_cap', 78.0, 'medium'),
('MARUTI.NS', 'Maruti Suzuki India Ltd', 'Automobile', 'Passenger Cars', 'large_cap', 75.0, 'low'),
('M&M.NS', 'Mahindra & Mahindra Ltd', 'Automobile', 'Commercial & Farm Vehicles', 'large_cap', 79.5, 'low'),
('BAJAJ-AUTO.NS', 'Bajaj Auto Ltd', 'Automobile', '2 & 3 Wheelers', 'large_cap', 77.0, 'low'),
('EICHERMOT.NS', 'Eicher Motors Ltd', 'Automobile', 'Motorcycles & Commercial', 'large_cap', 76.0, 'medium'),
('HEROMOTOCO.NS', 'Hero MotoCorp Ltd', 'Automobile', '2 Wheelers', 'large_cap', 74.5, 'low'),

-- Pharmaceuticals & Healthcare
('SUNPHARMA.NS', 'Sun Pharmaceutical Industries', 'Pharma', 'Generics & Specialty Pharma', 'large_cap', 77.5, 'low'),
('DRREDDY.NS', 'Dr. Reddys Laboratories Ltd', 'Pharma', 'Generics & Active Ingredients', 'large_cap', 80.0, 'low'),
('CIPLA.NS', 'Cipla Ltd', 'Pharma', 'Formulations & Generics', 'large_cap', 83.0, 'low'),
('DIVISLAB.NS', 'Divis Laboratories Ltd', 'Pharma', 'Active Pharmaceutical Ingredients', 'large_cap', 81.0, 'medium'),
('APOLLOHOSP.NS', 'Apollo Hospitals Enterprise', 'Pharma', 'Hospital Chains & Healthcare', 'large_cap', 79.0, 'medium'),
('LUPIN.NS', 'Lupin Ltd', 'Pharma', 'Formulations & Generics', 'mid_cap', 74.0, 'medium'),

-- FMCG (Fast Moving Consumer Goods)
('HINDUNILVR.NS', 'Hindustan Unilever Ltd', 'FMCG', 'Household & Personal Care', 'large_cap', 86.0, 'low'),
('ITC.NS', 'ITC Ltd', 'FMCG', 'Tobacco, FMCG, Hotels, Paper', 'large_cap', 78.0, 'low'),
('NESTLEIND.NS', 'Nestle India Ltd', 'FMCG', 'Food Products & Beverages', 'large_cap', 82.0, 'low'),
('BRITANNIA.NS', 'Britannia Industries Ltd', 'FMCG', 'Bakery & Dairy Products', 'large_cap', 80.0, 'low'),
('TATACONSUM.NS', 'Tata Consumer Products Ltd', 'FMCG', 'Beverages & Foods', 'large_cap', 81.5, 'low'),
('DABUR.NS', 'Dabur India Ltd', 'FMCG', 'Ayurvedic & Personal Care', 'large_cap', 79.0, 'low'),

-- Metals & Mining
('TATASTEEL.NS', 'Tata Steel Ltd', 'Metals', 'Steel Manufacturing', 'large_cap', 73.0, 'high'),
('JSWSTEEL.NS', 'JSW Steel Ltd', 'Metals', 'Steel Manufacturing', 'large_cap', 71.5, 'high'),
('HINDALCO.NS', 'Hindalco Industries Ltd', 'Metals', 'Aluminum & Copper', 'large_cap', 75.0, 'high'),
('COALINDIA.NS', 'Coal India Ltd', 'Metals', 'Coal Mining', 'large_cap', 64.0, 'medium'),
('VEDL.NS', 'Vedanta Ltd', 'Metals', 'Diversified Metals & Mining', 'large_cap', 62.0, 'high'),

-- Realty & Infrastructure
('DLF.NS', 'DLF Ltd', 'Realty', 'Real Estate Development', 'large_cap', 68.0, 'high'),
('GODREJPROP.NS', 'Godrej Properties Ltd', 'Realty', 'Residential & Commercial Real Estate', 'mid_cap', 72.0, 'high'),
('LT.NS', 'Larsen & Toubro Ltd', 'Infra', 'Engineering & Construction', 'large_cap', 82.0, 'low'),
('ADANIPORTS.NS', 'Adani Ports and SEZ Ltd', 'Infra', 'Ports & Logistics', 'large_cap', 70.0, 'medium'),
('ULTRACEMCO.NS', 'UltraTech Cement Ltd', 'Infra', 'Cement & Building Materials', 'large_cap', 78.5, 'medium')
ON CONFLICT (ticker) DO NOTHING;
