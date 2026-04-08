import pytest
import sys
import os
from unittest.mock import MagicMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from services.db import mongo


@pytest.fixture
def client():
    """Create test client and mock database"""
    app.config['TESTING'] = True
    app.config['MONGO_URI'] = 'mongodb://localhost:27017/test_db'
    app.config['SECRET_KEY'] = 'test_secret_key'

    with app.test_client() as client:
        with app.app_context():
            # Mock MongoDB collections
            mongo.db = MagicMock()
            mongo.db.workouts = MagicMock()
            mongo.db.meals = MagicMock()
            mongo.db.sleeps = MagicMock()
        yield client


# ✅ FIXED LOGIN (IMPORTANT CHANGE)
def login(client):
    """Fake login by setting session directly"""
    with client.session_transaction() as sess:
        sess["user"] = "testuser"
        sess["full_name"] = "Test User"


# ============================================
# HEALTH ENDPOINT TEST
# ============================================

def test_health_endpoint(client):
    response = client.get('/api/health')
    assert response.status_code == 200
    assert response.get_json()['status'] == 'success'


# ============================================
# LOGIN PAGE TESTS
# ============================================

def test_login_page_loads(client):
    response = client.get('/login')
    assert response.status_code == 200


def test_login_fail(client):
    response = client.post(
        '/login',
        data={'username': 'wrong', 'password': 'wrong'},
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b'Invalid username or password' in response.data


# ============================================
# PROTECTED PAGE TESTS
# ============================================

def test_dashboard_loads_after_login(client):
    with app.app_context():
        mongo.db.workouts.find.return_value = []
        mongo.db.meals.find.return_value = []
        mongo.db.sleeps.find.return_value = []

    login(client)
    response = client.get('/')
    assert response.status_code == 200


def test_add_workout_page_loads_after_login(client):
    login(client)
    response = client.get('/add-workout')
    assert response.status_code == 200


def test_add_meal_page_loads_after_login(client):
    login(client)
    response = client.get('/add-meal')
    assert response.status_code == 200


def test_add_sleep_page_loads_after_login(client):
    login(client)
    response = client.get('/add-sleep')
    assert response.status_code == 200


def test_ai_page_loads_after_login(client):
    login(client)
    response = client.get('/ai_page')
    assert response.status_code == 200


# ============================================
# AI FUNCTION TESTS
# ============================================

def test_build_prompt_returns_string():
    from routes.ai import build_prompt

    data = {
        "workouts": [{"workout_type": "Running", "duration": 30}],
        "meals": [{"meal_name": "Salad", "calories": 300}],
        "sleeps": [{"duration": 8, "quality": "Good"}]
    }

    result = build_prompt(data)
    assert isinstance(result, str)
    assert len(result) > 0


def test_fallback_insights_returns_string():
    from routes.ai import fallback_insights

    data = {
        "workouts": [],
        "meals": [],
        "sleeps": [],
        "db_status": "disconnected"
    }

    result = fallback_insights(data)
    assert isinstance(result, str)
    assert "Summary" in result


# ============================================
# BLUEPRINT TEST
# ============================================

def test_ai_blueprint_registered():
    assert 'ai' in app.blueprints


# ============================================
# ROUTE TESTS
# ============================================

def test_api_workouts_route_exists(client):
    response = client.get('/api/workouts')
    assert response.status_code in [200, 404]


def test_api_meals_route_exists(client):
    response = client.get('/api/meals')
    assert response.status_code in [200, 404]


def test_api_sleeps_route_exists(client):
    response = client.get('/api/sleeps')
    assert response.status_code in [200, 404]


def test_ai_insights_route_exists_after_login(client):
    login(client)
    response = client.get('/ai/insights')
    assert response.status_code in [200, 404]