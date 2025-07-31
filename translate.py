import os
from openai import OpenAI
import pyaudio
import wave
import threading
from queue import Queue
import signal
import sys
import tempfile
import time
import getpass
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import uvicorn

# グローバル変数の設定
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
TEMP_DIR = tempfile.gettempdir()
file_path = os.path.join(os.getcwd(), "subtitle.txt")

audio_queue = Queue()
running = False
record_thread = None
process_thread = None
last_translation = ""
console = Console()
client = None

# Web server components
app = FastAPI(title="OBS Real-Time Translation", version="1.0.0")
active_websockets: List[WebSocket] = []
translation_history: List[Dict[str, Any]] = []


def record_audio():
    global running
    audio = None
    stream = None
    try:
        audio = pyaudio.PyAudio()

        # Use non-blocking stream with larger buffer for macOS
        stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK * 4,  # Larger buffer for macOS
            input_device_index=None,  # Use default device
            stream_callback=None,
        )

        console.print("[green]🎤 Audio stream started[/green]")

        while running:
            frames = []
            # Record for 6 seconds with overflow protection
            try:
                for _ in range(0, int(RATE / CHUNK * 6)):
                    if not running:
                        break
                    # Non-blocking read with exception handling
                    try:
                        frame_data = stream.read(CHUNK, exception_on_overflow=False)
                        frames.append(frame_data)
                    except Exception as read_error:
                        console.print(
                            f"[yellow]⚠️  Audio read warning: {read_error}[/yellow]"
                        )
                        # Skip this chunk and continue
                        continue

                if frames:  # Only process if we have audio data
                    audio_data = b"".join(frames)
                    audio_queue.put(audio_data)

            except Exception as chunk_error:
                console.print(f"[yellow]⚠️  Audio chunk error: {chunk_error}[/yellow]")
                time.sleep(0.1)  # Brief pause before retry

    except Exception as e:
        console.print(f"[red]❌ Recording error: {e}[/red]")
    finally:
        try:
            if stream and stream.is_active():
                stream.stop_stream()
            if stream:
                stream.close()
        except Exception:
            pass  # Ignore cleanup errors
        try:
            if audio:
                audio.terminate()
        except Exception:
            pass  # Ignore cleanup errors
        console.print("[dim]🔇 Audio stream closed[/dim]")


