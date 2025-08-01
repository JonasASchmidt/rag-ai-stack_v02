import argparse
import json
import os
from difflib import SequenceMatcher
from pathlib import Path

import requests


def query_pipeline(prompt: str, url: str) -> str:
    """Send *prompt* to the pipeline and return the answer."""
    response = requests.post(url, json={"prompt": prompt}, timeout=30)
    response.raise_for_status()
    data = response.json()
    return data.get("answer", "")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Evaluate pipeline responses")
    default_url = os.environ.get("PIPELINE_URL", "http://localhost:8000/query")
    parser.add_argument(
        "--tests",
        type=Path,
        default=Path(__file__).with_name("tests.json"),
        help="Path to tests.json file",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("results.json"),
        help="Path to write results.json",
    )
    parser.add_argument(
        "--url",
        default=default_url,
        help="Pipeline query URL (env: PIPELINE_URL)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    with args.tests.open("r", encoding="utf-8") as f:
        tests = json.load(f)

    results = []
    for case in tests:
        prompt = case["prompt"]
        expected = case["expected"]
        answer = query_pipeline(prompt, args.url)
        score = SequenceMatcher(None, expected, answer).ratio()
        results.append(
            {
                "prompt": prompt,
                "expected": expected,
                "answer": answer,
                "score": score,
            }
        )

    with args.output.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
