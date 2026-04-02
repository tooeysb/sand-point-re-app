"""
Tests for API endpoints using httpx AsyncClient.

Covers health check, properties CRUD, calculation endpoints,
and auth API flow.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ── Health Check ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


# ── Properties CRUD ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_property(client):
    payload = {
        "name": "Test Property",
        "address_street": "123 Main St",
        "address_city": "Seattle",
        "address_state": "WA",
        "property_type": "retail",
        "net_rentable_sf": 10000,
        "purchase_price": 5000000,
    }
    response = await client.post("/api/properties/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Property"
    assert "id" in data


@pytest.mark.asyncio
async def test_list_properties(client):
    # Create one first
    await client.post(
        "/api/properties/",
        json={"name": "List Test", "property_type": "retail"},
    )
    response = await client.get("/api/properties/")
    assert response.status_code == 200
    data = response.json()
    assert "properties" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_property(client):
    create_resp = await client.post(
        "/api/properties/",
        json={"name": "Get Test"},
    )
    prop_id = create_resp.json()["id"]
    response = await client.get(f"/api/properties/{prop_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Get Test"


@pytest.mark.asyncio
async def test_get_property_not_found(client):
    response = await client.get("/api/properties/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_property(client):
    create_resp = await client.post(
        "/api/properties/",
        json={"name": "Update Test"},
    )
    prop_id = create_resp.json()["id"]
    response = await client.put(
        f"/api/properties/{prop_id}",
        json={"name": "Updated Name"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"


@pytest.mark.asyncio
async def test_delete_property(client):
    create_resp = await client.post(
        "/api/properties/",
        json={"name": "Delete Test"},
    )
    prop_id = create_resp.json()["id"]
    response = await client.delete(f"/api/properties/{prop_id}")
    assert response.status_code == 200
    assert response.json()["deleted"] is True

    # Verify it's gone (soft deleted)
    get_resp = await client.get(f"/api/properties/{prop_id}")
    assert get_resp.status_code == 404


# ── Calculation Endpoints ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_irr_endpoint(client):
    payload = {
        "cash_flows": [-1000.0, 300.0, 400.0, 500.0],
    }
    response = await client.post("/api/calculate/irr", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "irr" in data
    assert "multiple" in data
    assert "profit" in data
    assert data["irr"] > 0


@pytest.mark.asyncio
async def test_irr_endpoint_with_dates(client):
    payload = {
        "cash_flows": [-1000.0, 500.0, 700.0],
        "dates": ["2025-01-01", "2025-07-01", "2026-01-01"],
    }
    response = await client.post("/api/calculate/irr", json=payload)
    assert response.status_code == 200
    assert response.json()["irr"] > 0


@pytest.mark.asyncio
async def test_irr_endpoint_invalid(client):
    payload = {"cash_flows": [100.0, 200.0]}  # All positive
    response = await client.post("/api/calculate/irr", json=payload)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_amortization_endpoint(client):
    payload = {
        "principal": 500000.0,
        "annual_rate": 0.05,
        "amortization_years": 30,
        "io_months": 12,
        "total_months": 24,
    }
    response = await client.post("/api/calculate/amortization", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "schedule" in data
    assert len(data["schedule"]) == 24
    assert data["total_interest"] > 0


@pytest.mark.asyncio
async def test_cashflows_endpoint(client):
    payload = {
        "acquisition_date": "2025-01-01",
        "hold_period_months": 12,
        "purchase_price": 10000.0,
        "closing_costs": 200.0,
        "total_sf": 10000.0,
        "in_place_rent_psf": 50.0,
        "market_rent_psf": 55.0,
        "exit_cap_rate": 0.05,
        "sales_cost_percent": 0.01,
    }
    response = await client.post("/api/calculate/cashflows", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "metrics" in data
    assert "monthly_cashflows" in data
    assert "annual_cashflows" in data
    assert data["metrics"]["unleveraged_irr"] is not None


# ── Auth Endpoints ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_login_invalid_credentials(client):
    payload = {
        "email": "nobody@test.com",
        "password": "wrongpassword",
    }
    response = await client.post("/api/auth/login", json=payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_unauthenticated(client):
    response = await client.get("/api/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_no_token(client):
    response = await client.post("/api/auth/refresh", json={})
    assert response.status_code == 401