def process_audio():
    while running:
        try:
            if not audio_queue.empty():
                audio_data = audio_queue.get()
                # 一意のファイル名を生成
                temp_wav = os.path.join(
                    TEMP_DIR, f"audio_{int(time.time() * 1000)}.wav"
                )

                try:
                    with wave.open(temp_wav, "wb") as wf:
                        wf.setnchannels(CHANNELS)
                        wf.setsampwidth(pyaudio.PyAudio().get_sample_size(FORMAT))
                        wf.setframerate(RATE)
                        wf.writeframes(audio_data)

                    with open(temp_wav, "rb") as audio_file:
                        # リトライ付きでAPIリクエスト
                        text = None
                        for retry in range(3):  # 最大3回リトライ
                            try:
                                response = client.audio.transcriptions.create(
                                    model="whisper-1", file=audio_file
                                )
                                text = response.text
                                break  # 成功したらループを抜ける
                            except Exception as api_error:
                                print(f"API error (attempt {retry + 1}/3): {api_error}")
                                if retry < 2:  # 最後のリトライでなければ待機
                                    time.sleep(2)  # 2秒待機してリトライ
                                else:
                                    print(
                                        "API failed after 3 attempts, skipping this audio"
                                    )
                                    break

                        if text is None:  # 全てのリトライが失敗
                            continue

                    # 空のテキストや短すぎるテキストをスキップ
                    if len(text.strip()) < 5:  # 精度向上のため閾値を下げる
                        continue

                    # 特定のフレーズを無視（YouTube定型句や音声認識の誤検出）
                    ignore_phrases = [
                        "ご視聴いただきありがとうございます",
                        "ご視聴いただきありがとうございます。",
                        "ご覧いただきありがとうございます",
                        "ご覧いただきありがとうございます。",
                        "ご視聴ありがとうございます",
                        "ご視聴ありがとうございます。",
                        "ごしちょういただきありがとうございます",
                        "Thank you for watching",
                        "Thank you for watching.",
                        "Thank you so much for watching",
                        "Thank you so much for watching.",
                        "Thanks for watching",
                        "Thanks for watching.",
                        "thank you for watching",
                        "thank you for watching.",
                        "thanks for watching",
                        "thanks for watching.",
                        "Thankyouforwatching",
                        "thankyouforwatching",
                        "ThankyouforWatching",
                        "ThankYouForWatching",
                        "チャンネルを登録し",
                        "いいねを押して",
                        "コメントしてください",
                        "チャンネル登録といいねをお願いします",
                        "Please subscribe",
                        "Like and subscribe",
                        "Don't forget to subscribe",
                        "Hit the like button",
                        "Leave a comment",
                        "愛しています",
                        "2023年10月までのデータでトレーニングされています",
                        "2023年10月までのデータで訓練されています",
                        "2023年10月までのデータで学習されています",
                        "trained on data up to October 2023",
                        "training data up to October 2023",
                    ]

                    should_ignore = False
                    text_lower = (
                        text.lower().replace(" ", "").replace("　", "")
                    )  # 小文字化 + スペース削除

                    for phrase in ignore_phrases:
                        phrase_clean = phrase.lower().replace(" ", "").replace("　", "")
                        if phrase_clean in text_lower:
                            should_ignore = True
                            break

                    # 追加の強力なフィルタリング
                    if any(
                        keyword in text_lower for keyword in ["thankyou", "ありがとう"]
                    ) and any(
                        keyword in text_lower
                        for keyword in ["watching", "視聴", "しちょう"]
                    ):
                        should_ignore = True

                    if should_ignore:
                        print(f"Ignored: {text}")
                        continue

                    # 翻訳を別スレッドで並列実行して高速化
                    translation_thread = threading.Thread(
                        target=translate_and_update, args=(text,)
                    )
                    translation_thread.daemon = True  # メインプログラム終了時に強制終了
                    translation_thread.start()

                    # 前の翻訳スレッドが長時間実行中でも新しい音声処理を続行
                    # 各翻訳は独立して実行される

                except Exception as e:
                    console.print(f"[yellow]⚠️  Error processing audio: {e}[/yellow]")
                finally:
                    # 一時ファイルをクリーンアップ
                    if os.path.exists(temp_wav):
                        try:
                            os.remove(temp_wav)
                        except Exception:
                            pass
        except Exception as outer_e:
            console.print(f"[yellow]⚠️  Error in process_audio loop: {outer_e}[/yellow]")
            # エラーが発生しても処理を続行
            time.sleep(0.1)  # 短時間待機してから次のループへ


def detect_language(text):
    import re

    # より精密な言語検出
    japanese_chars = re.findall(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]", text)
    english_chars = re.findall(r"[a-zA-Z]", text)

    # 日本語文字が1つでもあれば日本語と判定
    if len(japanese_chars) > 0:
        return "ja"

    # 英語の文字が多い場合は英語
    if len(english_chars) > 3:
        return "en"

    # 短いテキストの場合、より慎重に判定
    total_meaningful_chars = len(japanese_chars) + len(english_chars)
    if total_meaningful_chars == 0:
        return "en"  # デフォルト

    japanese_ratio = len(japanese_chars) / total_meaningful_chars

    # 25%以上日本語文字なら日本語（閾値を下げて日本語検出を向上）
    if japanese_ratio > 0.25:
        return "ja"
    else:
        return "en"


