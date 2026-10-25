"""Geminiと会話履歴を保持しながら連続して質問するスクリプト。

使い方:
    uv run python -m app.ask "LoRAとは何ですか？"
    uv run python -m app.ask  # 最初に講座に固有の質問をする

同じ起動中はそれまでの質問・回答を踏まえて応答する。
終了するには exit / quit を入力するか、Ctrl+C を押す。
※終了後に会話履歴は保存されない。
"""

import argparse

from google import genai
from google.genai import errors

from app.config import MODEL, api_error_message, get_api_key

# 講座に固有の質問。正しい答えは data/glossary.json の homework-levels にある
DEFAULT_QUESTION = "AIE2026の講座の宿題にある「3レベル」とは何ですか？"


def ask(question: str, chat) -> str:
    """同じチャットに質問を送り、履歴を踏まえた回答を返す。"""
    response = chat.send_message(question)
    return response.text or "（テキストの回答がありませんでした）"


def main() -> None:
    parser = argparse.ArgumentParser(description="Geminiと会話履歴を保って連続対話する")
    parser.add_argument("question", nargs="?", default=DEFAULT_QUESTION)
    args = parser.parse_args()

    client = genai.Client(api_key=get_api_key())
    chat = client.chats.create(model=MODEL)

    print(f"[model] {MODEL}")
    print("[会話モード] 終了するには exit または quit を入力してください。\n")

    question = args.question
    try:
        while True:
            if question.strip().lower() in {"exit", "quit"}:
                break
            if question.strip():
                print(f"[質問] {question}\n")
                try:
                    print(f"[回答] {ask(question, chat)}\n")
                except errors.APIError as e:
                    print(f"[APIエラー] {api_error_message(e.code, e.message)}\n")
            try:
                question = input("[次の質問] ").strip()
            except EOFError:
                break
    except KeyboardInterrupt:
        print()  # Ctrl+C で終了した際の表示を整える
    finally:
        client.close()
        print("会話を終了しました。")


if __name__ == "__main__":
    main()
