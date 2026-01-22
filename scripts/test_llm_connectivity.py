#!/usr/bin/env python3
"""Test LLM connectivity via OpenRouter."""

import sys
sys.path.insert(0, ".")

from src.reqgate.config.settings import get_settings
from src.reqgate.adapters.llm import OpenRouterClient


def test_model(model: str) -> bool:
    """Test a single model."""
    print(f"\n🔄 Testing: {model}")
    print("-" * 40)
    
    settings = get_settings()
    
    # Create a new client with specific model
    from openai import OpenAI
    client = OpenAI(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
    )
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": "Say 'Hello ReqGate' in JSON format: {\"message\": \"...\"}"}
            ],
            response_format={"type": "json_object"},
            timeout=30,
            extra_headers={
                "HTTP-Referer": "https://reqgate.dev",
                "X-Title": "ReqGate Test",
            },
        )
        
        content = response.choices[0].message.content
        print(f"✅ Success!")
        print(f"   Response: {content[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False


def main():
    print("=" * 50)
    print("ReqGate LLM Connectivity Test")
    print("=" * 50)
    
    settings = get_settings()
    print(f"\n📡 OpenRouter Base URL: {settings.openrouter_base_url}")
    print(f"🔑 API Key: {settings.openrouter_api_key[:20]}...")
    
    # Models to test
    models = [
        settings.llm_model,  # Primary model
        *settings.fallback_models_list,  # Fallback models
    ]
    
    print(f"\n📋 Models to test: {models}")
    
    results = {}
    for model in models:
        results[model] = test_model(model)
    
    # Summary
    print("\n" + "=" * 50)
    print("Summary")
    print("=" * 50)
    
    for model, success in results.items():
        status = "✅ OK" if success else "❌ FAIL"
        print(f"  {model}: {status}")
    
    all_passed = all(results.values())
    print("\n" + ("🎉 All models connected!" if all_passed else "⚠️ Some models failed"))
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
