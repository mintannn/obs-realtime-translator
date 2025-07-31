# 🎙️ OBS Real-Time Translation Tool - UV Setup Guide

This tool now runs perfectly on macOS using UV with a modern Rich CLI interface!

## 🚀 Quick Start

```bash
# Install system dependency (one-time setup)
brew install portaudio

# Install dependencies
uv sync

# Option 1: Create .env file for API key (recommended)
cp .env.example .env
# Edit .env and add your OpenAI API key

# Option 2: Set environment variable
export OPENAI_API_KEY=sk-your-key-here

# Run the application
uv run python translate.py
```

## 📋 What Changed

### ✅ Replaced Tkinter with Rich
- **Before**: Clunky GUI dialogs and buttons
- **After**: Beautiful, modern CLI with Rich formatting
- **Benefits**: No Tkinter dependency issues, better UX, works in any terminal

### ✅ Pure UV Workflow  
- Uses UV's Python 3.10 (no system Python needed)
- All dependencies managed through `pyproject.toml`
- Clean, isolated environment

### ✅ Enhanced Interface
- 🎨 Colorful status messages and progress indicators
- 📊 Real-time status table
- 💬 Interactive command menu (`start`, `stop`, `status`, `quit`)
- 🔐 Secure API key input (hidden from terminal history)

### ✅ Environment Variable Support
- 📁 `.env` file support for API key storage
- 🔒 No need to enter API key every time
- 🛡️ Automatic .gitignore protection for secrets

## 🎮 Using the Application

When you run `uv run python translate.py`, you'll see:

**With .env file:**
```
╭──────────────────────────────────────────╮
│ 🎙️  OBS Real-Time Translation Tool        │
│ Japanese ⇔ English Real-time Translation │
│ Created by: minta                        │
╰──────────────────────────────────────────╯

🎤 Available Audio Input Devices:
  0: Infinite Microphone
  1: MacBook Air Microphone (default)

✅ Found API key in environment (.env file)
Using key: sk-proj...xyz9
✅ API key validated
```

**Without .env file:**
```
🔑 No API key found in .env file
Tip: Create a .env file with OPENAI_API_KEY=sk-your-key-here

🔑 Please enter your OpenAI API key:
```

After entering your API key:

```
📊 System Status
┏━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Component   ┃ Status                   ┃
┡━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Audio Input │ ✅ Ready                 │
│ OpenAI API  │ ✅ Connected             │
│ Subtitle    │ ✅ /path/to/subtitle.txt │
└─────────────┴──────────────────────────┘

🎯 Commands:
• start - Begin recording and translation
• stop - Stop recording and translation
• status - Show current status
• quit - Exit the application
• Ctrl+C - Emergency stop

Enter command [start]:
```

## 🔧 Dependencies

All managed through UV:

```toml
[project]
dependencies = [
    "openai>=1.98.0",         # Modern OpenAI client
    "pyaudio>=0.2.11",        # Audio recording
    "rich>=13.0.0",           # Beautiful CLI interface
    "python-dotenv>=1.0.0",   # Environment variable support
]
```

## 🔑 API Key Configuration

### Method 1: .env File (Recommended)
```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your key
echo "OPENAI_API_KEY=sk-your-actual-key-here" > .env
```

### Method 2: Environment Variable
```bash
# Set for current session
export OPENAI_API_KEY=sk-your-actual-key-here

# Or add to your shell profile (~/.zshrc, ~/.bashrc)
echo 'export OPENAI_API_KEY=sk-your-actual-key-here' >> ~/.zshrc
```

### Method 3: Interactive Input
If no API key is found in the environment, the app will prompt you to enter it manually (secure input, won't show in terminal history).

## 🎵 Audio Setup

The audio setup is the same as before - just ensure your microphone permissions are granted and PortAudio is installed:

```bash
# Install PortAudio (required for PyAudio)
brew install portaudio

# Grant microphone permissions when prompted
# System Preferences > Security & Privacy > Microphone
```

## 📺 OBS Integration

The subtitle file integration remains the same:

1. **Add Text Source** in OBS
2. **Read from file**: Select `subtitle.txt` 
3. **Configure appearance**: Font size, colors, position
4. **Start translation** and speak into your microphone

## 🛠️ Troubleshooting

### ❌ "PortAudio not found"
```bash
brew install portaudio
uv sync --force
```

### ❌ Microphone permission denied
Grant Terminal app microphone access in System Preferences.

### ❌ API key issues  
Ensure your OpenAI API key starts with `sk-` and has credits available.

## 🎉 Benefits of This Approach

1. **No Tkinter issues** - Works on any macOS system
2. **Clean UV workflow** - All dependencies managed properly  
3. **Better UX** - Rich CLI is more intuitive than basic GUI
4. **Terminal-friendly** - Works over SSH, in any terminal
5. **Modern Python practices** - Uses current OpenAI client API

**Tkinter** was Python's built-in GUI toolkit, but it often has compatibility issues on macOS with different Python installations. Rich provides a much better terminal-based interface that's more reliable and looks great!