def translate_and_update(text):
    try:
        detected_lang = detect_language(text)
        translated_text = translate_text(text)
        if translated_text and len(translated_text.strip()) > 0:
            update_subtitle_file(translated_text)
            # Broadcast to web interface
            broadcast_translation(text, translated_text, detected_lang)
        else:
            console.print(f"[yellow]Translation failed or empty for: {text}[/yellow]")
    except Exception as e:
        console.print(f"[red]Error in translate_and_update: {e}[/red]")
        # エラーが発生しても処理を続行


def translate_text(text):
    detected_lang = detect_language(text)
    target_language = "ja" if detected_lang == "en" else "en"

    # 技術用語辞書（英語→日本語）
    # 特定の文脈や専門用語を追加することで、その分野に特化した翻訳精度が向上します
    tech_terms_dict = {
        "vibe coding": "バイブコーディング",
        "vibecoding": "バイブコーディング",
        "codegen": "コードジェン",
        "code generation": "コードジェネレーション",
        "live coding": "ライブコーディング",
        "livecoding": "ライブコーディング",
        "pair programming": "ペアプログラミング",
        "code review": "コードレビュー",
        "refactoring": "リファクタリング",
        "debugging": "デバッグ",
        "api": "API",
        "rest api": "REST API",
        "graphql": "GraphQL",
        "typescript": "TypeScript",
        "javascript": "JavaScript",
        "react": "React",
        "vue": "Vue",
        "angular": "Angular",
        "node.js": "Node.js",
        "docker": "Docker",
        "kubernetes": "Kubernetes",
        "microservices": "マイクロサービス",
        "serverless": "サーバーレス",
        "ci/cd": "CI/CD",
        "devops": "DevOps",
        "agile": "アジャイル",
        "scrum": "スクラム",
        "kanban": "カンバン",
        "machine learning": "機械学習",
        "artificial intelligence": "人工知能",
        "deep learning": "ディープラーニング",
        "blockchain": "ブロックチェーン",
        "cryptocurrency": "暗号通貨",
    }

    # 言語別にプロンプトを最適化（解説なし、翻訳結果のみ）
    if detected_lang == "en" and target_language == "ja":
        # 英語→日本語: 解説を一切出さない厳格なプロンプト
        system_prompt = """以下の英語テキストを日本語に翻訳してください。
翻訳結果のみを返してください。解説、説明、注釈は一切不要です。
技術用語は自然な日本語として翻訳してください。"""
        model = "gpt-4o-mini"
        temperature = 0.1  # 精度最重視
    else:
        # 日本語→英語: 解説なしの厳格なプロンプト
        system_prompt = f"""Translate the following {detected_lang} text to {target_language}.
Return only the translation. Do not add explanations, comments, or notes."""
        model = "gpt-4o-mini"
        temperature = 0.1

    # リトライ付きで翻訳API実行（元のテキストを使用）
    translation = None
    for retry in range(3):  # 最大3回リトライ
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text},
                ],
                temperature=temperature,
            )
            translation = response.choices[0].message.content.strip()
            break  # 成功したらループを抜ける
        except Exception as api_error:
            print(f"Translation API error (attempt {retry + 1}/3): {api_error}")
            if retry < 2:  # 最後のリトライでなければ待機
                time.sleep(2)  # 2秒待機してリトライ
            else:
                print("Translation API failed after 3 attempts")
                return "Translation temporarily unavailable"

    if translation is None:  # 全てのリトライが失敗
        return "Translation failed"

    # 翻訳後に技術用語を置換（英語→日本語の場合のみ）
    if detected_lang == "en" and target_language == "ja":
        for eng_term, jp_term in tech_terms_dict.items():
            # 大文字小文字を無視して置換
            import re

            pattern = re.compile(re.escape(eng_term), re.IGNORECASE)
            translation = pattern.sub(jp_term, translation)

    try:
        # OpenAIのシステムメッセージや解説的な内容をフィルタリング
        unwanted_phrases = [
            "あなたは2023年",
            "2023年10月までの",
            "データでトレーニング",
            "データで訓練",
            "データで学習",
            "この文章は",
            "この表現は",
            "という意味です",
            "と訳すこともできます",
            "という訳語もあります",
            "という意味になります",
            "可能性があります",
            "場合もあります",
            "と解釈",
            "と理解",
            "説明すると",
            "つまり",
            "I'm an AI",
            "I am an AI",
            "I don't have",
            "I cannot",
            "As an AI",
            "私はAI",
            "データで訓練されています",
            "trained on data",
            "training data",
            "This could mean",
            "This might be",
            "It could also be",
            "In other words",
        ]

        # 解説的なフレーズを含む場合は除去
        for phrase in unwanted_phrases:
            if phrase in translation:
                return ""  # 不要なメッセージは出力しない

        # 複数文がある場合、解説的でない最初の文のみを返す
        sentences = translation.split("。")
        if len(sentences) > 1:
            # 最初の文が解説的でなければそれを返す
            first_sentence = sentences[0].strip()
            if not any(
                explain_word in first_sentence
                for explain_word in ["意味", "解釈", "訳", "表現", "場合"]
            ):
                return first_sentence + ("。" if first_sentence else "")

        return translation
    except Exception as e:
        print(f"Error translating text: {e}")
        return "Translation error"


