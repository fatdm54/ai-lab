"""
Basic tests for AI Lab core modules
"""

import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_api_gateway_import():
    """Test that API gateway can be imported"""
    from core.api_gateway import APIGateway
    assert APIGateway is not None


def test_content_generator_import():
    """Test that content generator can be imported"""
    from core.content_generator import ContentGenerator
    assert ContentGenerator is not None


def test_content_pillar_enum():
    """Test content pillar enum values"""
    from core.content_generator import ContentPillar
    
    assert ContentPillar.AI_TOOLS.value == "ai_tools"
    assert ContentPillar.TUTORIAL.value == "tutorial"
    assert ContentPillar.AUTOMATION.value == "automation"


def test_settings_import():
    """Test that settings can be imported"""
    from config.settings import settings
    assert settings is not None
    assert settings.api.google_rpm == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
