import pytest
import io
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "healthy"}

def test_module_1_signup_and_profile():
    signup_payload = {
        "email": "test_investor@bidup.ai",
        "password": "strongPassword123",
        "display_name": "Test Investor",
        "risk_tolerance": "high",
        "investment_horizon": "long",
        "sector_exclusions": ["Tobacco", "Fossil Fuels"]
    }
    # Test signup
    res = client.post("/api/auth/signup", json=signup_payload)
    if res.status_code == 400 and "already exists" in res.text:
        # If already signed up from earlier run, test login
        login_res = client.post("/api/auth/login", json={
            "email": "test_investor@bidup.ai",
            "password": "strongPassword123"
        })
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
    else:
        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert data["user"]["display_name"] == "Test Investor"
        assert data["user"]["risk_tolerance"] == "high"
        assert data["user"]["investment_horizon"] == "long"
        assert "Tobacco" in data["user"]["sector_exclusions"]
        token = data["access_token"]

    headers = {"Authorization": f"Bearer {token}"}

    # Test /api/auth/me
    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == "test_investor@bidup.ai"
    assert me_data["risk_tolerance"] == "high"

def test_module_2_stock_catalog():
    res = client.get("/api/portfolio/stocks")
    assert res.status_code == 200
    stocks = res.json()
    assert len(stocks) >= 30
    tickers = [s["ticker"] for s in stocks]
    assert "TCS.NS" in tickers
    assert "RELIANCE.NS" in tickers
    assert "HDFCBANK.NS" in tickers

def test_module_2_manual_holding_and_csv():
    # Login first
    login_res = client.post("/api/auth/login", json={
        "email": "test_investor@bidup.ai",
        "password": "strongPassword123"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Add manual holding
    add_res = client.post("/api/portfolio/manual", json={
        "ticker": "INFY.NS",
        "quantity": 20,
        "avg_buy_price": 1750.0
    }, headers=headers)
    assert add_res.status_code == 200
    add_data = add_res.json()
    assert add_data["ticker"] == "INFY.NS"
    assert add_data["quantity"] == 20
    assert add_data["invested_value"] == 35000.0
    assert add_data["current_value"] > 0

    # Get holdings
    holdings_res = client.get("/api/portfolio/holdings", headers=headers)
    assert holdings_res.status_code == 200
    holdings = holdings_res.json()
    assert any(h["ticker"] == "INFY.NS" for h in holdings)

    # Test CSV Import
    csv_content = b"ticker,quantity,avg_buy_price\nTCS.NS,15,3850.00\nRELIANCE.NS,25,2740.50\n"
    csv_file = io.BytesIO(csv_content)
    upload_res = client.post(
        "/api/portfolio/import-csv",
        files={"file": ("portfolio.csv", csv_file, "text/csv")},
        headers=headers
    )
    assert upload_res.status_code == 200
    upload_data = upload_res.json()
    assert upload_data["success"] is True
    assert upload_data["imported_count"] == 2

    # Check broker status
    broker_res = client.get("/api/portfolio/broker-sync-status")
    assert broker_res.status_code == 200
    assert broker_res.json()["status"] == "coming_soon"

if __name__ == "__main__":
    pytest.main(["-v", __file__])
