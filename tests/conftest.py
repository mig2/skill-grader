"""Shared pytest fixtures for skill-grader tests."""

from pathlib import Path
import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir():
    return FIXTURES_DIR


@pytest.fixture
def gold_skill(fixtures_dir):
    return fixtures_dir / "gold"


@pytest.fixture
def profiles_path():
    return Path(__file__).parent.parent / "config" / "profiles.yaml"
