# 🔑 API Key Setup Guide

## Quick Setup with .env File

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Get your OpenAI API Key:**
   - Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
   - Create a new secret key
   - Copy the key (starts with `sk-`)

3. **Add your key to .env:**
   ```bash
   # Open .env in your favorite editor
   nano .env
   
   # Or use echo
   echo "OPENAI_API_KEY=sk-your-actual-key-here" > .env
   ```

4. **Verify it works:**
   ```bash
   uv run python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('API Key found:', 'Yes' if os.getenv('OPENAI_API_KEY') else 'No')"
   ```

## Security Notes

✅ **Safe practices:**
- The `.env` file is automatically ignored by git
- Your API key stays on your local machine
- The app masks your key when displaying it

❌ **Avoid these:**
- Don't commit .env files to version control
- Don't share your API key in screenshots or logs
- Don't use API keys in public code

## Alternative Methods

### Environment Variable
```bash
export OPENAI_API_KEY=sk-your-key-here
uv run python translate.py
```

### Shell Profile (Persistent)
Add to `~/.zshrc` or `~/.bashrc`:
```bash
export OPENAI_API_KEY=sk-your-key-here
```

### Interactive Input
If no key is found, the app will prompt you to enter it securely.

---

**Ready to go!** Run `uv run python translate.py` and your API key will be loaded automatically.