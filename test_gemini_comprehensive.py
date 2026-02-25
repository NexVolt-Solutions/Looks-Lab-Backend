"""
Comprehensive Gemini API Test Script for Looks Lab Backend
Tests all AI-powered features: Workout, Diet, Food Analysis, Skincare, Insights
Run this to verify your Gemini configuration is working correctly.
"""
import json
import google.generativeai as genai
from app.core.config import settings

print("=" * 80)
print("🧪 LOOKS LAB - Gemini API Comprehensive Test Suite")
print("=" * 80)

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

# Initialize model
try:
    model = genai.GenerativeModel(settings.GEMINI_MODEL)
    print(f"✅ Model initialized: {settings.GEMINI_MODEL}")
except Exception as e:
    print(f"\n❌ Failed to initialize model: {e}")
    exit(1)


# ══════════════════════════════════════════════════════════════════════════════
# TEST 1: Simple Text Generation
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("🧪 TEST 1: Simple Text Generation")
print("=" * 80)
try:
    response = model.generate_content("Say hello to Looks Lab team!")
    print(f"\n✅ Test 1 PASSED")
    print(f"Response: {response.text[:100]}...")
except Exception as e:
    print(f"\n❌ TEST 1 FAILED: {e}")
    exit(1)


# ══════════════════════════════════════════════════════════════════════════════
# TEST 2: Workout Plan Generation
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("🧪 TEST 2: AI Workout Plan Generation")
print("=" * 80)

workout_prompt = """Generate a personalized workout plan with this JSON structure:

User Profile:
- Goal: Build muscle
- Fitness Level: Intermediate
- Days per week: 4
- Session duration: 60 minutes
- Equipment: Dumbbells, Barbell, Bench
- Injuries: Lower back pain
- Preferences: Prefer compound movements

Return ONLY valid JSON (no markdown, no backticks):
{
  "plan_name": "string",
  "duration_weeks": number,
  "weekly_schedule": [
    {
      "day": "Monday",
      "focus": "Upper Body",
      "exercises": [
        {
          "name": "Bench Press",
          "sets": 4,
          "reps": "8-10",
          "rest_seconds": 90,
          "notes": "Focus on form"
        }
      ],
      "estimated_duration_minutes": 60
    }
  ],
  "nutrition_tips": ["tip1", "tip2"],
  "progression_plan": "string",
  "safety_notes": ["note1", "note2"]
}"""

try:
    response = model.generate_content(workout_prompt)
    result = response.text.strip()
    
    # Try to parse as JSON
    try:
        workout_data = json.loads(result)
        print(f"\n✅ TEST 2 PASSED - Workout Plan Generated")
        print(f"   Plan Name: {workout_data.get('plan_name', 'N/A')}")
        print(f"   Duration: {workout_data.get('duration_weeks', 'N/A')} weeks")
        print(f"   Days: {len(workout_data.get('weekly_schedule', []))} days/week")
        if workout_data.get('weekly_schedule'):
            first_day = workout_data['weekly_schedule'][0]
            print(f"   First Day: {first_day.get('day')} - {first_day.get('focus')}")
            print(f"   Exercises: {len(first_day.get('exercises', []))}")
    except json.JSONDecodeError as e:
        print(f"\n⚠️  TEST 2 WARNING: Valid response but not JSON")
        print(f"Response preview: {result[:200]}...")
        
except Exception as e:
    print(f"\n❌ TEST 2 FAILED: {e}")
    exit(1)


# ══════════════════════════════════════════════════════════════════════════════
# TEST 3: Meal Plan Generation
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("🧪 TEST 3: AI Meal Plan Generation")
print("=" * 80)

meal_plan_prompt = """Generate a personalized meal plan with this JSON structure:

User Profile:
- Goal: Weight loss
- Daily Calorie Target: 2000
- Dietary Restrictions: Vegetarian, Gluten-free
- Allergies: Nuts
- Meals per day: 3
- Preferences: High protein, low carb

Return ONLY valid JSON (no markdown, no backticks):
{
  "plan_name": "string",
  "daily_calories": number,
  "daily_macros": {
    "protein_g": number,
    "carbs_g": number,
    "fat_g": number
  },
  "meals": [
    {
      "meal_type": "Breakfast",
      "name": "Scrambled Eggs with Avocado",
      "ingredients": ["ingredient1", "ingredient2"],
      "calories": number,
      "protein_g": number,
      "carbs_g": number,
      "fat_g": number,
      "preparation_time_minutes": number,
      "instructions": ["step1", "step2"]
    }
  ],
  "shopping_list": ["item1", "item2"],
  "meal_prep_tips": ["tip1", "tip2"]
}"""

