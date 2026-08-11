import pytest
from unittest.mock import MagicMock
from app.infrastructure.db.models import DeveloperEvent, Skill, SkillEvent


@pytest.fixture
def mock_db():
    """A mock DB session for tests that don't need a real database."""
    db = MagicMock()
    return db


@pytest.fixture
def sample_event():
    """A real-shaped DeveloperEvent, matching what extraction actually produces."""
    event = MagicMock(spec=DeveloperEvent)
    event.id = "test-event-id"
    event.user_id = "test-user-id"
    event.technology_tags = "redis, celery, python"
    return event