#!/usr/bin/env python3
"""Test DeepSeek API integration."""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_deepseek():
    """Test DeepSeek API connection."""
    print("=" * 50)
    print("Testing DeepSeek API Integration")
    print("=" * 50)
    print()

    try:
        from privateclaw.core.llm.factory import LLMFactory
        from privateclaw.core.llm.config import LLMConfig

        # Create DeepSeek config
        config = LLMConfig(
            provider="deepseek",
            model="deepseek-v4-flash",
            api_key="sk-41384c56db2e4e9ba884e364ac171c44",
            api_base="https://api.deepseek.com",
            temperature=0.7,
        )

        print(f"Provider: {config.provider}")
        print(f"Model: {config.model}")
        print(f"Base URL: {config.api_base}")
        print()

        # Create LLM instance
        print("Creating LLM instance...")
        llm = LLMFactory.create(config)
        print("✓ LLM instance created successfully!")
        print()

        # Test with a simple message
        print("Testing API call...")
        from langchain_core.messages import HumanMessage

        response = await llm.ainvoke([HumanMessage(content="Hello! Say 'PrivateClaw is working!' in one sentence.")])

        print(f"Response: {response.content}")
        print()
        print("=" * 50)
        print("✓ DeepSeek API integration test PASSED!")
        print("=" * 50)

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    success = asyncio.run(test_deepseek())
    sys.exit(0 if success else 1)