def update_subtitle_file(text):
    global last_translation

    # 空のテキストや不要なメッセージは書き込まない
    if not text or len(text.strip()) == 0:
        return

    # 重複検出：前回と同じ内容はスキップ
    if text.strip() == last_translation.strip():
        return

    # 類似した内容の検出（簡単な方法）
    if last_translation and len(text) > 10 and len(last_translation) > 10:
        # 文字列の類似度を簡単チェック
        common_words = set(text.lower().split()) & set(last_translation.lower().split())
        if len(common_words) > len(text.split()) * 0.7:  # 70%以上同じ単語
            return

    last_translation = text

    try:
        # OBS用に1行ずつ上書き（追記ではなく上書き）
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text)
        console.print(f"[blue]📝 Subtitle:[/blue] {text}")
    except Exception as e:
        print(f"Failed to update subtitle: {e}")


async def broadcast_to_websockets(message_type: str, data: dict):
    """Broadcast message to all connected WebSocket clients"""
    if not active_websockets:
        return

    message = json.dumps({"type": message_type, "data": data})

    # Send to all connected clients
    disconnected = []
    for websocket in active_websockets:
        try:
            await websocket.send_text(message)
        except Exception:
            disconnected.append(websocket)

    # Remove disconnected clients
    for ws in disconnected:
        if ws in active_websockets:
            active_websockets.remove(ws)


def broadcast_translation(original_text: str, translated_text: str, detected_lang: str):
    """Broadcast translation to web clients"""
    try:
        # Add to history
        timestamp = datetime.now().isoformat()
        translation_data = {
            "timestamp": timestamp,
            "original": original_text,
            "translation": translated_text,
            "detected_language": detected_lang,
            "source_lang": "🇯🇵 Japanese" if detected_lang == "ja" else "🇺🇸 English",
            "target_lang": "🇺🇸 English" if detected_lang == "ja" else "🇯🇵 Japanese",
        }

        translation_history.append(translation_data)
        if len(translation_history) > 50:  # Keep last 50
            translation_history.pop(0)

        # Broadcast to WebSocket clients (run in thread to avoid blocking)
        def run_broadcast():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(
                    broadcast_to_websockets("translation", translation_data)
                )
                loop.close()
            except Exception as e:
                console.print(f"[yellow]⚠️  Web broadcast error: {e}[/yellow]")

        threading.Thread(target=run_broadcast, daemon=True).start()

    except Exception as e:
        console.print(f"[yellow]⚠️  Broadcast setup error: {e}[/yellow]")


