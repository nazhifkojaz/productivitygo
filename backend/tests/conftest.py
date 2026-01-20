"""
Pytest configuration and fixtures for battle service tests.
"""
import sys
import os
from unittest.mock import Mock, patch
import pytest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture
def mock_supabase():
    """Mock supabase client for testing."""
    with patch('services.battle_service.supabase') as mock:
        yield mock


@pytest.fixture
def sample_battle_data():
    """Sample battle data for testing."""
    return {
        'id': 'battle-123',
        'user1_id': 'user-1',
        'user2_id': 'user-2',
        'start_date': '2026-01-20',
        'end_date': '2026-01-22',
        'duration': 3,
        'current_round': 0,
        'status': 'active',
        'winner_id': None,
        'created_at': '2026-01-19T00:00:00Z'
    }


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
