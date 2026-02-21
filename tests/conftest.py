"""
Pytest configuration and shared fixtures.
Author: Patrick Cooper
"""

import pytest
from unittest.mock import patch


UNIT_TEST_MODEL = "test-model/unit-test"


@pytest.fixture(autouse=True)
def mock_default_model(request):
    """
    Patch _get_default_model for all unit tests so they don't require a
    running server. Integration tests (classes containing 'Integration')
    are excluded and make real calls.
    """
    cls = getattr(request.node, "cls", None)
    is_integration = cls is not None and "Integration" in cls.__name__

    if is_integration:
        yield
        return

    with patch(
        "src.client.curc_llm_client.CURCLLMClient._get_default_model",
        return_value=UNIT_TEST_MODEL,
    ):
        yield
