import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_cross_user_rls_isolation():
    """
    Rigorously verifies multi-tenant isolation:
    User A cannot read, update, or delete User B's portfolio holdings or profile.
    """
    
    # 1. Register User A (Alice)
    alice_signup = {
        "email": "alice_isolation@bidup.ai",
        "password": "PasswordAlice123!",
        "display_name": "Alice Investor",
        "risk_tolerance": "low",
        "investment_horizon": "long",
        "sector_exclusions": ["Tobacco"]
    }
    res_a = client.post("/api/auth/signup", json=alice_signup)
    if res_a.status_code == 400: # Already exists
        res_a = client.post("/api/auth/login", json={"email": alice_signup["email"], "password": alice_signup["password"]})
    assert res_a.status_code == 200
    token_a = res_a.json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # 2. Register User B (Bob)
    bob_signup = {
        "email": "bob_isolation@bidup.ai",
        "password": "PasswordBob123!",
        "display_name": "Bob Trader",
        "risk_tolerance": "high",
        "investment_horizon": "short",
        "sector_exclusions": ["Fossil Fuels"]
    }
    res_b = client.post("/api/auth/signup", json=bob_signup)
    if res_b.status_code == 400: # Already exists
        res_b = client.post("/api/auth/login", json={"email": bob_signup["email"], "password": bob_signup["password"]})
    assert res_b.status_code == 200
    token_b = res_b.json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # 3. Add holdings for Alice: TCS.NS (10 units), INFY.NS (20 units)
    add_a1 = client.post("/api/portfolio/manual", json={"ticker": "TCS.NS", "quantity": 10, "avg_buy_price": 3900.0}, headers=headers_a)
    add_a2 = client.post("/api/portfolio/manual", json={"ticker": "INFY.NS", "quantity": 20, "avg_buy_price": 1700.0}, headers=headers_a)
    assert add_a1.status_code == 200
    assert add_a2.status_code == 200

    # 4. Add holdings for Bob: RELIANCE.NS (15 units)
    add_b = client.post("/api/portfolio/manual", json={"ticker": "RELIANCE.NS", "quantity": 15, "avg_buy_price": 2800.0}, headers=headers_b)
    assert add_b.status_code == 200

    # 5. Isolation Assertion 1: Alice queries her holdings
    alice_holdings = client.get("/api/portfolio/holdings", headers=headers_a).json()
    alice_tickers = [h["ticker"] for h in alice_holdings]
    assert "TCS.NS" in alice_tickers
    assert "INFY.NS" in alice_tickers
    assert "RELIANCE.NS" not in alice_tickers, "CRITICAL: Alice was able to see Bob's holding RELIANCE.NS!"

    # 6. Isolation Assertion 2: Bob queries his holdings
    bob_holdings = client.get("/api/portfolio/holdings", headers=headers_b).json()
    bob_tickers = [h["ticker"] for h in bob_holdings]
    assert "RELIANCE.NS" in bob_tickers
    assert "TCS.NS" not in bob_tickers, "CRITICAL: Bob was able to see Alice's holding TCS.NS!"
    assert "INFY.NS" not in bob_tickers, "CRITICAL: Bob was able to see Alice's holding INFY.NS!"

    # 7. Isolation Assertion 3: Alice attempts to delete Bob's holding (RELIANCE.NS)
    del_attempt = client.delete("/api/portfolio/holding/RELIANCE.NS", headers=headers_a)
    # Alice should receive 404 because RELIANCE.NS does not exist in Alice's user scope
    assert del_attempt.status_code == 404, f"Expected 404 when Alice tries deleting Bob's holding, got {del_attempt.status_code}"

    # 8. Verify Bob's holding is untouched
    bob_holdings_after = client.get("/api/portfolio/holdings", headers=headers_b).json()
    bob_tickers_after = [h["ticker"] for h in bob_holdings_after]
    assert "RELIANCE.NS" in bob_tickers_after, "Bob's holding was deleted by Alice!"
    assert any(h["quantity"] == 15 for h in bob_holdings_after if h["ticker"] == "RELIANCE.NS")

    # 9. Isolation Assertion 4: Profile isolation
    alice_profile = client.get("/api/auth/me", headers=headers_a).json()
    bob_profile = client.get("/api/auth/me", headers=headers_b).json()
    assert alice_profile["email"] == "alice_isolation@bidup.ai"
    assert alice_profile["risk_tolerance"] == "low"
    assert bob_profile["email"] == "bob_isolation@bidup.ai"
    assert bob_profile["risk_tolerance"] == "high"

    # 10. Isolation Assertion 5: Update isolation
    update_res = client.put("/api/auth/profile", json={"display_name": "Alice Updated"}, headers=headers_a)
    assert update_res.status_code == 200
    
    # Assert Bob's profile remains untouched
    bob_profile_check = client.get("/api/auth/me", headers=headers_b).json()
    assert bob_profile_check["display_name"] == "Bob Trader"

if __name__ == "__main__":
    pytest.main(["-v", __file__])
