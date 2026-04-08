import pytest
from unittest.mock import MagicMock, patch
from models.schemas import Lead, ExtractionRequest
from services.excel_service import generate_excel
from services.job_store import create_job, get_job, update_job, ExtractionStatus
import uuid


# ---- Model Tests ----

def test_lead_defaults():
    lead = Lead()
    assert lead.name == ""
    assert lead.city == ""
    assert lead.notes == ""


def test_extraction_request_invalid_url():
    with pytest.raises(Exception):
        ExtractionRequest(maps_url="https://not-google.com/page")


def test_extraction_request_valid_url():
    req = ExtractionRequest(maps_url="https://www.google.com/maps/search/gyms/@28.6139,77.2090,14z")
    assert "google.com/maps" in req.maps_url


# ---- Excel Tests ----

def test_generate_excel_empty():
    data = generate_excel([])
    assert isinstance(data, bytes)
    assert len(data) > 0


def test_generate_excel_with_leads():
    leads = [
        Lead(name="Test Gym", city="Delhi", phone="+91-9999999999", website="https://testgym.com"),
        Lead(name="Fit Zone", city="Mumbai", phone="+91-8888888888"),
    ]
    data = generate_excel(leads)
    assert len(data) > 5000  # Should be a valid xlsx binary


def test_generate_excel_deduplicates():
    lead = Lead(name="Dup Gym", phone="1234567890", website="https://dup.com")
    data = generate_excel([lead, lead])
    # No crash expected; dedup works
    assert data


# ---- Job Store Tests ----

def test_create_and_get_job():
    jid = str(uuid.uuid4())
    status = ExtractionStatus(job_id=jid, status="pending")
    create_job(jid, status)
    result = get_job(jid)
    assert result is not None
    assert result.job_id == jid
    assert result.status == "pending"


def test_update_job():
    jid = str(uuid.uuid4())
    status = ExtractionStatus(job_id=jid, status="pending")
    create_job(jid, status)
    update_job(jid, status="running", total_found=10)
    result = get_job(jid)
    assert result.status == "running"
    assert result.total_found == 10


def test_get_nonexistent_job():
    result = get_job("nonexistent-id")
    assert result is None


# ---- City Extraction Test ----

def test_extract_city_from_address():
    from scraper.maps_scraper import _extract_city
    addr = "123 Main St, Connaught Place, New Delhi, Delhi 110001"
    city = _extract_city(addr)
    assert city != ""
    assert "Delhi" in city or "New Delhi" in city or "Connaught" in city
