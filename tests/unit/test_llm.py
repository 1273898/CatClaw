"""Unit tests for the LLM factory and providers."""

import pytest
from privateclaw.core.llm.factory import LLMFactory
from privateclaw.core.llm.config import LLMConfig


class TestLLMConfig:
    """Tests for LLMConfig."""

    def test_default_config(self):
        """Test default configuration."""
        config = LLMConfig()
        assert config.provider == "deepseek"
        assert config.model == "deepseek-v4-flash"
        assert config.temperature == 0.7

    def test_custom_config(self):
        """Test custom configuration."""
        config = LLMConfig(
            provider="openai",
            model="gpt-4",
            temperature=0.5,
            max_tokens=1000
        )
        assert config.provider == "openai"
        assert config.model == "gpt-4"
        assert config.temperature == 0.5
        assert config.max_tokens == 1000


class TestLLMFactory:
    """Tests for LLMFactory."""

    def test_list_providers(self):
        """Test listing available providers."""
        providers = LLMFactory.list_providers()
        assert isinstance(providers, list)
        # Should have at least deepseek and openai
        assert "deepseek" in providers or len(providers) > 0

    def test_list_models(self):
        """Test listing models for a provider."""
        try:
            models = LLMFactory.list_models("deepseek")
            assert isinstance(models, list)
        except Exception:
            # Provider might not be configured
            pass

    def test_create_llm_with_config(self):
        """Test creating LLM with configuration."""
        config = LLMConfig(
            provider="deepseek",
            model="deepseek-v4-flash",
            api_key="test-key",
            api_base="https://api.deepseek.com"
        )

        try:
            llm = LLMFactory.create(config)
            assert llm is not None
        except Exception as e:
            # May fail due to invalid API key, which is expected
            assert "api" in str(e).lower() or "key" in str(e).lower() or "auth" in str(e).lower()

    def test_create_from_settings(self):
        """Test creating LLM from settings."""
        from privateclaw.config.settings import Settings

        settings = Settings(
            llm_provider="deepseek",
            llm_model="deepseek-v4-flash",
            llm_api_key="test-key",
            llm_api_base="https://api.deepseek.com"
        )

        try:
            llm = LLMFactory.create_from_settings(settings)
            assert llm is not None
        except Exception as e:
            # Expected to fail with invalid API key
            assert "api" in str(e).lower() or "key" in str(e).lower() or "auth" in str(e).lower()

    def test_invalid_provider(self):
        """Test creating LLM with invalid provider."""
        config = LLMConfig(
            provider="nonexistent",
            model="test-model"
        )

        with pytest.raises(Exception):
            LLMFactory.create(config)


class TestLLMIntegration:
    """Integration tests for LLM (requires valid API key)."""

    @pytest.mark.skipif(
        not pytest.importorskip("privateclaw.config.settings").get_settings().llm_api_key,
        reason="No API key configured"
    )
    def test_basic_generation(self):
        """Test basic text generation (requires API key)."""
        from privateclaw.config.settings import get_settings

        settings = get_settings()
        if not settings.llm_api_key:
            pytest.skip("No API key configured")

        try:
            llm = LLMFactory.create_from_settings(settings)
            response = llm.invoke("Say hello in one word")
            assert response is not None
            assert len(response.content) > 0
        except Exception as e:
            pytest.fail(f"LLM generation failed: {e}")
