# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2024-12-XX

### 🎉 初回リリース / Initial Release

リアルタイム翻訳ツールの最初の公開バージョンです。
This is the first public version of Real-Time Translation Tool.

### ✨ Features
- Real-time speech recognition using OpenAI Whisper API
- Bidirectional translation (Japanese ⇔ English)
- Automatic language detection
- OBS Studio integration via text file output
- Simple GUI with start/stop controls
- Noise filtering for common phrases
- Technical term dictionary for accurate translations

### ⚠️ 重要な注意事項 / Important Notes

1. **ベータ版です** - まだ開発中のため、バグがある可能性があります
   **Beta Version** - Still under development, may contain bugs

2. **OpenAI APIが必要** - 使用には有料のAPIキーが必要です
   **OpenAI API Required** - Paid API key required for use

3. **Windows専用** - 現在Windows 10/11でのみテスト済み
   **Windows Only** - Currently tested only on Windows 10/11

### 🚧 Known Limitations
- **Languages**: Currently supports only Japanese and English
- **API Key Management**: API key must be entered manually each time (no persistent storage)
- **Audio Input**: Uses system default microphone only (no device selection)
- **Performance**: 6-second audio chunks may cause slight delay
- **Cost**: Requires OpenAI API subscription (pay-per-use)
- **Platform**: Tested only on Windows 10/11
- **Error Messages**: Limited error feedback in GUI

### 🔧 Technical Notes
- Uses OpenAI API v0.28.1 (newer versions not supported due to API changes)
- Requires Python 3.8+ and PyAudio installation
- Temporary audio files are created in system temp directory

### 🚀 使い方 / Getting Started

1. [README.md](README.md) (日本語) または [README_EN.md](README_EN.md) (English) を参照
2. `simple_installer.bat` を実行してセットアップ
3. OpenAI APIキーを準備
4. OBS Studioで字幕表示設定

### 📝 今後の予定 / Future Plans
- 多言語対応（中国語、韓国語、スペイン語など）
- APIキーの保存機能
- マイクデバイス選択機能
- 録音間隔の調整機能
- プライバシー保護のためのローカル処理オプション
- エラーハンドリングとユーザーフィードバックの改善

### 🙏 フィードバック / Feedback

使用感想や不具合報告は以下へ：
Please share your feedback:

- X (Twitter): [@mintabbl](https://twitter.com/mintabbl)
- [GitHub Issues](https://github.com/mintannn/obs-realtime-translator/issues)
- [GitHub Discussions](https://github.com/mintannn/obs-realtime-translator/discussions)

### 🙏 Credits
Created by minta with AI

---

**注意**: これは初期バージョンです。本番環境での使用は自己責任でお願いします。
**Note**: This is an early version. Use in production at your own risk.

[0.1.0]: https://github.com/mintannn/obs-realtime-translator/releases/tag/v0.1.0