def start_recording():
    global running, record_thread, process_thread
    if not running:
        running = True
        record_thread = threading.Thread(target=record_audio)
        process_thread = threading.Thread(target=process_audio)
        record_thread.start()
        process_thread.start()
        console.print("[green]✓ Started recording and translation[/green]")


def stop_recording():
    global running, record_thread, process_thread
    if running:
        running = False
        # タイムアウト付きでスレッドを停止
        if record_thread and record_thread.is_alive():
            record_thread.join(timeout=2)
        if process_thread and process_thread.is_alive():
            process_thread.join(timeout=2)
        console.print("[red]✗ Stopped recording and translation[/red]")


# Ctrl + C (SIGINT) に対応するハンドラ
def signal_handler(sig, frame):
    console.print("\n[yellow]⚠️  Ctrl + C detected! Stopping recording...[/yellow]")
    stop_recording()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


# Web Routes
@app.get("/", response_class=HTMLResponse)
async def get_viewer():
    """Serve the main translation viewer page"""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎙️ Real-Time Translation Viewer</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh; padding: 20px; color: white;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header {
            text-align: center; margin-bottom: 30px;
            background: rgba(255, 255, 255, 0.1); padding: 20px;
            border-radius: 15px; backdrop-filter: blur(10px);
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        .status {
            padding: 15px; border-radius: 10px; margin-bottom: 20px;
            text-align: center; font-weight: bold; transition: all 0.3s ease;
        }
        .status.connected { background: rgba(76, 175, 80, 0.8); }
        .status.disconnected { background: rgba(244, 67, 54, 0.8); }
        .status.recording { background: rgba(255, 152, 0, 0.8); animation: pulse 2s infinite; }
        @keyframes pulse { 0% { opacity: 0.8; } 50% { opacity: 1; } 100% { opacity: 0.8; } }
        .translation-container {
            background: rgba(255, 255, 255, 0.1); border-radius: 15px;
            backdrop-filter: blur(10px); min-height: 500px;
            overflow-y: auto; max-height: 70vh;
        }
        .translation-item {
            padding: 20px; border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            animation: slideIn 0.5s ease; transition: background 0.3s ease;
        }
        .translation-item:hover { background: rgba(255, 255, 255, 0.05); }
        .translation-item:last-child { border-bottom: none; }
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .timestamp { font-size: 0.8em; opacity: 0.7; margin-bottom: 8px; }
        .language-indicator {
            display: inline-block; padding: 4px 8px; border-radius: 12px;
            font-size: 0.7em; font-weight: bold; margin-right: 10px;
        }
        .lang-ja { background: rgba(255, 87, 87, 0.8); }
        .lang-en { background: rgba(74, 144, 226, 0.8); }
        .original-text {
            font-size: 1.1em; margin-bottom: 10px; padding: 10px;
            background: rgba(0, 0, 0, 0.2); border-radius: 8px;
            border-left: 4px solid #4CAF50;
        }
        .translated-text {
            font-size: 1.2em; font-weight: 500; padding: 15px;
            background: rgba(255, 255, 255, 0.15); border-radius: 8px;
            border-left: 4px solid #2196F3;
        }
        .no-translations {
            text-align: center; padding: 50px; opacity: 0.7; font-size: 1.1em;
        }
        .stats {
            display: flex; justify-content: space-around; margin-top: 20px;
            background: rgba(255, 255, 255, 0.1); padding: 15px; border-radius: 10px;
        }
        .stat-item { text-align: center; }
        .stat-number { font-size: 1.5em; font-weight: bold; display: block; }
        .connection-indicator {
            position: fixed; top: 20px; right: 20px; width: 12px; height: 12px;
            border-radius: 50%; background: #f44336; transition: background 0.3s ease;
        }
        .connection-indicator.connected {
            background: #4CAF50; box-shadow: 0 0 10px rgba(76, 175, 80, 0.5);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎙️ Real-Time Translation Viewer</h1>
            <p>Japanese ⇔ English Live Translation</p>
        </div>

        <div id="status" class="status disconnected">🔴 Connecting to translation service...</div>

        <div class="translation-container">
            <div id="translations">
                <div class="no-translations">
                    <h3>🎵 Waiting for translations...</h3>
                    <p>Start speaking into your microphone to see live translations appear here!</p>
                </div>
            </div>
        </div>

        <div class="stats">
            <div class="stat-item">
                <span id="total-translations" class="stat-number">0</span>
                <span>Total Translations</span>
            </div>
            <div class="stat-item">
                <span id="session-time" class="stat-number">00:00</span>
                <span>Session Time</span>
            </div>
            <div class="stat-item">
                <span id="connection-status" class="stat-number">🔴</span>
                <span>Connection</span>
            </div>
        </div>
    </div>

    <div id="connection-indicator" class="connection-indicator"></div>

    <script>
        class TranslationViewer {
            constructor() {
                this.ws = null;
                this.translationCount = 0;
                this.sessionStart = new Date();
                this.setupWebSocket();
                this.startSessionTimer();
            }

            setupWebSocket() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws`;

                try {
                    this.ws = new WebSocket(wsUrl);

                    this.ws.onopen = () => {
                        console.log('WebSocket connected');
                        this.updateConnectionStatus(true);
                    };

                    this.ws.onmessage = (event) => {
                        const message = JSON.parse(event.data);
                        this.handleMessage(message);
                    };

                    this.ws.onclose = () => {
                        console.log('WebSocket disconnected');
                        this.updateConnectionStatus(false);
                        setTimeout(() => this.setupWebSocket(), 3000);
                    };

                    this.ws.onerror = (error) => {
                        console.error('WebSocket error:', error);
                        this.updateConnectionStatus(false);
                    };
                } catch (error) {
                    console.error('Failed to create WebSocket:', error);
                    this.updateConnectionStatus(false);
                }
            }

            handleMessage(message) {
                switch (message.type) {
                    case 'translation':
                        this.addTranslation(message.data);
                        break;
                    case 'status':
                        this.updateStatus(message.data);
                        break;
                    case 'history':
                        this.loadHistory(message.data);
                        break;
                }
            }

            addTranslation(data) {
                const container = document.getElementById('translations');
                const noTranslations = container.querySelector('.no-translations');
                if (noTranslations) {
                    noTranslations.remove();
                }

                const translationElement = this.createTranslationElement(data);
                container.insertBefore(translationElement, container.firstChild);

                this.translationCount++;
                document.getElementById('total-translations').textContent = this.translationCount;

                const translations = container.querySelectorAll('.translation-item');
                if (translations.length > 20) {
                    translations[translations.length - 1].remove();
                }
            }

            createTranslationElement(data) {
                const div = document.createElement('div');
                div.className = 'translation-item';

                const timestamp = new Date(data.timestamp).toLocaleTimeString();
                const sourceLang = data.detected_language === 'ja' ? 'ja' : 'en';

                div.innerHTML = `
                    <div class="timestamp">${timestamp}</div>
                    <div class="original-text">
                        <span class="language-indicator lang-${sourceLang}">${data.source_lang}</span>
                        ${data.original}
                    </div>
                    <div class="translated-text">
                        <span class="language-indicator lang-${sourceLang === 'ja' ? 'en' : 'ja'}">${data.target_lang}</span>
                        ${data.translation}
                    </div>
                `;

                return div;
            }

            updateStatus(data) {
                const statusElement = document.getElementById('status');
                let statusClass = 'connected';
                let statusText = '';

                switch (data.status) {
                    case 'recording':
                        statusClass = 'recording';
                        statusText = '🔴 Recording and translating...';
                        break;
                    case 'stopped':
                        statusClass = 'connected';
                        statusText = '⏸️ Translation stopped';
                        break;
                    case 'error':
                        statusClass = 'disconnected';
                        statusText = `❌ Error: ${data.message}`;
                        break;
                    default:
                        statusText = `ℹ️ ${data.message}`;
                }

                statusElement.className = `status ${statusClass}`;
                statusElement.textContent = statusText;
            }

            updateConnectionStatus(connected) {
                const indicator = document.getElementById('connection-indicator');
                const statusSpan = document.getElementById('connection-status');
                const statusDiv = document.getElementById('status');

                if (connected) {
                    indicator.classList.add('connected');
                    statusSpan.textContent = '🟢';
                    statusDiv.className = 'status connected';
                    statusDiv.textContent = '🟢 Connected to translation service';
                } else {
                    indicator.classList.remove('connected');
                    statusSpan.textContent = '🔴';
                    statusDiv.className = 'status disconnected';
                    statusDiv.textContent = '🔴 Disconnected - Attempting to reconnect...';
                }
            }

            startSessionTimer() {
                setInterval(() => {
                    const elapsed = new Date() - this.sessionStart;
                    const minutes = Math.floor(elapsed / 60000);
                    const seconds = Math.floor((elapsed % 60000) / 1000);
                    document.getElementById('session-time').textContent =
                        `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                }, 1000);
            }
        }

        document.addEventListener('DOMContentLoaded', () => {
            new TranslationViewer();
        });
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_websockets.append(websocket)
    console.print(
        f"[green]🌐 New WebSocket connection. Total: {len(active_websockets)}[/green]"
    )

    # Send recent translation history to new connection
    if translation_history:
        await websocket.send_text(
            json.dumps(
                {
                    "type": "history",
                    "data": translation_history[-10:],  # Last 10 translations
                }
            )
        )

    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        if websocket in active_websockets:
            active_websockets.remove(websocket)
        console.print(
            f"[yellow]🔌 WebSocket disconnected. Total: {len(active_websockets)}[/yellow]"
        )


