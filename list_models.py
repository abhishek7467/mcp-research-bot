#!/usr/bin/env python3
"""
List available Google Gemini models
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("Checking Available Gemini Models")
print("=" * 60)

gemini_key = os.getenv('GEMINI_API_KEY')

if not gemini_key:
    print("❌ ERROR: GEMINI_API_KEY not found")
    sys.exit(1)

print(f"✓ API Key: {gemini_key[:20]}...")

try:
    import google.generativeai as genai
    
    genai.configure(api_key=gemini_key)
    
    print("\n📋 Listing available models...\n")
    
    for model in genai.list_models():
        if 'generateContent' in model.supported_generation_methods:
            print(f"✓ {model.name}")
            print(f"  Display Name: {model.display_name}")
            print(f"  Description: {model.description}")
            print()
    
except Exception as e:
    print(f"❌ ERROR: {str(e)}")
    sys.exit(1)
