# 🎙️ Real-Time Translation Tool / リアルタイム翻訳ツール

English | [日本語](README.md)

A real-time Japanese-English bidirectional translation tool for OBS Studio.  
Automatically recognizes microphone audio and displays real-time translated subtitles in Japanese ⇔ English.

## 🙏 Credits

If possible, we'd appreciate the following credit when using this tool:  
**"Real-Time Translator by minta" or "リアルタイム翻訳ツール by minta"**

*Credit attribution is optional. We're just happy to see the tool being used by many people!

## 📋 Table of Contents
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [OBS Setup](#obs-setup)
- [Troubleshooting](#troubleshooting)
- [Technical Details](#technical-details)
- [Contributing](#contributing)
- [License](#license)

---

## 🔧 Requirements

### 1. Python
- **Python 3.8 or higher** required
- Download from [Python official website](https://www.python.org/downloads/)
- ⚠️ **Important**: Check "Add Python to PATH" during installation

### 2. Required Libraries
The tool will automatically install these libraries:
- **OpenAI (v1.3.0)**: AI library for speech recognition and translation
- **PyAudio**: Library for recording audio from microphone

### 3. OpenAI API Key
- Create account at [OpenAI Platform](https://platform.openai.com/api-keys)
- Obtain API key (paid service)
- 💰 **Pricing**: Pay-per-use (approximately a few cents for 5 minutes of usage)

⚠️ **Important API Key Security Notice**:
- Your API key is **as important as a password**
- Never share it with others
- Be careful not to accidentally upload it to GitHub
- Current version does not save the key (requires input each time)

### 4. Microphone
- PC-connected microphone (built-in mic is OK)
- **Recommended**: External USB or Bluetooth microphone (better quality and recognition accuracy)

### 5. OBS Studio (Streaming Software)
- Download from [OBS Studio official site](https://obsproject.com/)
- Free software

---

## 💾 Installation

### Step 1: Download Files
Download the following files to the same folder:
- `translate.py`
- `simple_installer.bat`
- `requirements.txt`

### Step 2: Microphone Setup
#### Basic Setup
1. **Settings** → **Privacy** → **Microphone**
2. Enable "Allow apps to access your microphone"

#### Select Microphone Device
1. **Settings** → **System** → **Sound**
2. **Input** → **Choose your input device**
3. Select desired microphone (✓ marked device will be used)

#### External Microphone Usage
- **USB Microphone**: Often becomes default automatically when connected
- **Bluetooth Microphone**: May need manual default setting after pairing  
- **3.5mm Microphone**: Often requires manual default setting
- ⚠️ **Important**: Restart translation tool after changing microphone

---

## 🚀 Usage

### Basic Usage

#### 1. Launch Tool
1. Double-click `simple_installer.bat`
2. **First time only**: Automatically installs required libraries (takes a few minutes)
   - Displays "Libraries not found. Installing..."
   - Please wait
3. **Subsequent launches**: Shows "Libraries already installed!" and starts immediately
4. Translation tool launches

#### 2. Enter API Key
1. "OpenAI API Key" input dialog appears
2. Enter your API key and click OK
   - Example: `sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

#### 3. Start Translation
1. Click **"開始" (Start)** button
2. Speak into the microphone
3. Recognizes and translates speech every 6 seconds
4. Creates `subtitle.txt` file in the same folder

#### 4. Stop Translation
1. Click **"停止" (Stop)** button
2. Ends translation

---

## 📺 OBS Setup

### Display Subtitles in OBS

#### 1. Add Text Source
1. Open OBS Studio
2. Click **"+"** in **"Sources"**
3. Select **"Text (GDI+)"**
4. Enter name (e.g., "Translation Subtitles") and click OK

#### 2. Configure File Reading
1. Check **"Read from file"**
2. Click **"Browse"** button
3. Select **"subtitle.txt"** in translation tool folder

#### 3. Adjust Display Settings
1. **Font**: Choose readable font (e.g., Arial, Segoe UI)
2. **Size**: 24-36 recommended
3. **Color**: White or yellow
4. **Background**: Transparent or semi-transparent black
5. **Position**: Bottom center of screen

#### 4. Test Operation
1. Click "Start" in translation tool
2. Speak into microphone
3. Confirm translation appears in OBS

---

## 🔧 Troubleshooting

### Common Issues and Solutions

#### ❌ "Python not found" Error
**Cause**: Python not installed or PATH not set  
**Solution**:
1. Reinstall Python
2. Ensure "Add Python to PATH" is checked during installation

#### ❌ "Library installation failed" Error
**Cause**: Automatic library installation failed  
**Solution**:
1. Right-click `simple_installer.bat`
2. Select "Run as administrator"
3. Try again

#### ❌ "PyAudio" Installation Error
**Cause**: PyAudio (audio recording library) installation failed  
**Solution**:
1. Open Command Prompt as administrator
2. Run the following in order:
   ```
   pip install pipwin
   pipwin install pyaudio
   pip install openai==1.3.0
   ```

#### ❌ Microphone Audio Not Recognized
**Cause**: Microphone settings, volume, or permission issues  
**Solution**:
1. **Check microphone connection**: Ensure proper connection
2. **Default microphone setting**: Settings → System → Sound → Input, select desired microphone
3. **Microphone volume**: Same screen → "Device properties" → Set volume to 80% or higher
4. **Microphone access permission**: Settings → Privacy → Microphone → Enable "Allow apps to access microphone"
5. **Restart translation tool**: Always restart tool after changing microphone
6. **Microphone test**: Check audio level with "Test your microphone" in settings

#### ❌ Translation Results Not Displayed
**Cause**: API key issues, network connection problems  
**Solution**:
1. Verify API key is correctly entered
2. Check internet connection
3. Confirm OpenAI account has payment method set up

#### ❌ Subtitles Not Showing in OBS
**Cause**: File path configuration error  
**Solution**:
1. Confirm `subtitle.txt` file is created
2. Verify correct file selected in OBS text source
3. Ensure "Read from file" is checked

## 🎯 Use Cases

### Streaming
1. Speak in English → Japanese subtitles displayed
2. Speak in Japanese → English subtitles displayed
3. Viewers can understand content in both languages

### Online Meetings
1. Real-time translation during meetings
2. Cross-language communication

### Domain-Specific Optimization
**Customize the technical term dictionary to improve translation accuracy for specific fields:**
- **Programming streams**: Accurate translation of development terms like "live coding"
- **Medical/Academic**: Register specialized terminology for precise interpretation
- **Game streaming**: Support for game-specific terms and slang
- **Business**: Proper translation of industry jargon and company terms

Simply edit the `tech_terms_dict` around line 223 in `translate.py` to customize for your needs.

---

## 🛠️ Technical Details

### Architecture
- **Speech Recognition**: OpenAI Whisper API
- **Translation**: OpenAI GPT-4o-mini
- **Audio Processing**: PyAudio for real-time microphone capture
- **GUI**: Tkinter for simple interface

### Key Features
1. **Bidirectional Translation**: Automatically detects language (Japanese/English) and translates to the other
2. **Real-time Processing**: 6-second audio chunks for optimal balance between speed and accuracy
3. **Noise Filtering**: Ignores common phrases like "Thank you for watching"
4. **Technical Term Dictionary**: Maintains consistency for technical terminology
5. **Duplicate Prevention**: Avoids repeating similar translations

### Language Detection Algorithm
- Uses character-based detection for accurate language identification
- Japanese characters (Hiragana, Katakana, Kanji) presence determines Japanese
- Falls back to English for Latin alphabet text

### Performance Optimizations
- Parallel processing for translation while continuing audio capture
- Retry mechanism for API failures (up to 3 attempts)
- Efficient temporary file management

---

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup
```bash
# Clone repository
git clone https://github.com/yourusername/obs-realtime-translator.git
cd obs-realtime-translator

# Install dependencies
pip install -r requirements.txt

# Run the tool
python translate.py
```

### Code Style
- Follow PEP 8 guidelines
- Add comments for complex logic
- Maintain existing code structure

---

## ⚠️ Important Notes

### Privacy
- Audio data is sent to OpenAI servers
- Avoid using for confidential or personal conversations

### System Requirements
- **OS**: Windows 10/11
- **CPU**: Standard PC (no special requirements)
- **Memory**: 4GB+ recommended
- **Network**: Stable internet connection

### API Usage and Costs
- OpenAI API is a paid service
- Pay-per-use pricing model
- Estimate: Few dollars per hour of usage
- See [OpenAI Pricing](https://openai.com/pricing) for details

---

## 📝 Project Information

**Creator**: minta with AI  
**Version**: 0.1.0  
**Supported Languages**: Japanese ⇔ English  
**License**: MIT License

### Open Source

This project is open source and available on [GitHub](https://github.com/mintannn/obs-realtime-translator).

### Contributing

Pull requests and suggestions for improvements are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### License & Copyright Status
✅ **This project is safe to publish as open source**

**Library License Status:**
- **openai (v1.3.0)**: MIT License - Free to use
- **pyaudio (v0.2.11)**: MIT License - Free to use
- **tkinter**: Python standard library - Free to use
- Other standard libraries: Included with Python - Free to use

**Copyright Status:**
- ✅ Code is completely original
- ✅ No copies from other projects
- ✅ No license violations
- ✅ Commercial use is allowed

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 💬 Feedback

We'd love to hear your thoughts and experiences using this tool!

- **X (Twitter)**: Follow [@mintabbl](https://twitter.com/mintabbl) and share your feedback 🌟
- **GitHub Issues**: Report bugs or request features [here](https://github.com/mintannn/obs-realtime-translator/issues)
- **GitHub Discussions**: Ask questions or discuss [here](https://github.com/mintannn/obs-realtime-translator/discussions)

Whether it's usage examples from your streams or improvement ideas, any feedback is greatly appreciated!

---

**🎉 Setup complete! Enjoy your real-time translation experience!**