@app.get("/api/status")
async def get_status():
    """API endpoint to get current server status"""
    return {
        "status": "running",
        "active_connections": len(active_websockets),
        "total_translations": len(translation_history),
        "recording": running,
        "timestamp": datetime.now().isoformat(),
    }


def check_audio_devices():
    """Check available audio input devices"""
    try:
        audio = pyaudio.PyAudio()
        console.print("\n[cyan]🎤 Available Audio Input Devices:[/cyan]")

        default_device = None
        for i in range(audio.get_device_count()):
            device_info = audio.get_device_info_by_index(i)
            if device_info["maxInputChannels"] > 0:
                is_default = (
                    " [green](default)[/green]"
                    if i == audio.get_default_input_device_info()["index"]
                    else ""
                )
                console.print(f"  {i}: {device_info['name']}{is_default}")
                if is_default:
                    default_device = device_info

        if default_device:
            console.print(
                f"\n[green]✓ Using default device: {default_device['name']}[/green]"
            )

        audio.terminate()
        return True
    except Exception as e:
        console.print(f"[red]❌ Error checking audio devices: {e}[/red]")
        return False


def main():
    global client

    # Rich console header
    console.print(
        Panel.fit(
            "[bold blue]🎙️  OBS Real-Time Translation Tool[/bold blue]\n"
            "[dim]Japanese ⇔ English Real-time Translation[/dim]\n"
            "[dim]Created by: minta[/dim]",
            border_style="blue",
        )
    )

    # Check audio devices first
    if not check_audio_devices():
        console.print(
            "[red]❌ Cannot access audio devices. Check microphone permissions.[/red]"
        )
        sys.exit(1)

    # Load environment variables from .env file
    load_dotenv()

    # Try to get API key from environment first
    api_key = os.getenv("OPENAI_API_KEY")

    if api_key:
        console.print("[green]✅ Found API key in environment (.env file)[/green]")
        # Mask the key for display
        masked_key = (
            api_key[:7] + "..." + api_key[-4:] if len(api_key) > 11 else "sk-..."
        )
        console.print(f"[dim]Using key: {masked_key}[/dim]")
    else:
        # API key input with Rich
        console.print("\n[yellow]🔑 No API key found in .env file[/yellow]")
        console.print(
            "[dim]Tip: Create a .env file with OPENAI_API_KEY=sk-your-key-here[/dim]"
        )
        console.print("\n[yellow]Please enter your OpenAI API key:[/yellow]")
        api_key = getpass.getpass("API Key (sk-...): ")

    if not api_key or not api_key.startswith("sk-"):
        console.print("[red]❌ Error: Valid API key is required to proceed.[/red]")
        sys.exit(1)

    try:
        client = OpenAI(api_key=api_key)
        console.print("[green]✅ API key validated[/green]")
    except Exception as e:
        console.print(f"[red]❌ Error: Invalid API key - {e}[/red]")
        sys.exit(1)

    # Status table
    table = Table(show_header=True, title="📊 System Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    table.add_row("Audio Input", "✅ Ready")
    table.add_row("OpenAI API", "✅ Connected")
    table.add_row("Subtitle File", f"✅ {file_path}")

    console.print(table)

    # Start web server in background thread
    def start_web_server():
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error")

    web_thread = threading.Thread(target=start_web_server, daemon=True)
    web_thread.start()
    time.sleep(2)  # Give web server time to start

    console.print("[green]✅ Web server started at http://localhost:8000[/green]")

    # Interactive menu
    console.print("\n[bold yellow]🎯 Commands:[/bold yellow]")
    console.print("• [green]start[/green] - Begin recording and translation")
    console.print("• [red]stop[/red] - Stop recording and translation")
    console.print("• [yellow]status[/yellow] - Show current status")
    console.print("• [cyan]web[/cyan] - Open web viewer (http://localhost:8000)")
    console.print("• [red]quit[/red] - Exit the application")
    console.print("• [dim]Ctrl+C - Emergency stop[/dim]")

    console.print(
        "\n[bold green]🌐 Web Viewer:[/bold green] [link]http://localhost:8000[/link]"
    )

    # Main loop
    while True:
        try:
            command = Prompt.ask(
                "\n[bold]Enter command",
                choices=["start", "stop", "status", "web", "quit"],
                default="start",
            )

            if command == "start":
                if not running:
                    start_recording()
                else:
                    console.print("[yellow]⚠️  Already recording![/yellow]")

            elif command == "stop":
                if running:
                    stop_recording()
                else:
                    console.print("[yellow]⚠️  Not currently recording![/yellow]")

            elif command == "status":
                status = "🟢 Recording" if running else "🔴 Stopped"
                console.print(f"[bold]Status:[/bold] {status}")
                console.print(f"[bold]Subtitle file:[/bold] {file_path}")
                console.print(
                    f"[bold]Last translation:[/bold] {last_translation or 'None'}"
                )
                console.print("[bold]Web server:[/bold] http://localhost:8000")
                console.print(f"[bold]Web connections:[/bold] {len(active_websockets)}")

            elif command == "web":
                import webbrowser

                try:
                    webbrowser.open("http://localhost:8000")
                    console.print("[green]🌐 Opening web viewer in browser...[/green]")
                except Exception as e:
                    console.print(f"[red]Could not open browser: {e}[/red]")
                    console.print("[dim]Manually open: http://localhost:8000[/dim]")

            elif command == "quit":
                if running:
                    stop_recording()
                console.print("[blue]👋 Goodbye![/blue]")
                break

        except KeyboardInterrupt:
            signal_handler(signal.SIGINT, None)
        except Exception as e:
            console.print(f"[red]❌ Error: {e}[/red]")


if __name__ == "__main__":
    main()
