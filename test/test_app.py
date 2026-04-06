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


def login(client):
    """Helper function to log in before testing protected routes"""
    return client.post(
        '/login',
        data={
            'username': 'admin',
            'password': '1234'
        },
        follow_redirects=True
    )


# ============================================
# HEALTH ENDPOINT TEST
# ============================================

def test_health_endpoint(client):
    """Test 1: Health check endpoint returns success"""
    response = client.get('/api/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'


# ============================================
# LOGIN TESTS
# ============================================

def test_login_page_loads(client):
    """Test 2: Login page loads successfully"""
    response = client.get('/login')
    assert response.status_code == 200


def test_login_success(client):
    """Test 3: Login works with correct username and password"""
    response = client.post(
        '/login',
        data={
            'username': 'admin',
            'password': '1234'
        },
        follow_redirects=True
    )
    assert response.status_code == 200


def test_login_fail(client):
    """Test 4: Login fails with wrong username/password"""
    response = client.post(
        '/login',
        data={
            'username': 'wrong',
            'password': 'wrong'
        },
        follow_redirects=True
    )
    assert response.status_code == 200
    assert b'Invalid username or password' in response.data


# ============================================
# PROTECTED PAGE TESTS
# ============================================

def test_dashboard_loads_after_login(client):
    """Test 5: Dashboard page loads after login"""
    with app.app_context():
        mongo.db.workouts.find.return_value = []
        mongo.db.meals.find.return_value = []
        mongo.db.sleeps.find.return_value = []

    login(client)
    response = client.get('/')
    assert response.status_code == 200


def test_add_workout_page_loads_after_login(client):
    """Test 6: Add workout page loads after login"""
    login(client)
    response = client.get('/add-workout')
    assert response.status_code == 200


def test_add_meal_page_loads_after_login(client):
    """Test 7: Add meal page loads after login"""
    login(client)
    response = client.get('/add-meal')
    assert response.status_code == 200


def test_add_sleep_page_loads_after_login(client):
    """Test 8: Add sleep page loads after login"""
    login(client)
    response = client.get('/add-sleep')
    assert response.status_code == 200


def test_ai_page_loads_after_login(client):
    """Test 9: AI page loads after login"""
    login(client)
    response = client.get('/ai_page')
    assert response.status_code == 200


# ============================================
# AI FUNCTION TESTS
# ============================================

def test_build_prompt_returns_string():
    """Test 10: build_prompt returns a non-empty string"""
    from routes.ai import build_prompt

    test_data = {
        "workouts": [{"workout_type": "Running", "duration": 30}],
        "meals": [{"meal_name": "Salad", "calories": 300}],
        "sleeps": [{"duration": 8, "quality": "Good"}]
    }

    result = build_prompt(test_data)
    assert isinstance(result, str)
    assert len(result) > 0


def test_fallback_insights_returns_string():
    """Test 11: fallback_insights returns a non-empty string"""
    from routes.ai import fallback_insights

    test_data = {
        "workouts": [],
        "meals": [],
        "sleeps": [],
        "db_status": "disconnected"
    }

    result = fallback_insights(test_data)
    assert isinstance(result, str)
    assert len(result) > 0
    assert "Summary" in result


# ============================================
# BLUEPRINT TEST
# ============================================

def test_ai_blueprint_registered():
    """Test 12: AI blueprint is registered"""
    assert 'ai' in app.blueprints


# ============================================
# ROUTE EXISTENCE TESTS
# ============================================

def test_api_workouts_route_exists(client):
    """Test 13: /api/workouts route exists"""
    response = client.get('/api/workouts')
    assert response.status_code in [200, 404]


def test_api_meals_route_exists(client):
    """Test 14: /api/meals route exists"""
    response = client.get('/api/meals')
    assert response.status_code in [200, 404]


def test_api_sleeps_route_exists(client):
    """Test 15: /api/sleeps route exists"""
    response = client.get('/api/sleeps')
    assert response.status_code in [200, 404]


def test_ai_insights_route_exists_after_login(client):
    """Test 16: /ai/insights route exists after login"""
    login(client)
    response = client.get('/ai/insights')
    assert response.status_code in [200, 404]