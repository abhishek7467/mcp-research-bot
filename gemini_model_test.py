#!/usr/bin/env python3
"""Test script for Google Gemini API"""

import google.generativeai as genai

# API Keys
api_keys = [
    "AIzaSyDDaJMFU_NF9iovJ2iVycIigJng3xhim9w",
    "AIzaSyDzXSas9tXO0u4FkOL_d6lJSH8D0FhHAac",
]

print("Testing Google Gemini API...")
print("=" * 60)

# Configure API
genai.configure(api_key=api_keys[0])
print("✓ Using GOOGLE_API_KEY_7")

# Test chat
print("\nTesting chat...")
try:
    model = genai.GenerativeModel('models/gemini-2.5-flash')
    response = model.generate_content("Hello! Say hi in one sentence.")
    print(f"✓ Response: {response.text}")
    print("\n✓ SUCCESS! API is working!")
except Exception as e:
    print(f"✗ Error: {e}")
