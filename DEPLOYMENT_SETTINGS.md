# ⚠️ Important: Python Version Settings

## The Problem
The deployment platform is using **Python 3.13**, but pydantic-core doesn't have pre-built wheels for it, causing build failures.

## ✅ Solution: Force Python 3.11

### For Streamlit Cloud:
1. Go to your app settings: https://share.streamlit.io/
2. Click on your app → **Settings** (⚙️)
3. Under **Advanced settings**:
   - **Python version:** Select **3.11** (NOT 3.13)
4. Save and redeploy

### For Railway:
- Add environment variable: `PYTHON_VERSION=3.11`
- Or Railway should respect `runtime.txt` automatically

### For Render:
- In your service settings:
  - **Environment:** Python 3
  - **Python Version:** 3.11
- Or add buildpack: `heroku/python` with `runtime.txt`

## Current Configuration

✅ `runtime.txt` = `python-3.11.9`  
✅ `requirements.txt` = `pydantic==2.7.4` (Python 3.11 compatible)

## After Setting Python 3.11

The deployment should succeed because:
- Python 3.11 has pre-built wheels for pydantic-core 2.7.4
- No need to build from source
- Faster installation