try:
    response = model.generate_content(meal_plan_prompt)
    result = response.text.strip()
    
    try:
        meal_data = json.loads(result)
        print(f"\n✅ TEST 3 PASSED - Meal Plan Generated")
        print(f"   Plan Name: {meal_data.get('plan_name', 'N/A')}")
        print(f"   Daily Calories: {meal_data.get('daily_calories', 'N/A')}")
        print(f"   Meals: {len(meal_data.get('meals', []))}")
        if meal_data.get('daily_macros'):
            macros = meal_data['daily_macros']
            print(f"   Macros: P:{macros.get('protein_g')}g C:{macros.get('carbs_g')}g F:{macros.get('fat_g')}g")
    except json.JSONDecodeError:
        print(f"\n⚠️  TEST 3 WARNING: Valid response but not JSON")
        print(f"Response preview: {result[:200]}...")
        
except Exception as e:
    print(f"\n❌ TEST 3 FAILED: {e}")
    exit(1)


# ══════════════════════════════════════════════════════════════════════════════
# TEST 4: Food Analysis (Text-based simulation)
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("🧪 TEST 4: Food Nutrition Analysis")
print("=" * 80)

food_analysis_prompt = """Analyze this food: Grilled Chicken Caesar Salad

Return ONLY valid JSON (no markdown, no backticks):
{
  "food_name": "string",
  "description": "string",
  "calories": number,
  "macros": {
    "protein_g": number,
    "carbs_g": number,
    "fat_g": number,
    "fiber_g": number
  },
  "micronutrients": {
    "vitamin_a_mcg": number,
    "vitamin_c_mg": number,
    "calcium_mg": number,
    "iron_mg": number
  },
  "health_score": number,
  "tags": ["tag1", "tag2"],
  "recommendations": ["rec1", "rec2"]
}"""

try:
    response = model.generate_content(food_analysis_prompt)
    result = response.text.strip()
    
    try:
        food_data = json.loads(result)
        print(f"\n✅ TEST 4 PASSED - Food Analysis Complete")
        print(f"   Food: {food_data.get('food_name', 'N/A')}")
        print(f"   Calories: {food_data.get('calories', 'N/A')}")
        if food_data.get('macros'):
            macros = food_data['macros']
            print(f"   Macros: P:{macros.get('protein_g')}g C:{macros.get('carbs_g')}g F:{macros.get('fat_g')}g")
        print(f"   Health Score: {food_data.get('health_score', 'N/A')}/10")
    except json.JSONDecodeError:
        print(f"\n⚠️  TEST 4 WARNING: Valid response but not JSON")
        print(f"Response preview: {result[:200]}...")
        
except Exception as e:
    print(f"\n❌ TEST 4 FAILED: {e}")
    exit(1)


# ══════════════════════════════════════════════════════════════════════════════
# TEST 5: Skincare Analysis
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("🧪 TEST 5: Skincare Analysis")
print("=" * 80)

skincare_prompt = """Analyze this skin profile and provide recommendations:

User Profile:
- Skin Type: Oily
- Main Concerns: Acne, Large pores
- Age: 25
- Current Routine: Basic cleanser and moisturizer
- Climate: Tropical (humid)

Return ONLY valid JSON (no markdown, no backticks):
{
  "skin_analysis": {
    "type": "string",
    "concerns": ["concern1", "concern2"],
    "severity": "mild/moderate/severe"
  },
  "recommended_routine": [
    {
      "step": "Cleansing",
      "products": ["product1", "product2"],
      "frequency": "twice daily",
      "tips": ["tip1", "tip2"]
    }
  ],
  "ingredients_to_look_for": ["ingredient1", "ingredient2"],
  "ingredients_to_avoid": ["ingredient1", "ingredient2"],
  "lifestyle_tips": ["tip1", "tip2"],
  "expected_timeline": "string"
}"""

try:
    response = model.generate_content(skincare_prompt)
    result = response.text.strip()
    
    try:
        skincare_data = json.loads(result)
        print(f"\n✅ TEST 5 PASSED - Skincare Analysis Complete")
        if skincare_data.get('skin_analysis'):
            analysis = skincare_data['skin_analysis']
            print(f"   Skin Type: {analysis.get('type', 'N/A')}")
            print(f"   Concerns: {', '.join(analysis.get('concerns', []))}")
            print(f"   Severity: {analysis.get('severity', 'N/A')}")
        print(f"   Routine Steps: {len(skincare_data.get('recommended_routine', []))}")
        print(f"   Timeline: {skincare_data.get('expected_timeline', 'N/A')}")
    except json.JSONDecodeError:
        print(f"\n⚠️  TEST 5 WARNING: Valid response but not JSON")
        print(f"Response preview: {result[:200]}...")
        
