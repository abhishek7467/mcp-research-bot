#!/usr/bin/env python3
"""
Quick test script to verify Google Gemini API key is working
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("Testing Google Gemini API Key")
print("=" * 60)

# Get API key
gemini_key = os.getenv('GEMINI_API_KEY')

if not gemini_key:
    print("❌ ERROR: GEMINI_API_KEY not found in .env file")
    sys.exit(1)

print(f"✓ API Key found: {gemini_key[:20]}...")

# Test Gemini
try:
    import google.generativeai as genai
    
    print("\n✓ google-generativeai package imported successfully")
    
    # Configure with API key
    genai.configure(api_key=gemini_key)
    print("✓ Gemini configured with API key")
    
    # Create model
    model = genai.GenerativeModel('gemini-2.5-flash')
    print("✓ Model created: gemini-2.5-flash")
    
    # Test generation
    print("\n📝 Testing text generation...")
    response = model.generate_content("Write a one-line summary of what AI is.")
    
    print("✓ Generation successful!")
    print(f"\n📄 Response: {response.text}")
    
    print("\n" + "=" * 60)
    print("✅ SUCCESS! Google Gemini API is working correctly")
    print("=" * 60)
    print("\nYou can now run the main orchestrator:")
    print("  python mcp_orchestrator.py --topics 'AI' --max-items 10")
    
except ImportError as e:
    print(f"\n❌ ERROR: google-generativeai not installed")
    print(f"   Run: pip install google-generativeai")
    print(f"   Details: {str(e)}")
    sys.exit(1)
    
except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    print("\nPossible issues:")
    print("  1. Invalid API key")
    print("  2. API key not activated")
    print("  3. Network connection issues")
    print("  4. API quota exceeded")
    sys.exit(1)
