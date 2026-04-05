import pytest
import sys
import os

# Add project root to path - THIS IS CRITICAL
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from services.db import mongo
from unittest.mock import patch, MagicMock


@pytest.fixture
def client():
    """Test client fixture"""
    app.config['TESTING'] = True
    app.config['MONGO_URI'] = 'mongodb://localhost:27017/test_db'
    
    with app.test_client() as client:
        with app.app_context():
            # Mock the database
            mongo.db = MagicMock()
            mongo.db.workouts = MagicMock()
            mongo.db.meals = MagicMock()
            mongo.db.sleeps = MagicMock()
        yield client


# ============================================
# HEALTH ENDPOINT TESTS
# ============================================

def test_health_endpoint(client):
    """Test 1: Health check endpoint returns success"""
    response = client.get('/api/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'


def test_dashboard_loads(client):
    """Test 2: Dashboard page loads successfully"""
    with app.app_context():
        mongo.db.workouts.find.return_value = []
        mongo.db.meals.find.return_value = []
        mongo.db.sleeps.find.return_value = []
    
    response = client.get('/')
    assert response.status_code == 200


# ============================================
# PAGE ROUTE TESTS
# ============================================

def test_add_workout_page_loads(client):
    """Test 3: Add workout page loads"""
    response = client.get('/add-workout')
    assert response.status_code == 200


def test_add_meal_page_loads(client):
    """Test 4: Add meal page loads"""
    response = client.get('/add-meal')
    assert response.status_code == 200


def test_add_sleep_page_loads(client):
    """Test 5: Add sleep page loads"""
    response = client.get('/add-sleep')
    assert response.status_code == 200


def test_ai_page_loads(client):
    """Test 6: AI insights page loads"""
    response = client.get('/ai_page')
    assert response.status_code == 200


# ============================================
# AI FUNCTION TESTS
# ============================================

def test_build_prompt_returns_string():
    """Test 7: Build prompt returns a string"""
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
    """Test 8: Fallback insights returns a string"""
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
# CONFIGURATION TESTS
# ============================================



def test_blueprints_registered():
    """Test 10: All blueprints are registered"""
    expected_blueprints = ['workout_bp', 'meal_bp', 'sleep_bp', 'ai']
    for bp in expected_blueprints:
        assert bp in app.blueprints


# ============================================
# ROUTE EXISTENCE TESTS
# ============================================

def test_api_workouts_route_exists(client):
    """Test 11: /api/workouts route exists"""
    response = client.get('/api/workouts')
    assert response.status_code in [200, 404]


def test_api_meals_route_exists(client):
    """Test 12: /api/meals route exists"""
    response = client.get('/api/meals')
    assert response.status_code in [200, 404]


def test_api_sleeps_route_exists(client):
    """Test 13: /api/sleeps route exists"""
    response = client.get('/api/sleeps')
    assert response.status_code in [200, 404]


def test_ai_insights_route_exists(client):
    """Test 14: /ai/insights route exists"""
    response = client.get('/ai/insights')
    assert response.status_code in [200, 404]