# API Keys Setup Guide

## Quick Setup

### 1. Claude (Anthropic) API Key ✅

**Get your API key:**
1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Sign up or log in
3. Navigate to **API Keys**
4. Create a new key (starts with `sk-ant-api03-`)

**Set environment variable:**
```bash
# Windows (PowerShell)
$env:ANTHROPIC_API_KEY="YOUR_ANTHROPIC_API_KEY_HERE"

# Windows (CMD)
set ANTHROPIC_API_KEY=YOUR_ANTHROPIC_API_KEY_HERE

# Linux/Mac
export ANTHROPIC_API_KEY="YOUR_ANTHROPIC_API_KEY_HERE"
```

**Or add to `.env` file:**
```
ANTHROPIC_API_KEY=YOUR_ANTHROPIC_API_KEY_HERE
```

### 2. Grok (xAI) API Key

**Get your API key:**
1. Go to [x.ai](https://x.ai) and sign up
2. Navigate to **API Keys** section
3. Create a new key (starts with `xai-`)

**Set environment variable:**
```bash
# Windows (PowerShell)
$env:XAI_API_KEY="YOUR_XAI_API_KEY_HERE"

# Windows (CMD)
set XAI_API_KEY=YOUR_XAI_API_KEY_HERE

# Linux/Mac
export XAI_API_KEY="YOUR_XAI_API_KEY_HERE"
```

**Or add to `.env` file:**
```
XAI_API_KEY=YOUR_XAI_API_KEY_HERE
```

**Note:** The system also accepts `GROK_API_KEY` as an alternative name.

### 3. OpenAI API Key (Already Configured ✅)

You mentioned this is already set up. If you need to verify or update:

```bash
# Check if set
echo $env:OPENAI_API_KEY  # PowerShell
echo %OPENAI_API_KEY%     # CMD
echo $OPENAI_API_KEY      # Linux/Mac
```

### 4. BioGPT via Hugging Face (Optional - Free!)

**BioGPT is open-source and free!** You can use it via Hugging Face Inference API:

1. Go to [huggingface.co](https://huggingface.co) and sign up (free)
2. Go to your profile → **Settings** → **Access Tokens**
3. Click **"New token"** → Select **"Read"** role → Generate
4. Copy the token (starts with `hf_`)

**Set environment variable:**
```bash
# PowerShell
$env:HUGGINGFACEHUB_API_TOKEN="hf_..."

# Or alternative name
$env:HF_API_KEY="hf_..."
```

**Note:** Free tier has rate limits (~1,000 requests/day). Perfect for development!

### 5. Groq API Key (Optional - Different from Grok!)

**Important:** Groq and Grok are different services:
- **Groq**: Fast inference platform (groq.com) - provides LLaMA/Mixtral models
- **Grok**: xAI's model (x.ai) - you already have this!

If you want Groq (for fast inference with LLaMA/Mixtral):
1. Go to [console.groq.com](https://console.groq.com)
2. Sign up or log in
3. Navigate to **API Keys**
4. Create a new key
5. Set: `GROQ_API_KEY=...`

**Note:** Groq does NOT provide BioGPT - use Hugging Face for BioGPT!

## Complete Environment Variables

Create a `.env` file in your project root:

```env
# Required (minimum)
OPENAI_API_KEY=sk-...

# Optional (for enhanced features)
ANTHROPIC_API_KEY=YOUR_ANTHROPIC_API_KEY_HERE
XAI_API_KEY=YOUR_XAI_API_KEY_HERE
HUGGINGFACEHUB_API_TOKEN=hf_...  # Free! For BioGPT
GROQ_API_KEY=...  # Only if you want Groq (for LLaMA/Mixtral, not BioGPT)
WRITER_API_KEY=...  # Only if you have Palmyra-Med access
```

## Model Selection by API Key

| API Key Set | Models Available | Best For |
|-------------|------------------|----------|
| `OPENAI_API_KEY` only | GPT-4o-mini, GPT-4o | All features (cost-effective) |
| + `ANTHROPIC_API_KEY` | + Claude Opus, Sonnet | Better causal reasoning |
| + `XAI_API_KEY` | + Grok-2 | Fast reasoning, literature |
| + `HUGGINGFACEHUB_API_TOKEN` | + BioGPT | **Biomedical literature** (free!) |
| + `GROQ_API_KEY` | + LLaMA-3, Mixtral | Fast inference (not BioGPT) |

## Testing Your Keys

After setting up, restart your Streamlit server and check the console. The system will automatically detect available models.

You can also test in Python:
```python
import os
from src.ai.medical_llm import get_available_models

models = get_available_models()
print("Available models:", models)
```

## Security Notes

⚠️ **Never commit API keys to git!**

- Add `.env` to `.gitignore`
- Use environment variables in production
- Rotate keys if exposed
- Use different keys for dev/prod

## Troubleshooting

**"No models available"**
- Check API keys are set: `echo $env:OPENAI_API_KEY`
- Restart Streamlit server after setting keys
- Check key format (should start with `sk-` for OpenAI, `sk-ant-` for Claude, `xai-` for Grok)

**"API error"**
- Verify key is valid (not expired/revoked)
- Check internet connection
- Verify billing/quota on provider dashboard

