# Quick Test Guide - AI Assistant Fix

## What Was Fixed

The AI assistant was not recognizing the OpenAI API key configured via the Admin Settings panel. This has been fixed - the assistant now automatically reinitializes when you update the API key through the UI.

## Testing Steps

### 1. Restart the Backend (REQUIRED)

Since we modified the startup code, you need to restart the backend service:

```powershell
# Stop the backend if it's running (Ctrl+C)

# Start it again
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or if using Docker:
```powershell
docker-compose restart backend
```

### 2. Verify Backend Started Successfully

Check the console output for:
```
INFO:     AI Agent with OpenAI+MCP initialized successfully
```

OR (if no API key is set yet):
```
ERROR:    Failed to initialize AI Agent: OpenAI API key not configured
WARNING:  AI Agent will use fallback mode until OpenAI API key is configured via admin settings
```

Both are OK! The second message means it's ready to be configured via admin panel.

### 3. Configure OpenAI API Key

1. Open your browser to: `http://localhost:3000/admin`
2. Go to the **AI Settings** section
3. Enter your OpenAI API key
4. Click **"Validate API Key"** - should show ✅ green checkmark
5. Click **"Save Settings"**

**Important**: Watch the backend console for this message:
```
INFO:     Main AI agent service reinitialized successfully
```

This confirms the fix is working!

### 4. Test the Chat Interface

1. Click the **AI Assistant** chat icon
2. Type: `how to create jira issue?`
3. Press Send

**Expected Result**: You should now get a detailed AI-powered response with:
- Endpoint information (POST /rest/api/3/issue)
- Code examples (Python, cURL)
- Step-by-step instructions
- Related operations

**NOT the old fallback message!**

### 5. Verify It's Really Working

The AI response should include:
- ✅ Specific API endpoint paths
- ✅ Code examples with actual syntax
- ✅ Detailed explanations
- ✅ Uses information from the documentation database

## Troubleshooting

### Issue: Still seeing "not configured" message

**Solution**: 
1. Check backend logs for errors
2. Verify API key was saved (Admin Settings should show masked key like `sk-proj-ab...`)
3. Try refreshing the frontend page
4. Check that the response from Save Settings includes: `"ai_agent_reinitialized": true`

### Issue: API key validation fails

**Solution**:
1. Verify your API key is correct (starts with `sk-proj-` or `sk-`)
2. Check your OpenAI account has available credits
3. Ensure no firewall is blocking OpenAI API (api.openai.com)

### Issue: Backend won't start

**Solution**:
1. Check Python dependencies are installed: `pip install -r requirements.txt`
2. Verify database is running (PostgreSQL)
3. Check the error message in console

## What Changed Technically

### Files Modified:
1. `backend/app/api/v1/ai_settings.py`
   - Added `set_ai_agent_service()` function
   - Modified `update_ai_settings()` to reinitialize AI agent
   
2. `backend/app/main.py`
   - Added service registration on startup
   - Better error handling for initialization failures

### The Fix:
When you update the OpenAI API key via admin panel, the system now:
1. Updates the settings ✅
2. Reinitializes the OpenAI client ✅
3. **Reinitializes the main AI agent service** ✅ (NEW!)
4. Returns confirmation that agent is ready ✅ (NEW!)

## Success Criteria

✅ Backend starts without errors  
✅ Can validate API key in admin panel  
✅ Saving API key shows "ai_agent_reinitialized" in response  
✅ Backend logs show "Main AI agent service reinitialized successfully"  
✅ Chat assistant provides detailed AI responses  
✅ No restart required after configuring API key  

## Additional Notes

- The fix applies immediately - no restart needed after setting API key
- The first time after code changes, you MUST restart the backend
- Your API key is stored in memory only (not persisted to database yet)
- If you restart the backend, you'll need to re-enter the API key via admin panel

---

**Need Help?**  
Check `AI_ASSISTANT_FIX_SUMMARY.md` for detailed technical explanation.

