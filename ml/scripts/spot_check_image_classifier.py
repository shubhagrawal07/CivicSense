"""Manual dev tool for SL-22. Runs classify_image() over SL-21's sample images
and prints an accuracy number. Makes real paid API calls, never run in CI.
Needs a real ANTHROPIC_API_KEY and the backend dependencies installed.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SAMPLES_DIR = ROOT / "ml" / "datasets" / "images" / "test_samples"

# the backend app isn't an installed package, so point at it directly
sys.path.insert(0, str(ROOT / "backend"))

from app.intelligence.image_classifier import classify_image


def main():
    if not SAMPLES_DIR.exists():
        print(f"no sample images yet at {SAMPLES_DIR}, see SL-21")
        return

    total = 0
    correct = 0
    for category_dir in sorted(SAMPLES_DIR.iterdir()):
        if not category_dir.is_dir():
            continue
        expected = category_dir.name
        for image_path in sorted(category_dir.iterdir()):
            result = classify_image(image_path)
            match = result["category"] == expected
            total += 1
            correct += match
            status = "ok" if match else "miss"
            print(
                f"{expected:25} -> {result['category']:25} "
                f"({result['confidence']:.2f}) {status}"
            )

    if total:
        print(f"\naccuracy: {correct}/{total} ({correct / total:.0%})")


if __name__ == "__main__":
    main()
