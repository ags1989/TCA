"""
Pytest configuration and fixtures for TFS Confluence Automation tests
"""
import pytest
import asyncio
from typing import AsyncGenerator


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def work_item_id():
    """Fixture providing a test work item ID"""
    return 210636


@pytest.fixture
def test_work_item_id():
    """Fixture providing another test work item ID"""
    return 215042


@pytest.fixture
def houston_work_item_id():
    """Fixture providing Houston project work item ID"""
    return 233918
