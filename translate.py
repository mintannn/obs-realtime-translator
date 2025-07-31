import os
import tkinter as tk
from tkinter import simpledialog, messagebox
import openai
import pyaudio
import wave
import threading
from queue import Queue
import signal
import sys
import tempfile
import time

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


def record_audio():
    global running
    audio = None
    stream = None
    try:
        audio = pyaudio.PyAudio()
        stream = audio.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK,
        )

        overlap_frames = []

        while running:
            frames = []
            # 6秒間録音（英語のより長い文章に対応）
            for _ in range(0, int(RATE / CHUNK * 6)):
                if not running:
                    break
                frame_data = stream.read(CHUNK)
                frames.append(frame_data)

            # シンプルに録音データを使用
            combined_frames = frames
            audio_data = b"".join(combined_frames)
            audio_queue.put(audio_data)

    except Exception as e:
        print(f"Recording error: {e}")
    finally:
        if stream:
            stream.stop_stream()
            stream.close()
        if audio:
            audio.terminate()


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
                                response = openai.Audio.transcribe(
                                    model="whisper-1", file=audio_file
                                )
                                text = response["text"]
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
                    print(f"Error processing audio: {e}")
                finally:
                    # 一時ファイルをクリーンアップ
                    if os.path.exists(temp_wav):
                        try:
                            os.remove(temp_wav)
                        except:
                            pass
        except Exception as outer_e:
            print(f"Error in process_audio loop: {outer_e}")
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
        translated_text = translate_text(text)
        if translated_text and len(translated_text.strip()) > 0:
            update_subtitle_file(translated_text)
        else:
            print(f"Translation failed or empty for: {text}")
    except Exception as e:
        print(f"Error in translate_and_update: {e}")
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
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text},
                ],
                temperature=temperature,
            )
            translation = response["choices"][0]["message"]["content"].strip()
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
        print(f"Updated subtitle to: {text}")
    except Exception as e:
        print(f"Failed to update subtitle: {e}")


def start_recording():
    global running, record_thread, process_thread
    if not running:
        running = True
        record_thread = threading.Thread(target=record_audio)
        process_thread = threading.Thread(target=process_audio)
        record_thread.start()
        process_thread.start()
        print("Started recording")


def stop_recording():
    global running, record_thread, process_thread
    if running:
        running = False
        # タイムアウト付きでスレッドを停止
        if record_thread and record_thread.is_alive():
            record_thread.join(timeout=2)
        if process_thread and process_thread.is_alive():
            process_thread.join(timeout=2)
        print("Stopped recording")


# Ctrl + C (SIGINT) に対応するハンドラ
def signal_handler(sig, frame):
    print("Ctrl + C detected! Stopping recording...")
    stop_recording()
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)

# Tkinterの設定
root = tk.Tk()
root.title("リアルタイム翻訳システム")
root.geometry("400x200")

# APIキーの入力プロンプト
api_key = simpledialog.askstring(
    title="OpenAI API Key", prompt="Please enter your OpenAI API key:"
)

if not api_key:
    messagebox.showerror("Error", "API key is required to proceed.")
    root.destroy()
    exit()

openai.api_key = api_key

# GUIのボタン設定
start_button = tk.Button(root, text="開始", command=start_recording)
start_button.pack(pady=10)

stop_button = tk.Button(root, text="停止", command=stop_recording)
stop_button.pack(pady=10)

# 作成者のラベル
author_label = tk.Label(root, text="コード作成者：minta", font=("Arial", 8))
author_label.pack(side="bottom")

root.mainloop()
