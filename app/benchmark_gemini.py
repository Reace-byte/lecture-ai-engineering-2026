import argparse
import csv
import time
from pathlib import Path

from google import genai
from google.genai import errors, types

from app.config import get_api_key

QUESTIONS = {
    "basic": "LoRAとは何ですか？",
    "detailed": (
        "LoRAとQLoRAの違いを、仕組み・利点・"
        "欠点の観点から説明してください。"
    ),
    "course": (
        "AIE2026の講座の宿題にある"
        "「3レベル」とは何ですか？"
    ),
}

FIELDS = [
    "model", "question_id", "question", "trial","response_time_s", "input_tokens",
    "output_tokens", "thinking_tokens","total_tokens", "response_chars","status", "response_text",
]

def get_count(usage, field):
    if usage is None:
        return ""
    value = getattr(usage, field, None)
    return value if value is not None else ""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--models", nargs="+",
        default=["gemini-3.5-flash-lite","gemini-3.8-flash",],
    )
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--interval", type=float, default=15)
    parser.add_argument("--output",default="lectures/01/benchmark_results.csv",)
    args = parser.parse_args()

    if args.repeats < 1 or args.interval < 0:
        parser.error("repeatsは1以上、intervalは0以上")

    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)

    client = genai.Client(
    api_key=get_api_key(),http_options=types.HttpOptions(timeout=360000,  # 360秒（単位はミリ秒）),
))
    stop = False

    try:
        with path.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()

            for model in args.models:
                if stop:
                    break

                for question_id, question in QUESTIONS.items():
                    if stop:
                        break

                    for trial in range(1, args.repeats + 1):
                        row = {
                            "model": model,"question_id": question_id,"question": question,"trial": trial,
                            "response_time_s": "","input_tokens": "","output_tokens": "","thinking_tokens": "",
                            "total_tokens": "","response_chars": "","status": "","response_text": "",
                        }

                        start = time.perf_counter()

                        try:
                            response = client.models.generate_content(
                                model=model,contents=question,config=types.GenerateContentConfig(temperature=0,max_output_tokens=1024,),
                            )

                            elapsed = time.perf_counter() - start
                            usage = response.usage_metadata
                            answer = response.text or ""

                            row.update({
                                "response_time_s": round(elapsed, 3),
                                "input_tokens": get_count(
                                    usage, "prompt_token_count"
                                ),
                                "output_tokens": get_count(
                                    usage, "candidates_token_count"
                                ),
                                "thinking_tokens": get_count(
                                    usage, "thoughts_token_count"
                                ),
                                "total_tokens": get_count(
                                    usage, "total_token_count"
                                ),
                                "response_chars": len(answer),
                                "status": "ok",
                                "response_text": answer,
                            })

                        except errors.APIError as exc:
                            elapsed = time.perf_counter() - start
                            code = getattr(exc, "code", None)

                            row["response_time_s"] = round(elapsed, 3)
                            row["status"] = f"api_error_{code}"

                            if code == 429:
                                print("レート制限に到達しました。""実験を停止します。")
                                stop = True

                        except Exception as exc:
                            elapsed = time.perf_counter() - start
                            row["response_time_s"] = round(elapsed, 3)
                            row["status"] = (f"error_{type(exc).__name__}")

                        writer.writerow(row)
                        f.flush()

                        print(
                            f"{model} | {question_id} | "
                            f"{trial}回目 | "
                            f"{row['response_time_s']}秒 | "
                            f"入力:{row['input_tokens']} | "
                            f"出力:{row['output_tokens']} | "
                            f"{row['status']}"
                        )

                        if stop:
                            break

                        time.sleep(args.interval)

    except KeyboardInterrupt:
        print("ユーザー操作で計測を中断しました。")
    finally:
        client.close()

    print(f"結果保存先: {path}")

if __name__ == "__main__":
    main()
