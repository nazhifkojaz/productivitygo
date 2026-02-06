"""
Pytest configuration and shared fixtures for ProductivityGo backend tests.

This file provides common test fixtures used across all test modules.
Fixtures are automatically available to any test file in the tests/ directory.
"""
import sys
import os
from unittest.mock import Mock, patch
import pytest
from datetime import date

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# -----------------------------------------------------------------------------
# Mock Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def mock_supabase():
    """Mock supabase client for testing."""
    with patch('services.battle_service.supabase') as mock:
        yield mock


@pytest.fixture
def mock_user():
    """Mock authenticated user."""
    return Mock(id="user-123", email="test@example.com")


# -----------------------------------------------------------------------------
# Battle Data Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def sample_battle_data():
    """Sample active battle for testing."""
    return {
        'id': 'battle-123',
        'user1_id': 'user-1',
        'user2_id': 'user-2',
        'start_date': '2026-01-20',
        'end_date': '2026-01-25',
        'duration': 5,
        'current_round': 0,
        'status': 'active',
        'winner_id': None,
        'created_at': '2026-01-19T00:00:00Z'
    }


@pytest.fixture
def sample_pending_battle():
    """Sample pending battle."""
    return {
        'id': 'battle-123',
        'user1_id': 'user-1',
        'user2_id': 'user-2',
        'status': 'pending',
        'start_date': '2026-01-21',
        'end_date': '2026-01-25',
        'duration': 5
    }


@pytest.fixture
def sample_battle_with_profiles():
    """Sample battle with both profiles present."""
    return {
        'id': 'battle-123',
        'user1_id': 'user-123',
        'user2_id': 'user-456',
        'start_date': '2026-01-20',
        'end_date': '2026-01-22',
        'duration': 3,
        'current_round': 0,
        'status': 'active',
        'user1': {
            'username': 'PlayerOne',
            'level': 5,
            'timezone': 'America/New_York',
            'battle_win_count': 3,
            'battle_count': 10,
            'total_xp_earned': 2500,
            'completed_tasks': 45
        },
        'user2': {
            'username': 'PlayerTwo',
            'level': 3,
            'timezone': 'Europe/London',
            'battle_win_count': 1,
            'battle_count': 5,
            'total_xp_earned': 1200,
            'completed_tasks': 25
        }
    }


# -----------------------------------------------------------------------------
# RPC Result Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def sample_completion_result():
    """Sample result from complete_battle RPC."""
    return {
        'winner_id': 'user-1',
        'user1_total_xp': 350,
        'user2_total_xp': 280,
        'already_completed': False
    }


@pytest.fixture
def sample_already_completed_result():
    """Sample result when battle was already completed (idempotent call)."""
    return {
        'winner_id': 'user-1',
        'user1_total_xp': 350,
        'user2_total_xp': 280,
        'already_completed': True
    }


# -----------------------------------------------------------------------------
# Profile Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def sample_profile():
    """Sample user profile."""
    return {
        'id': 'user-123',
        'username': 'TestUser',
        'level': 5,
        'timezone': 'UTC',
        'battle_win_count': 3,
        'battle_count': 10,
        'total_xp_earned': 2500,
        'completed_tasks': 45
    }


@pytest.fixture
def default_profile():
    """Default profile with fallback values."""
    return {
        'timezone': 'UTC',
        'username': 'Unknown',
        'level': 1,
        'battle_win_count': 0,
        'battle_count': 0,
        'total_xp_earned': 0,
        'completed_tasks': 0
    }
