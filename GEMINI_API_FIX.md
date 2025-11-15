# Gemini API Configuration Fix

## Problem
Gemini API calls are failing because `genai.configure()` is being called **after** agents are initialized.

## Root Cause
When you run `Orchestrator(db)`, it creates agents, and each agent's `__init__` method creates a `genai.GenerativeModel()` instance. If the API hasn't been configured yet (via `genai.configure(api_key=...)`), the models won't have proper credentials, causing API calls to fail.

## Solution

### Step 1: Ensure Correct Cell Order
Your notebook cells MUST run in this exact order:

```
1. Install packages (pip install)
2. Import statements
3. ⚠️ API KEY CONFIGURATION (see below)
4. Define classes (ToonNotation, DatabaseManager, etc.)
5. Create database
6. Create orchestrator
7. Run processing
```

### Step 2: Fix the API Configuration Cell
Find the cell that retrieves your API key and make sure it looks like this:

```python
# %% Cell: Configure Gemini API (MUST BE EARLY IN NOTEBOOK!)
from kaggle_secrets import UserSecretsClient
import google.generativeai as genai

# Get API key from Kaggle secrets
user_secrets = UserSecretsClient()
secret_value_0 = user_secrets.get_secret("GOOGLE_API_KEY")

# ⚠️ CRITICAL: Configure API immediately!
genai.configure(api_key=secret_value_0)

print("✓ Gemini API configured successfully")
```

**Key points:**
- This cell must run BEFORE any cell that creates agents or orchestrator
- Must import `genai` if not already imported
- Must call `genai.configure()` in the same cell (or immediately after) getting the secret
- The print statement helps verify it ran successfully

### Step 3: Remove Duplicate Configuration
Search your notebook for any OTHER `genai.configure()` calls and remove them. You should only configure the API **once**, early in the notebook.

### Step 4: Run Diagnostic
Add this cell right after your API configuration to verify it works:

```python
# %% Cell: Test Gemini API
print("Testing Gemini API...")
try:
    test_model = genai.GenerativeModel("gemini-2.0-flash-exp")
    response = test_model.generate_content("Say 'API is working!'")
    print("✅ SUCCESS! API Response:", response.text)
except Exception as e:
    print("❌ FAILED! Error:", str(e))
    print("\nTroubleshooting:")
    print("1. Check that the previous cell with genai.configure() ran successfully")
    print("2. Verify your API key at: https://aistudio.google.com/app/apikey")
    print("3. Make sure you haven't exceeded your quota")
```

### Step 5: Restart and Run All
1. In Kaggle: Click "Run" → "Restart & Run All"
2. Watch for the "✓ Gemini API configured successfully" message
3. Watch for the "✅ SUCCESS!" message from the test
4. If both succeed, continue with normal processing

## Common Errors and Solutions

### Error: "API key not configured"
**Cause:** `genai.configure()` wasn't called before creating agents
**Fix:** Move the API configuration cell to run BEFORE `Orchestrator(db)`

### Error: "Invalid API key" or "401 Unauthorized"
**Cause:** Wrong API key or key not set correctly
**Fix:**
1. Get your API key from https://aistudio.google.com/app/apikey
2. In Kaggle, go to Settings → Secrets
3. Add/update `GOOGLE_API_KEY` with your key
4. Restart kernel and run all cells

### Error: "Resource exhausted" or "429"
**Cause:** Rate limit exceeded
**Fix:**
1. Wait 60 seconds and try again
2. Your code already has rate limiting built in - check `API_CONFIG` settings
3. For free tier: Use `API_CONFIG = APITier.FREE` (10 req/min)

### Error: Cells running out of order
**Cause:** You manually ran cells in wrong sequence
**Fix:** Always use "Restart & Run All" to ensure correct order

## Verification Checklist

Before running your full pipeline, verify:

- [ ] API key cell runs successfully (see ✓ message)
- [ ] API key cell is positioned BEFORE agent definitions
- [ ] API key cell is positioned BEFORE `Orchestrator(db)`
- [ ] Test cell shows "✅ SUCCESS!"
- [ ] No other `genai.configure()` calls exist later in notebook
- [ ] You ran "Restart & Run All" (not individual cells)

## Quick Test Script

If you're still having issues, create a new cell at the top and run this:

```python
# Minimal test
from kaggle_secrets import UserSecretsClient
import google.generativeai as genai

# Configure
user_secrets = UserSecretsClient()
api_key = user_secrets.get_secret("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

# Test
model = genai.GenerativeModel("gemini-2.0-flash-exp")
response = model.generate_content("Say: It works!")
print("✅ Result:", response.text)
```

If this works, your API key is fine. The issue is cell execution order in your main notebook.

## Still Not Working?

If you've followed all steps and it still fails:

1. **Check the exact error message** - what does it say?
2. **Verify API key is valid** - generate a new one if needed
3. **Check quota** - free tier has limits
4. **Try a fresh notebook** - copy working cells to new notebook
5. **Share the error** - post the exact error message for help

## Example: Correct Cell Sequence

```python
# Cell 1: Imports
import sqlite3
import json
import google.generativeai as genai
# ... other imports

# Cell 2: API Configuration ⚠️ MUST BE HERE!
from kaggle_secrets import UserSecretsClient
user_secrets = UserSecretsClient()
secret_value_0 = user_secrets.get_secret("GOOGLE_API_KEY")
genai.configure(api_key=secret_value_0)
print("✓ API configured")

# Cell 3: Test API ✓ Verify it works
test_model = genai.GenerativeModel("gemini-2.0-flash-exp")
print("✅", test_model.generate_content("Test").text)

# Cell 4: Define classes
class ToonNotation:
    ...

# Cell 5: Create database
db = DatabaseManager("project.db")
db.connect()

# Cell 6: Create orchestrator (API already configured!)
orchestrator = Orchestrator(db)

# Cell 7: Process data (everything works!)
job_id = orchestrator.process_data_dictionary(...)
```