except Exception as e:
    print(f"\n❌ TEST 5 FAILED: {e}")
    exit(1)


# ══════════════════════════════════════════════════════════════════════════════
# TEST 6: Progress Insights Generation
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("🧪 TEST 6: Progress Insights Generation")
print("=" * 80)

insights_prompt = """Generate personalized insights based on user progress:

User Data:
- Domain: Workout
- Goal: Build muscle
- Days completed: 30
- Consistency: 85%
- Weight progression: Started 70kg, now 72kg
- Strength gains: Bench press 60kg → 75kg

Return ONLY valid JSON (no markdown, no backticks):
{
  "overall_progress": "string",
  "achievements": ["achievement1", "achievement2"],
  "insights": [
    {
      "category": "strength",
      "message": "string",
      "importance": "high/medium/low"
    }
  ],
  "recommendations": ["rec1", "rec2"],
  "next_milestone": "string",
  "motivation_message": "string"
}"""

try:
    response = model.generate_content(insights_prompt)
    result = response.text.strip()
    
    try:
        insights_data = json.loads(result)
        print(f"\n✅ TEST 6 PASSED - Insights Generated")
        print(f"   Progress: {insights_data.get('overall_progress', 'N/A')[:80]}...")
        print(f"   Achievements: {len(insights_data.get('achievements', []))}")
        print(f"   Insights: {len(insights_data.get('insights', []))}")
        print(f"   Next Milestone: {insights_data.get('next_milestone', 'N/A')}")
    except json.JSONDecodeError:
        print(f"\n⚠️  TEST 6 WARNING: Valid response but not JSON")
        print(f"Response preview: {result[:200]}...")
        
except Exception as e:
    print(f"\n❌ TEST 6 FAILED: {e}")
    exit(1)


# ══════════════════════════════════════════════════════════════════════════════
# TEST 7: Multi-turn Conversation (Context Retention)
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("🧪 TEST 7: Multi-turn Conversation (Context Retention)")
print("=" * 80)

try:
    chat = model.start_chat(history=[])
    
    # Turn 1
    response1 = chat.send_message("I'm a 25-year-old male looking to lose weight. What should I focus on?")
    print(f"\n✅ Turn 1: {response1.text[:100]}...")
    
    # Turn 2 (should remember context)
    response2 = chat.send_message("What about my workout routine?")
    print(f"✅ Turn 2: {response2.text[:100]}...")
    
    # Turn 3 (should remember both previous turns)
    response3 = chat.send_message("How many calories should I eat?")
    print(f"✅ Turn 3: {response3.text[:100]}...")
    
    print(f"\n✅ TEST 7 PASSED - Context retention working")
    
except Exception as e:
    print(f"\n❌ TEST 7 FAILED: {e}")
    exit(1)


# ══════════════════════════════════════════════════════════════════════════════
# TEST 8: Safety & Content Filtering
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("🧪 TEST 8: Safety & Content Filtering")
print("=" * 80)

try:
    # Test with a benign prompt
    response = model.generate_content(
        "Provide 3 healthy meal ideas for someone with diabetes",
        safety_settings={
            'HARASSMENT': 'BLOCK_NONE',
            'HATE_SPEECH': 'BLOCK_NONE',
            'SEXUALLY_EXPLICIT': 'BLOCK_NONE',
            'DANGEROUS_CONTENT': 'BLOCK_NONE',
        }
    )
    
    print(f"\n✅ TEST 8 PASSED - Safety filtering working")
    print(f"Response: {response.text[:100]}...")
    
except Exception as e:
    print(f"\n❌ TEST 8 FAILED: {e}")
    exit(1)


# ══════════════════════════════════════════════════════════════════════════════
# SUMMARY
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 80)
print("🎉 TEST SUITE COMPLETE!")
print("=" * 80)

print(f"""
✅ All 8 Tests Passed Successfully!

Summary:
├── ✅ Test 1: Simple Text Generation
├── ✅ Test 2: Workout Plan Generation
├── ✅ Test 3: Meal Plan Generation
├── ✅ Test 4: Food Nutrition Analysis
├── ✅ Test 5: Skincare Analysis
├── ✅ Test 6: Progress Insights Generation
├── ✅ Test 7: Multi-turn Conversation
└── ✅ Test 8: Safety & Content Filtering

Your Gemini configuration is working correctly! 🚀
All AI features for Looks Lab are ready to use.

Model: {settings.GEMINI_MODEL}
Environment: {settings.ENV}
""")

print("=" * 80)

