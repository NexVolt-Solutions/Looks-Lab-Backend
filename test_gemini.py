"""
Test script for Gemini API configuration.
Run this to verify your API key and model are working correctly.
"""
import google.generativeai as genai

from app.core.config import settings

print("=" * 60)
print("🧪 Testing Gemini Configuration")
print("=" * 60)

# Display configuration
print(f"\n📋 Configuration:")
print(f"   Model: {settings.GEMINI_MODEL}")
print(f"   API Key: {settings.GEMINI_API_KEY[:20]}...{settings.GEMINI_API_KEY[-4:]}")
print(f"   Environment: {settings.ENV}")

# Configure Gemini
try:
    genai.configure(api_key=settings.GEMINI_API_KEY)
    print(f"\n✅ API Key configured successfully")
except Exception as e:
    print(f"\n❌ Failed to configure API key: {e}")
    exit(1)

# Test 1: Simple text generation
print("\n" + "=" * 60)
print("🧪 Test 1: Simple Text Generation")
print("=" * 60)

try:
    model = genai.GenerativeModel(settings.GEMINI_MODEL)
    response = model.generate_content("Say hello to Looks Lab!")
    print(f"\n✅ Model: {settings.GEMINI_MODEL}")
    print(f"✅ Response: {response.text}")
except Exception as e:
    print(f"\n❌ Test 1 failed: {e}")
    exit(1)

# Test 2: Vision capabilities (food analysis simulation)
print("\n" + "=" * 60)
print("🧪 Test 2: Vision Capabilities (Food Analysis)")
print("=" * 60)

try:
    response = model.generate_content(
        "Describe what a healthy balanced meal looks like in terms of "
        "macronutrients (protein, carbs, fats) and portion sizes."
    )
    print(f"\n✅ Vision test passed")
    print(f"✅ Response:\n{response.text}")
except Exception as e:
    print(f"\n❌ Test 2 failed: {e}")
    exit(1)

# Test 3: JSON structured output (used in your app)
print("\n" + "=" * 60)
print("🧪 Test 3: Structured JSON Output")
print("=" * 60)

try:
    response = model.generate_content(
        """Analyze this food: Grilled Chicken Salad

        Return ONLY valid JSON with this exact structure:
        {
          "food_name": "...",
          "calories": 0,
          "protein": 0,
          "carbs": 0,
          "fat": 0
        }"""
    )
    print(f"\n✅ JSON generation test passed")
    print(f"✅ Response:\n{response.text}")
except Exception as e:
    print(f"\n❌ Test 3 failed: {e}")
    exit(1)

print("\n" + "=" * 60)
print("🎉 All tests passed! Gemini is configured correctly!")
print("=" * 60)

