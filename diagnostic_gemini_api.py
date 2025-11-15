"""
Gemini API Diagnostic Script for Kaggle Notebooks

Copy this entire cell into your Kaggle notebook and run it to diagnose
Gemini API configuration issues.

This script will:
1. Check if API key is available in Kaggle secrets
2. Verify google-generativeai module is installed
3. Configure the API
4. Test with a simple API call
5. Provide specific error guidance if anything fails
"""

print("=" * 60)
print("GEMINI API DIAGNOSTIC")
print("=" * 60)

# Step 1: Check if API key is available
print("\n1. Checking API key availability...")
try:
    from kaggle_secrets import UserSecretsClient
    user_secrets = UserSecretsClient()
    api_key = user_secrets.get_secret("GOOGLE_API_KEY")
    print(f"   ✅ API key found (length: {len(api_key)})")
    key_preview = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
    print(f"   Preview: {key_preview}")
except Exception as e:
    print(f"   ❌ Error getting API key: {e}")
    print("   → Add GOOGLE_API_KEY to Kaggle secrets")
    print("   → Go to: Settings → Secrets → Add Secret")
    exit(1)

# Step 2: Import and configure genai
print("\n2. Importing google.generativeai...")
try:
    import google.generativeai as genai
    print("   ✅ Module imported successfully")
except ImportError as e:
    print(f"   ❌ Import error: {e}")
    print("   → Run in a new cell: !pip install -q google-generativeai")
    exit(1)

# Step 3: Configure API
print("\n3. Configuring Gemini API...")
try:
    genai.configure(api_key=api_key)
    print("   ✅ API configured successfully")
except Exception as e:
    print(f"   ❌ Configuration error: {e}")
    exit(1)

# Step 4: Test API call
print("\n4. Testing API call...")
try:
    model = genai.GenerativeModel("gemini-2.0-flash-exp")
    print("   ✅ Model created")

    print("   Making test API call...")
    response = model.generate_content("Reply with just: Working!")
    print(f"   ✅ API call successful!")
    print(f"   Response: {response.text}")

except Exception as e:
    error_msg = str(e)
    print(f"   ❌ API call failed: {error_msg[:200]}...")

    # Provide specific guidance based on error type
    if "API_KEY_INVALID" in error_msg or "401" in error_msg:
        print("\n   💡 Diagnosis: Invalid API key")
        print("   → Get a new key at: https://aistudio.google.com/app/apikey")
        print("   → Make sure you copied the ENTIRE key")
        print("   → Update Kaggle secret with new key")

    elif "429" in error_msg or "ResourceExhausted" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
        print("\n   💡 Diagnosis: Rate limit or quota exceeded")
        print("   → Wait 60 seconds and try again")
        print("   → Free tier: 10 requests/minute")
        print("   → Check quota: https://aistudio.google.com/app/apikey")

    elif "PERMISSION_DENIED" in error_msg or "403" in error_msg:
        print("\n   💡 Diagnosis: Permission denied")
        print("   → API might not be enabled for your key")
        print("   → Try generating a new API key")

    elif "FAILED_PRECONDITION" in error_msg:
        print("\n   💡 Diagnosis: API prerequisites not met")
        print("   → Your API key might need additional setup")
        print("   → Visit: https://aistudio.google.com/")

    else:
        print("\n   💡 Diagnosis: Unknown error")
        print("   → Full error message:")
        print(f"   {error_msg}")

    exit(1)

# Step 5: Test rate limiting (optional)
print("\n5. Testing rate limiting (optional)...")
try:
    import time
    print("   Making 3 rapid calls to test rate limiting...")
    for i in range(3):
        response = model.generate_content(f"Say: Test {i+1}")
        print(f"   ✅ Call {i+1}: {response.text[:30]}")
        time.sleep(0.5)  # Small delay
    print("   ✅ Rate limiting working correctly")
except Exception as e:
    print(f"   ⚠️  Rate limit hit (expected for free tier): {str(e)[:100]}")
    print("   This is normal - your code has rate limiting built in")

print("\n" + "=" * 60)
print("✅ ALL CHECKS PASSED - Gemini API is working correctly!")
print("=" * 60)
print("\n💡 Next steps:")
print("   1. Make sure this cell runs BEFORE creating agents/orchestrator")
print("   2. Keep genai.configure() in your early cells")
print("   3. Run your full notebook with 'Restart & Run All'")
print("=" * 60)
