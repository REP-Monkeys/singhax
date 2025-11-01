"""
Pytest configuration and shared fixtures for all tests.

This file mocks heavy dependencies like OCR libraries that aren't needed for testing.
"""

import sys
from unittest.mock import MagicMock
from types import ModuleType

# Create proper mock modules with __spec__ set
def create_mock_module(name):
    """Create a mock module with __spec__ attribute."""
    mock = MagicMock(spec=ModuleType)
    mock.__spec__ = MagicMock()
    mock.__spec__.name = name
    return mock

# Mock OCR-related modules before they're imported
sys.modules['pytesseract'] = create_mock_module('pytesseract')

pdf2image_mock = create_mock_module('pdf2image')
pdf2image_mock.convert_from_bytes = MagicMock(return_value=[])
sys.modules['pdf2image'] = pdf2image_mock

# Mock PIL with Image submodule
pil_mock = create_mock_module('PIL')
image_mock = create_mock_module('PIL.Image')
pil_mock.Image = image_mock
sys.modules['PIL'] = pil_mock
sys.modules['PIL.Image'] = image_mock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def client():
    """Create test client for FastAPI."""
    from app.main import app
    return TestClient(app)

